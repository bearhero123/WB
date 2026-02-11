"""会员 Key 相关 Schema"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.utils.time import to_tz_datetime


class MemberKeyCreate(BaseModel):
    label: Optional[str] = Field(None, max_length=100)
    bound_account_id: Optional[int] = None
    expires_at: Optional[datetime] = None


class MemberKeyUpdate(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=100)
    enabled: Optional[bool] = None
    bound_account_id: Optional[int] = None
    expires_at: Optional[datetime] = None


class MemberKeyResponse(BaseModel):
    id: int
    label: Optional[str] = None
    bound_account_id: Optional[int] = None
    bound_account_name: Optional[str] = None
    enabled: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_account(cls, key):
        data = cls.model_validate(key)
        data.expires_at = to_tz_datetime(data.expires_at)
        data.last_used_at = to_tz_datetime(data.last_used_at)
        data.created_at = to_tz_datetime(data.created_at)
        if key.bound_account:
            data.bound_account_name = key.bound_account.account_name
        return data


class MemberKeyCreateResponse(MemberKeyResponse):
    """创建 Key 时返回明文（仅此一次）"""
    plain_key: str
