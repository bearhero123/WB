"""管理后台 — 任务与签到路由"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_admin
from app.models.account import Account
from app.models.task_log import TaskLog
from app.schemas.external import TaskLogResponse
from app.services import account_service, checkin_service, cookie_service
from app.services.scheduler_service import (
    apply_account_schedule,
    apply_all_schedules,
    get_scheduler_status,
)
from app.utils.time import to_tz_iso

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/tasks",
    tags=["Admin-Tasks"],
    dependencies=[Depends(require_admin)],
)


@router.post("/checkin/{account_id}")
async def manual_checkin(
    account_id: int,
    db: AsyncSession = Depends(get_db),
):
    """手动触发单个账号签到"""
    account = await account_service.get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    try:
        result = await checkin_service.run_checkin(db, account)
        return {"ok": True, "message": "签到完成", "result": result}
    except Exception as e:
        logger.error(f"手动签到异常: {e}")
        return {"ok": False, "message": f"签到异常: {str(e)}"}


@router.post("/checkin-all")
async def manual_checkin_all(db: AsyncSession = Depends(get_db)):
    """手动触发所有启用账号签到"""
    accounts = await account_service.get_all_scheduled_accounts(db)
    results = []
    for account in accounts:
        try:
            result = await checkin_service.run_checkin(db, account)
            results.append({"account": account.account_name, "ok": True, "result": result})
        except Exception as e:
            results.append({"account": account.account_name, "ok": False, "error": str(e)})
    return {"ok": True, "message": f"已执行 {len(results)} 个账号", "results": results}


@router.post("/validate-cookie/{account_id}")
async def validate_cookie(
    account_id: int,
    db: AsyncSession = Depends(get_db),
):
    """验证账号 Cookie 有效性"""
    account = await account_service.get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.cookie_sub:
        return {"ok": False, "message": "账号未配置 Cookie"}

    is_valid, info = await cookie_service.validate_cookie(
        account.cookie_sub, account.cookie_subp, account.cookie_twm
    )
    return {
        "ok": is_valid,
        "message": "Cookie 有效" if is_valid else "Cookie 已失效",
        "user_info": info,
    }


@router.post("/apply-schedules")
async def api_apply_schedules():
    """重新加载所有定时任务"""
    count = await apply_all_schedules()
    return {"ok": True, "message": f"已应用 {count} 个定时任务"}


@router.post("/apply-schedule/{account_id}")
async def api_apply_schedule(account_id: int):
    """重新加载单个账号定时任务"""
    await apply_account_schedule(account_id)
    return {"ok": True, "message": "定时任务已更新"}


@router.get("/scheduler-status")
async def api_scheduler_status():
    """获取调度器状态"""
    jobs = get_scheduler_status()
    return {"ok": True, "jobs": jobs, "total": len(jobs)}


@router.get("/logs", response_model=list[TaskLogResponse])
async def get_task_logs(
    account_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """查询任务日志"""
    query = select(TaskLog).order_by(desc(TaskLog.created_at))

    if account_id is not None:
        query = query.where(TaskLog.account_id == account_id)
    if event_type:
        query = query.where(TaskLog.event_type == event_type)
    if status:
        query = query.where(TaskLog.status == status)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    response = []
    for log in logs:
        r = TaskLogResponse(
            id=log.id,
            account_id=log.account_id,
            event_type=log.event_type,
            status=log.status,
            detail=log.detail,
            message=log.message,
            created_at=to_tz_iso(log.created_at),
        )
        # 尝试获取账号名
        if log.account_id:
            acc = await account_service.get_account_by_id(db, log.account_id)
            if acc:
                r.account_name = acc.account_name
        response.append(r)

    return response
