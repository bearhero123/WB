"""超话签到核心业务服务"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.task_log import TaskLog
from app.services.cookie_service import validate_cookie
from app.services.push_service import (
    push_event,
    build_checkin_message,
    build_cookie_invalid_message,
)
from app.services.weibo_client import get_provider

logger = logging.getLogger(__name__)


async def run_checkin(db: AsyncSession, account: Account) -> dict:
    """
    执行一个账号的超话签到任务

    返回签到统计结果（含每个超话明细）
    """
    account_name = account.account_name
    logger.info(f"开始签到: {account_name}")

    # 1. Cookie 有效性校验
    is_valid, user_info = await validate_cookie(
        account.cookie_sub or "",
        account.cookie_subp or "",
        account.cookie_twm or "",
    )

    if not is_valid:
        logger.warning(f"Cookie 无效: {account_name}")

        # 记录日志
        log = TaskLog(
            account_id=account.id,
            event_type="cookie_invalid",
            status="fail",
            message=f"Cookie 已失效: {account_name}",
        )
        db.add(log)

        # 更新账号状态
        account.last_checkin_at = datetime.now(timezone.utc).replace(tzinfo=None)
        account.last_checkin_status = "cookie_invalid"
        await db.commit()

        # 推送告警
        title, desp = build_cookie_invalid_message(account_name)
        await push_event(db, "cookie_invalid", title, desp, account)

        return {"total": 0, "success": 0, "already": 0, "failed": 0, "cookie_valid": False}

    # 2. 获取超话列表
    provider = get_provider(
        account.cookie_sub or "",
        account.cookie_subp or "",
        account.cookie_twm or "",
    )

    try:
        topics = await provider.get_topics()
    except Exception as e:
        logger.error(f"获取超话列表失败: {account_name}: {e}")
        topics = []

    if not topics:
        logger.info(f"无可签到超话: {account_name}")
        stats = {
            "total": 0, "success": 0, "already": 0, "failed": 0,
            "cookie_valid": True, "checkin_details": [],
        }

        log = TaskLog(
            account_id=account.id,
            event_type="checkin",
            status="success",
            message="无可签到超话 (未获取到关注的超话列表，请检查Cookie或API参数)",
            detail=stats,
        )
        db.add(log)
        account.last_checkin_at = datetime.now(timezone.utc).replace(tzinfo=None)
        account.last_checkin_status = "success"
        await db.commit()

        # 即使没有超话也推送通知，方便排查
        title, desp = build_checkin_message(account_name, "VALID", stats)
        await push_event(db, "checkin", title, desp, account, force=True)

        return stats

    # 3. 遍历签到
    stats = {
        "total": len(topics), "success": 0, "already": 0, "failed": 0,
        "failed_items": [], "checkin_details": [],
    }

    logger.info(f"获取到 {len(topics)} 个超话，开始逐一签到: {account_name}")
    for idx, topic in enumerate(topics, 1):
        result = None
        for attempt in range(account.retry_count):
            result = await provider.checkin(topic)
            if result.status != "failed":
                break
            if attempt < account.retry_count - 1:
                await asyncio.sleep(1)

        if result:
            stats[result.status] = stats.get(result.status, 0) + 1
            if result.status == "failed":
                stats["failed_items"].append(f"{topic.title}: {result.detail}")

            # 记录每个超话的详细结果
            stats["checkin_details"].append({
                "name": topic.title,
                "status": result.status,
                "detail": result.detail,
            })
            logger.info(f"  [{idx}/{len(topics)}] [{result.status}] {topic.title}: {result.detail}")

        # 请求间隔
        await asyncio.sleep(account.request_interval)

    # 4. 汇总
    if stats["failed"] == 0:
        status = "success"
    elif stats["success"] > 0:
        status = "partial"
    else:
        status = "fail"

    # 构建详细的日志消息
    detail_lines = []
    for item in stats["checkin_details"]:
        icon = {"success": "✅", "already": "☑️", "failed": "❌"}.get(item["status"], "?")
        detail_lines.append(f"{icon} {item['name']}: {item['detail']}")
    detail_text = "\n".join(detail_lines)

    log = TaskLog(
        account_id=account.id,
        event_type="checkin",
        status=status,
        message=f"总计{stats['total']}, 成功{stats['success']}, 已签{stats['already']}, 失败{stats['failed']}",
        detail=stats,
    )
    db.add(log)

    account.last_checkin_at = datetime.now(timezone.utc).replace(tzinfo=None)
    account.last_checkin_status = status
    await db.commit()

    # 5. 推送签到结果
    title, desp = build_checkin_message(account_name, "VALID", stats)
    await push_event(db, "checkin", title, desp, account)

    logger.info(f"签到完成: {account_name} - {log.message}\n{detail_text}")
    return stats
