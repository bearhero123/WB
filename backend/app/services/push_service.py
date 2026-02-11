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

    根据 Sendkey.md:
    - URL: https://sctapi.ftqq.com/{sendkey}.send
    - title: 最大长度 32
    - desp: Markdown, 最大 32KB
    - 支持 GET(urlencode) 或 POST(form/json)

    返回:
        {"ok": True/False, "status_code": int, "message": str}
    """
    url = SERVERCHAN_URL.format(sendkey=sendkey)

    # title 不能超过 32 字符
    if len(title) > 32:
        title = title[:31] + "…"

    # desp 不能超过 32KB
    if len(desp.encode("utf-8")) > 32000:
        desp = desp[:10000] + "\n\n...(内容过长已截断)"

    data = {"title": title, "desp": desp, "noip": "1"}

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, data=data)

            logger.info(f"Server酱响应: status={resp.status_code}, body={resp.text[:200]}")

            body = {}
            try:
                body = resp.json()
            except Exception:
                pass

            if resp.status_code == 200 and body.get("code") == 0:
                return {"ok": True, "status_code": 200, "message": "推送成功"}

            error_msg = body.get("message", "") or body.get("info", "") or f"HTTP {resp.status_code}"
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
    # 签到结果默认不去重，避免手动测试或短时间重试时收不到推送
    skip_dedup = event_type == "checkin"
    if not force and not skip_dedup and _should_dedup(account_id, event_type):
        logger.info(f"推送已去重: account={account_id}, event={event_type}")
        return {"ok": True, "message": "推送已去重（10分钟内重复事件）"}

    sendkey = _get_sendkey(account)
    if not sendkey:
        logger.warning(
            f"无可用 SendKey, 仅记录日志: {title}. "
            f"account.sendkey={getattr(account, 'sendkey', None) if account else 'N/A'}, "
            f"DEFAULT_SENDKEY={'SET' if settings.DEFAULT_SENDKEY else 'EMPTY'}"
        )
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

def _get_key_info(account: Account) -> str:
    """获取账号关联密钥的有效期信息"""
    if not account or not account.member_keys:
        return "未绑定密钥"

    valid_keys = [k for k in account.member_keys if k.enabled]
    if not valid_keys:
        return "无有效密钥"

    # 检查是否有永久密钥
    if any(k.expires_at is None for k in valid_keys):
        return "永久密钥用户"

    # 计算最晚过期时间
    # 注意：expires_at 存储为无时区 UTC
    latest_expire = max(k.expires_at for k in valid_keys if k.expires_at)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    if latest_expire <= now_utc:
        return "密钥已过期"

    days = (latest_expire - now_utc).days
    return f"剩余 {days} 天"


def build_checkin_message(account: Account, stats: dict) -> tuple[str, str]:
    """构建签到结果推送消息（含超话明细）"""
    account_name = account.account_name
    cookie_status = "有效" if account.cookie_sub else "失效"
    key_info = _get_key_info(account)

    total = stats.get("total", 0)
    success = stats.get("success", 0)
    already = stats.get("already", 0)
    failed = stats.get("failed", 0)

    # title 限制 32 字符
    if total == 0:
        title = f"签到·{account_name}·无超话"
    elif failed == 0:
        title = f"签到·{account_name}·全部完成"
    else:
        title = f"签到·{account_name}·{failed}个失败"
    if len(title) > 32:
        title = title[:31] + "…"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    desp = f"""### 签到任务结果

| 项目 | 值 |
|------|------|
| 账号 | `{account_name}` |
| 时间 | `{now}` |
| 密钥 | `{key_info}` |
| Cookie | `{cookie_status}` |
| 总超话 | **{total}** |
| ✅ 新签到 | **{success}** |
| ☑️ 已签到 | **{already}** |
| ❌ 失败 | **{failed}** |
"""

    # 列出每个超话的签到状态
    checkin_details = stats.get("checkin_details", [])
    if checkin_details:
        desp += "\n### 超话签到明细\n\n"
        desp += "| 序号 | 超话名称 | 状态 | 说明 |\n"
        desp += "|------|----------|------|------|\n"
        for i, item in enumerate(checkin_details, 1):
            status_icon = {"success": "✅", "already": "☑️", "failed": "❌"}.get(item["status"], "❓")
            name = item.get("name", "未知")
            detail = item.get("detail", "")
            # 截断过长的 detail
            if len(detail) > 40:
                detail = detail[:37] + "..."
            desp += f"| {i} | {name} | {status_icon} {item['status']} | {detail} |\n"
    elif total == 0:
        desp += "\n> ⚠️ 未获取到任何关注的超话。\n"
        desp += "> 可能原因：Cookie 已过期、未关注超话、或微博 API 参数配置不正确。\n"

    if stats.get("failed_items"):
        desp += "\n### ❌ 失败详情\n\n"
        for item in stats["failed_items"][:20]:
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
