"""管理后台 — 账号管理路由"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_admin
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from app.services import account_service
from app.services.scheduler_service import apply_account_schedule

router = APIRouter(
    prefix="/api/admin/accounts",
    tags=["Admin-Accounts"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    accounts = await account_service.get_accounts(db, skip=skip, limit=limit)
    return [AccountResponse.from_orm_with_cookie_status(a) for a in accounts]


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
):
    account = await account_service.get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return AccountResponse.from_orm_with_cookie_status(account)


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(
    body: AccountCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await account_service.get_account_by_name(db, body.account_name)
    if existing:
        raise HTTPException(status_code=409, detail="账号名已存在")
    account = await account_service.create_account(db, body)
    await apply_account_schedule(account.id, account)
    return AccountResponse.from_orm_with_cookie_status(account)


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    body: AccountUpdate,
    db: AsyncSession = Depends(get_db),
):
    account = await account_service.update_account(db, account_id, body)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    await apply_account_schedule(account.id, account)
    return AccountResponse.from_orm_with_cookie_status(account)


@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
):
    ok = await account_service.delete_account(db, account_id)
    if not ok:
        raise HTTPException(status_code=404, detail="账号不存在")
    return {"ok": True, "message": "账号已删除"}
