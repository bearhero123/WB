"""管理后台 — 密钥管理路由"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_admin
from app.schemas.member_key import (
    MemberKeyCreate,
    MemberKeyUpdate,
    MemberKeyResponse,
    MemberKeyCreateResponse,
)
from app.services import key_service

router = APIRouter(
    prefix="/api/admin/keys",
    tags=["Admin-Keys"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[MemberKeyResponse])
async def list_keys(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    keys = await key_service.get_keys(db, skip=skip, limit=limit)
    return [MemberKeyResponse.from_orm_with_account(k) for k in keys]


@router.get("/{key_id}", response_model=MemberKeyResponse)
async def get_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
):
    key = await key_service.get_key_by_id(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    return MemberKeyResponse.from_orm_with_account(key)


@router.post("", response_model=MemberKeyCreateResponse, status_code=201)
async def create_key(
    body: MemberKeyCreate,
    db: AsyncSession = Depends(get_db),
):
    member_key, plain_key = await key_service.create_key(db, body)
    resp = MemberKeyResponse.from_orm_with_account(member_key)
    return MemberKeyCreateResponse(
        **resp.model_dump(),
        plain_key=plain_key,
    )


@router.put("/{key_id}", response_model=MemberKeyResponse)
async def update_key(
    key_id: int,
    body: MemberKeyUpdate,
    db: AsyncSession = Depends(get_db),
):
    key = await key_service.update_key(db, key_id, body)
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    return MemberKeyResponse.from_orm_with_account(key)


@router.delete("/{key_id}")
async def delete_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
):
    ok = await key_service.delete_key(db, key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="密钥不存在")
    return {"ok": True, "message": "密钥已删除"}
