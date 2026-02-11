"""会员 Key 生命周期管理服务"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member_key import MemberKey
from app.schemas.member_key import MemberKeyCreate, MemberKeyUpdate
from app.utils.security import generate_member_key, hash_key


async def get_keys(
    db: AsyncSession, skip: int = 0, limit: int = 50
) -> List[MemberKey]:
    """获取 Key 列表"""
    result = await db.execute(
        select(MemberKey).order_by(MemberKey.id.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_key_by_id(db: AsyncSession, key_id: int) -> Optional[MemberKey]:
    """根据 ID 获取 Key"""
    result = await db.execute(select(MemberKey).where(MemberKey.id == key_id))
    return result.scalar_one_or_none()


async def create_key(db: AsyncSession, data: MemberKeyCreate) -> tuple[MemberKey, str]:
    """
    创建会员 Key
    返回: (MemberKey 对象, 明文 Key)
    明文仅此一次返回
    """
    plain_key = generate_member_key()
    key_hashed = hash_key(plain_key)

    expires_at = data.expires_at
    if expires_at and expires_at.tzinfo:
        expires_at = expires_at.replace(tzinfo=None)

    member_key = MemberKey(
        label=data.label,
        key_hash=key_hashed,
        bound_account_id=data.bound_account_id,
        expires_at=expires_at,
    )
    db.add(member_key)
    await db.commit()
    await db.refresh(member_key)
    return member_key, plain_key


async def update_key(db: AsyncSession, key_id: int, data: MemberKeyUpdate) -> Optional[MemberKey]:
    """更新 Key"""
    result = await db.execute(select(MemberKey).where(MemberKey.id == key_id))
    member_key = result.scalar_one_or_none()
    if not member_key:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "expires_at" in update_data and update_data["expires_at"] and update_data["expires_at"].tzinfo:
        update_data["expires_at"] = update_data["expires_at"].replace(tzinfo=None)

    for key, value in update_data.items():
        setattr(member_key, key, value)
    await db.commit()
    await db.refresh(member_key)
    return member_key


async def delete_key(db: AsyncSession, key_id: int) -> bool:
    """删除 Key"""
    result = await db.execute(select(MemberKey).where(MemberKey.id == key_id))
    member_key = result.scalar_one_or_none()
    if not member_key:
        return False
    await db.delete(member_key)
    await db.commit()
    return True
