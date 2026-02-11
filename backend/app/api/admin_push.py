"""管理后台 — 推送测试路由"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_admin
from app.services import account_service, push_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/push",
    tags=["Admin-Push"],
    dependencies=[Depends(require_admin)],
)


@router.post("/test")
async def test_push(
    sendkey: str = Query(None, description="指定 SendKey, 为空使用系统默认"),
    db: AsyncSession = Depends(get_db),
):
    """发送测试推送"""
    target_key = sendkey or push_service._get_sendkey()
    if not target_key:
        return {"ok": False, "message": "未配置 SendKey"}

    result = await push_service.send_push(
        sendkey=target_key,
        title="微博签到系统 - 测试推送",
        desp="这是一条测试推送消息\n\n如果您收到此消息，说明推送配置正常。",
    )
    return {
        "ok": result["ok"],
        "message": result["message"],
    }


@router.post("/test/{account_id}")
async def test_push_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
):
    """使用账号的 SendKey 发送测试推送"""
    account = await account_service.get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    target_key = account.sendkey or push_service._get_sendkey()
    if not target_key:
        return {"ok": False, "message": "账号和系统均未配置 SendKey"}

    result = await push_service.send_push(
        sendkey=target_key,
        title=f"测试推送 - {account.account_name}",
        desp=f"这是账号 **{account.account_name}** 的测试推送。",
    )
    return {
        "ok": result["ok"],
        "message": result["message"],
    }
