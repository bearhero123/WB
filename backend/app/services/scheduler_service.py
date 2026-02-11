"""APScheduler 定时调度管理"""

import logging
import random
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import async_session
from app.models.account import Account
from app.services import checkin_service
from sqlalchemy import select

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def _run_checkin_job(account_id: int):
    """调度器执行的签到任务"""
    async with async_session() as db:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()

        if not account:
            logger.warning(f"定时任务: 账号 ID {account_id} 不存在, 跳过")
            return

        if not account.schedule_enabled:
            logger.info(f"定时任务: 账号 {account.account_name} 已禁用, 跳过")
            return

        # 随机延迟
        delay = random.randint(0, account.schedule_random_delay)
        if delay > 0:
            logger.info(f"定时任务: {account.account_name} 随机延迟 {delay}s")
            import asyncio
            await asyncio.sleep(delay)

        logger.info(f"定时任务开始: {account.account_name}")
        try:
            await checkin_service.run_checkin(db, account)
        except Exception as e:
            logger.error(f"定时任务异常: {account.account_name}: {e}")


def _make_job_id(account_id: int) -> str:
    return f"checkin_{account_id}"


async def apply_account_schedule(account_id: int, account: Account = None):
    """应用/更新单个账号的定时任务"""
    job_id = _make_job_id(account_id)

    # 先移除旧任务
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)
        logger.info(f"移除旧定时任务: {job_id}")

    if account is None:
        async with async_session() as db:
            result = await db.execute(select(Account).where(Account.id == account_id))
            account = result.scalar_one_or_none()

    if not account or not account.schedule_enabled:
        logger.info(f"账号 {account_id} 未启用定时, 跳过")
        return

    # 解析时间
    try:
        parts = account.schedule_time.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
    except Exception:
        hour, minute = 8, 0

    trigger = CronTrigger(hour=hour, minute=minute, timezone="Asia/Shanghai")
    scheduler.add_job(
        _run_checkin_job,
        trigger=trigger,
        id=job_id,
        args=[account_id],
        replace_existing=True,
        name=f"签到-{account.account_name}",
    )
    logger.info(f"已应用定时任务: {account.account_name} -> {hour:02d}:{minute:02d}")


async def apply_all_schedules():
    """重新应用所有定时任务"""
    # 清除所有现有签到任务
    for job in scheduler.get_jobs():
        if job.id.startswith("checkin_"):
            scheduler.remove_job(job.id)

    async with async_session() as db:
        result = await db.execute(
            select(Account).where(Account.schedule_enabled == True)
        )
        accounts = result.scalars().all()

        count = 0
        for account in accounts:
            await apply_account_schedule(account.id, account)
            count += 1

    logger.info(f"已应用 {count} 个定时任务")
    return count


def get_scheduler_status() -> list[dict]:
    """获取所有定时任务状态"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
        })
    return jobs


def start_scheduler():
    """启动调度器"""
    if not scheduler.running:
        scheduler.start()
        logger.info("调度器已启动")


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("调度器已关闭")
