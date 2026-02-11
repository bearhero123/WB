"""鉴权依赖注入"""

from datetime import datetime, timezone
from fastapi import Header, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.member_key import MemberKey
from app.utils.security import hash_key


async def require_admin(x_admin_key: str = Header(None)):
    """管理员鉴权: 检查 X-Admin-Key Header"""
    if not x_admin_key or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail={"ok": False, "message": "管理员密钥无效"})
    return True


async def require_member_key(
    db: AsyncSession = Depends(get_db),
    x_member_key: str = Header(None),
    x_access_key: str = Header(None),
) -> MemberKey:
    """
    会员 Key 鉴权:
    - 同时检查 X-Member-Key 和 X-Access-Key, 任一匹配即可
    - SHA-256 后与数据库 key_hash 匹配
    - 校验 enabled 和 expires_at
    - 更新 last_used_at
    """
    raw_key = x_member_key or x_access_key
    if not raw_key:
        raise HTTPException(
            status_code=401,
            detail={"ok": False, "message": "缺少会员密钥，请提供 X-Member-Key 或 X-Access-Key"},
        )

    key_hashed = hash_key(raw_key)
    result = await db.execute(select(MemberKey).where(MemberKey.key_hash == key_hashed))
    member_key = result.scalar_one_or_none()

    if not member_key:
        raise HTTPException(status_code=401, detail={"ok": False, "message": "会员密钥无效"})

    if not member_key.enabled:
        raise HTTPException(status_code=403, detail={"ok": False, "message": "会员密钥已被禁用"})

    now = datetime.now(timezone.utc)
    if member_key.expires_at and member_key.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=403, detail={"ok": False, "message": "会员密钥已过期"})

    # 更新最近使用时间
    member_key.last_used_at = now.replace(tzinfo=None)
    await db.commit()

    return member_key
