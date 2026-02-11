"""账号相关 Schema"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.utils.time import to_tz_datetime


class AccountCreate(BaseModel):
    account_name: str = Field(..., min_length=1, max_length=100)
    schedule_enabled: bool = False
    schedule_time: str = "08:00"
    schedule_random_delay: int = Field(300, ge=0, le=86400)
    retry_count: int = Field(3, ge=1, le=10)
    request_interval: float = Field(2.0, ge=0.5, le=30.0)
    sendkey: Optional[str] = None


class AccountUpdate(BaseModel):
    account_name: Optional[str] = Field(None, min_length=1, max_length=100)
    cookie_sub: Optional[str] = None
    cookie_subp: Optional[str] = None
    cookie_twm: Optional[str] = None
    cookie_updated_at: Optional[datetime] = None
    schedule_enabled: Optional[bool] = None
    schedule_time: Optional[str] = None
    schedule_random_delay: Optional[int] = Field(None, ge=0, le=86400)
    retry_count: Optional[int] = Field(None, ge=1, le=10)
    request_interval: Optional[float] = Field(None, ge=0.5, le=30.0)
    sendkey: Optional[str] = None


class AccountResponse(BaseModel):
    id: int
    account_name: str
    cookie_sub: Optional[str] = None
    cookie_subp: Optional[str] = None
    cookie_twm: Optional[str] = None
    cookie_updated_at: Optional[datetime] = None
    schedule_enabled: bool
    schedule_time: str
    schedule_random_delay: int
    retry_count: int
    request_interval: float
    sendkey: Optional[str] = None
    last_checkin_at: Optional[datetime] = None
    last_checkin_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # 计算字段
    has_cookie: bool = False
    cookie_status: str = "empty"  # empty / valid / unknown

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_cookie_status(cls, account):
        data = cls.model_validate(account)
        data.cookie_updated_at = to_tz_datetime(data.cookie_updated_at)
        data.last_checkin_at = to_tz_datetime(data.last_checkin_at)
        data.created_at = to_tz_datetime(data.created_at)
        data.updated_at = to_tz_datetime(data.updated_at)
        data.has_cookie = bool(account.cookie_sub and account.cookie_subp)
        if account.cookie_sub and account.cookie_subp:
            data.cookie_status = "valid"
        elif account.cookie_sub or account.cookie_subp:
            data.cookie_status = "unknown"
        else:
            data.cookie_status = "empty"
        return data
