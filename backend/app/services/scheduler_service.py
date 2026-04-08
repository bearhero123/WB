"""APScheduler job management for daily check-in tasks."""

import asyncio
import logging
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.database import async_session
from app.models.account import Account
from app.services import checkin_service

logger = logging.getLogger(__name__)

SCHEDULER_TZ = "Asia/Shanghai"
scheduler = AsyncIOScheduler(timezone=SCHEDULER_TZ)


def _parse_schedule_time(raw_time: str | None) -> tuple[int, int]:
    """Parse HH:mm value and fall back to 08:00."""
    try:
        if not raw_time:
            raise ValueError("empty schedule time")
        parts = raw_time.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("invalid schedule range")
        return hour, minute
    except Exception:
        return 8, 0


def _to_local(dt: datetime | None, tz: ZoneInfo) -> datetime | None:
    """Convert stored datetime (naive UTC in DB) to target timezone."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)


def _make_job_id(account_id: int) -> str:
    return f"checkin_{account_id}"


async def _run_checkin_job(account_id: int):
    """Scheduler callback that runs one account check-in."""
    async with async_session() as db:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()

        if not account:
            logger.warning("Scheduled job skipped: account_id=%s does not exist", account_id)
            return

        if not account.schedule_enabled:
            logger.info("Scheduled job skipped: account=%s is disabled", account.account_name)
            return

        delay = random.randint(0, account.schedule_random_delay)
        if delay > 0:
            logger.info("Scheduled job delay: account=%s, delay=%ss", account.account_name, delay)
            await asyncio.sleep(delay)

        logger.info("Scheduled job started: account=%s", account.account_name)
        try:
            await checkin_service.run_checkin(db, account)
        except Exception as exc:
            logger.error("Scheduled job failed: account=%s, err=%s", account.account_name, exc)


async def apply_account_schedule(account_id: int, account: Account = None):
    """Apply one account schedule (create/replace/remove)."""
    job_id = _make_job_id(account_id)
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)
        logger.info("Removed old schedule job: %s", job_id)

    if account is None:
        async with async_session() as db:
            result = await db.execute(select(Account).where(Account.id == account_id))
            account = result.scalar_one_or_none()

    if not account or not account.schedule_enabled:
        logger.info("Account schedule disabled, skipped: account_id=%s", account_id)
        return

    hour, minute = _parse_schedule_time(account.schedule_time)
    trigger = CronTrigger(hour=hour, minute=minute, timezone=SCHEDULER_TZ)
    scheduler.add_job(
        _run_checkin_job,
        trigger=trigger,
        id=job_id,
        args=[account_id],
        replace_existing=True,
        name=f"checkin-{account.account_name}",
    )
    logger.info("Applied schedule: account=%s, time=%02d:%02d", account.account_name, hour, minute)


async def apply_all_schedules() -> int:
    """Rebuild all enabled account schedules."""
    for job in scheduler.get_jobs():
        if job.id.startswith("checkin_"):
            scheduler.remove_job(job.id)

    async with async_session() as db:
        result = await db.execute(select(Account).where(Account.schedule_enabled == True))
        accounts = result.scalars().all()

        count = 0
        for account in accounts:
            await apply_account_schedule(account.id, account)
            count += 1

    logger.info("Applied %s schedule jobs", count)
    return count


async def run_startup_catchup() -> int:
    """Run one catch-up check-in on startup if today's schedule time is already missed."""
    tz = ZoneInfo(SCHEDULER_TZ)
    now_local = datetime.now(tz)
    count = 0

    async with async_session() as db:
        result = await db.execute(select(Account).where(Account.schedule_enabled == True))
        accounts = result.scalars().all()

        for account in accounts:
            hour, minute = _parse_schedule_time(account.schedule_time)
            scheduled_today = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # Cron jobs do not backfill by default. If startup is after today's schedule,
            # trigger one catch-up execution unless the account has already run today.
            if now_local <= scheduled_today:
                continue

            last_checkin_local = _to_local(account.last_checkin_at, tz)
            if last_checkin_local and last_checkin_local.date() == now_local.date():
                continue

            logger.info(
                "Startup catch-up triggered: account=%s, schedule=%02d:%02d, now=%s",
                account.account_name,
                hour,
                minute,
                now_local.isoformat(timespec="seconds"),
            )
            try:
                await checkin_service.run_checkin(db, account)
                count += 1
            except Exception as exc:
                logger.error("Startup catch-up failed: account=%s, err=%s", account.account_name, exc)

    if count:
        logger.info("Startup catch-up finished: %s account(s) executed", count)
    else:
        logger.info("Startup catch-up finished: no account required catch-up")
    return count


def get_scheduler_status() -> list[dict]:
    """Return all scheduler jobs and next run time."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            }
        )
    return jobs


def start_scheduler():
    """Start APScheduler once."""
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler():
    """Shutdown APScheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
