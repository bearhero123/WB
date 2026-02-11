"""Server酱推送服务"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.account import Account
from app.models.task_log import TaskLog

logger = logging.getLogger(__name__)

SERVERCHAN_URL = "https://sctapi.ftqq.com/{sendkey}.send"

# 推送去重缓存: {f"{account_id}:{event_type}": timestamp}
_push_dedup_cache: dict[str, float] = {}
DEDUP_WINDOW = 600  # 10 分钟


def _get_sendkey(account: Optional[Account] = None) -> Optional[str]:
    """获取 SendKey, 按优先级: 账号级 → 系统默认 → None"""
    if account and account.sendkey:
        return account.sendkey
    if settings.DEFAULT_SENDKEY:
        return settings.DEFAULT_SENDKEY
    return None


def _should_dedup(account_id: int, event_type: str) -> bool:
    """检查是否应该去重"""
    cache_key = f"{account_id}:{event_type}"
    now = datetime.now(timezone.utc).timestamp()

    last_time = _push_dedup_cache.get(cache_key)
    if last_time and (now - last_time) < DEDUP_WINDOW:
        return True

    _push_dedup_cache[cache_key] = now
    return False


async def send_push(
    sendkey: str,
    title: str,
    desp: str,
    max_retries: int = 3,
) -> dict:
    """
    发送 Server酱推送

    返回:
        {"ok": True/False, "status_code": int, "message": str}
    """
    url = SERVERCHAN_URL.format(sendkey=sendkey)
    data = {"title": title, "desp": desp}

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

            body = resp.json() if resp.status_code == 200 else {}
            if resp.status_code == 200 and body.get("code") == 0:
                return {"ok": True, "status_code": 200, "message": "推送成功"}

            error_msg = body.get("message", f"HTTP {resp.status_code}")
            logger.warning(f"推送失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")

        except Exception as e:
            logger.warning(f"推送异常 (尝试 {attempt + 1}/{max_retries}): {e}")
            error_msg = str(e)

        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** (attempt + 1))  # 2s, 4s, 8s

    return {"ok": False, "status_code": 0, "message": f"推送失败: {error_msg}"}


async def push_event(
    db: AsyncSession,
    event_type: str,
    title: str,
    desp: str,
    account: Optional[Account] = None,
    force: bool = False,
) -> dict:
    """
    统一推送入口

    参数:
        event_type: cookie_update / cookie_invalid / checkin / push_test
        title: 推送标题
        desp: Markdown 正文
        account: 关联账号 (可选)
        force: 是否跳过去重
    """
    account_id = account.id if account else 0

    # 去重检查
    if not force and _should_dedup(account_id, event_type):
        logger.info(f"推送已去重: account={account_id}, event={event_type}")
        return {"ok": True, "message": "推送已去重（10分钟内重复事件）"}

    sendkey = _get_sendkey(account)
    if not sendkey:
        logger.info(f"无可用 SendKey, 仅记录日志: {title}")
        # 记录到数据库日志
        log = TaskLog(
            account_id=account_id if account_id else None,
            event_type=f"push_{event_type}",
            status="skip",
            message=f"无可用 SendKey: {title}",
            detail={"title": title},
        )
        db.add(log)
        await db.commit()
        return {"ok": True, "message": "无可用 SendKey，仅记录日志"}

    result = await send_push(sendkey, title, desp)

    # 记录推送日志
    log = TaskLog(
        account_id=account_id if account_id else None,
        event_type=f"push_{event_type}",
        status="success" if result["ok"] else "fail",
        message=result["message"],
        detail={"title": title, "status_code": result.get("status_code")},
    )
    db.add(log)
    await db.commit()

    return result


# ─── 推送消息模板 ───

def build_checkin_message(account_name: str, cookie_status: str, stats: dict) -> tuple[str, str]:
    """构建签到结果推送消息"""
    title = f"签到结果 - {account_name}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S +08:00")

    total = stats.get("total", 0)
    success = stats.get("success", 0)
    already = stats.get("already", 0)
    failed = stats.get("failed", 0)

    if failed == 0:
        conclusion = "本次任务执行成功。"
    elif success > 0:
        conclusion = "本次任务部分成功，存在失败项。"
    else:
        conclusion = "本次任务执行失败。"

    desp = f"""### 签到任务结果

- 账号: `{account_name}`
- 时间: `{now}`
- Cookie状态: `{cookie_status}`
- 总超话: `{total}`
- 新签到: `{success}`
- 已签到: `{already}`
- 失败: `{failed}`

结论: {conclusion}"""

    if stats.get("failed_items"):
        desp += "\n\n**失败详情:**\n"
        for item in stats["failed_items"][:10]:
            desp += f"- {item}\n"

    return title, desp


def build_cookie_update_message(account_name: str, success: bool, detail: str = "") -> tuple[str, str]:
    """构建 Cookie 更新推送消息"""
    status = "成功" if success else "失败"
    title = f"Cookie更新{status} - {account_name}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S +08:00")

    desp = f"""### Cookie 更新通知

- 账号: `{account_name}`
- 时间: `{now}`
- 状态: `{status}`
"""
    if detail:
        desp += f"- 详情: {detail}\n"

    return title, desp


def build_cookie_invalid_message(account_name: str) -> tuple[str, str]:
    """构建 Cookie 失效推送消息"""
    title = f"⚠️ Cookie失效 - {account_name}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S +08:00")

    desp = f"""### Cookie 失效告警

- 账号: `{account_name}`
- 时间: `{now}`
- 状态: `INVALID`

请尽快使用客户端重新上传 Cookie。"""

    return title, desp
