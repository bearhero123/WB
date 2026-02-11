"""外部 API 路由 — 供 GUI 客户端调用"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_member_key
from app.models.member_key import MemberKey
from app.schemas.external import CookieUpdateRequest, ExternalResponse
from app.services import account_service, cookie_service, push_service
from app.services.scheduler_service import apply_account_schedule

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/external", tags=["External"])


@router.post("/key/verify", response_model=ExternalResponse)
async def verify_key(
    member_key: MemberKey = Depends(require_member_key),
):
    """验证会员密钥"""
    account_name = None
    if member_key.bound_account:
        account_name = member_key.bound_account.account_name

    return ExternalResponse(
        ok=True,
        message="密钥验证成功",
        account=account_name,
        account_name=account_name,
        notification={"type": "info", "text": "密钥有效"},
    )


@router.post("/cookie/update", response_model=ExternalResponse)
async def update_cookie(
    payload: CookieUpdateRequest,
    db: AsyncSession = Depends(get_db),
    member_key: MemberKey = Depends(require_member_key),
):
    """
    更新微博 Cookie
    - 如果 Key 绑定了账号，使用绑定账号
    - 否则使用 payload 中的 account_name，自动创建或更新
    """
    # 确定目标账号名
    account_name = None
    if member_key.bound_account:
        account_name = member_key.bound_account.account_name
    elif payload.account_name:
        account_name = payload.account_name.strip()

    if not account_name:
        return ExternalResponse(
            ok=False,
            message="无法确定目标账号: Key 未绑定账号且请求中未提供 account_name",
        )

    # 检查 Cookie 是否提供
    if not payload.SUB:
        return ExternalResponse(ok=False, message="Cookie SUB 不能为空")

    # 验证 Cookie 有效性
    is_valid, user_info = await cookie_service.validate_cookie(
        payload.SUB, payload.SUBP, payload.T_WM
    )

    if not is_valid:
        return ExternalResponse(
            ok=False,
            message="Cookie 验证失败: 登录状态无效",
            account=account_name,
            account_name=account_name,
        )

    # 获取或创建账号
    account = await account_service.get_account_by_name(db, account_name)

    if account is None:
        # 自动创建账号
        from app.schemas.account import AccountCreate
        account = await account_service.create_account(
            db,
            AccountCreate(account_name=account_name),
        )
        logger.info(f"自动创建账号: {account_name}")

    # 更新 Cookie 字段
    from app.services.account_service import update_account
    from app.schemas.account import AccountUpdate

    update_data = AccountUpdate(
        cookie_sub=payload.SUB,
        cookie_subp=payload.SUBP,
        cookie_twm=payload.T_WM,
        cookie_updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )

    # 如果 Key 未绑定账号, 自动绑定
    if not member_key.bound_account_id:
        member_key.bound_account_id = account.id
        await db.commit()
        logger.info(f"Key {member_key.label} 自动绑定到账号 {account_name}")

    # 处理定时任务配置
    cron_info = None
    if payload.schedule and payload.apply_schedule:
        update_data.schedule_enabled = payload.schedule.enabled
        update_data.schedule_time = payload.schedule.time
        update_data.schedule_random_delay = payload.schedule.random_delay

    account = await update_account(db, account.id, update_data)

    # 应用定时任务
    if payload.schedule and payload.apply_schedule:
        await apply_account_schedule(account.id, account)
        cron_info = {
            "enabled": account.schedule_enabled,
            "time": account.schedule_time,
            "random_delay": account.schedule_random_delay,
        }

    # 推送通知
    title, desp = push_service.build_cookie_update_message(
        account.account_name,
        True,
        str(user_info) if user_info else "",
    )
    await push_service.push_event(
        db=db,
        event_type="cookie_update",
        title=title,
        desp=desp,
        account=account,
    )

    return ExternalResponse(
        ok=True,
        message="Cookie 更新成功",
        account=account_name,
        account_name=account_name,
        notification={"type": "success", "text": f"Cookie 已更新 ({account_name})"},
        cron=cron_info,
    )
