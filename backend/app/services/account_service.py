"""账号 CRUD 服务"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate


async def get_accounts(
    db: AsyncSession, skip: int = 0, limit: int = 50
) -> List[Account]:
    """获取账号列表"""
    result = await db.execute(
        select(Account).order_by(Account.id.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_account_by_id(db: AsyncSession, account_id: int) -> Optional[Account]:
    """根据 ID 获取账号"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    return result.scalar_one_or_none()


async def get_account_by_name(db: AsyncSession, account_name: str) -> Optional[Account]:
    """根据名称获取账号"""
    result = await db.execute(select(Account).where(Account.account_name == account_name))
    return result.scalar_one_or_none()


async def create_account(db: AsyncSession, data: AccountCreate) -> Account:
    """创建账号"""
    account = Account(**data.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def update_account(db: AsyncSession, account_id: int, data: AccountUpdate) -> Optional[Account]:
    """更新账号"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(account, key, value)
    account.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(account)
    return account


async def delete_account(db: AsyncSession, account_id: int) -> bool:
    """删除账号"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        return False
    await db.delete(account)
    await db.commit()
    return True


async def get_all_scheduled_accounts(db: AsyncSession) -> List[Account]:
    """获取所有启用定时的账号"""
    result = await db.execute(
        select(Account).where(Account.schedule_enabled == True)
    )
    return list(result.scalars().all())
