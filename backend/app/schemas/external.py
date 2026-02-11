"""外部 API 请求/响应 Schema（兼容 GUI 客户端）"""

from typing import Optional, Any
from pydantic import BaseModel, Field


class SchedulePayload(BaseModel):
    enabled: bool = True
    time: str = "08:00"
    random_delay: int = Field(300, ge=0, le=86400)


class CookieUpdateRequest(BaseModel):
    """与 GUI 客户端 Payload 完全一致"""
    account_name: Optional[str] = ""
    SUB: str = ""
    SUBP: str = ""
    T_WM: str = Field("", alias="_T_WM")
    sendkey: Optional[str] = ""
    sync_env: Optional[bool] = True  # 接受但忽略
    schedule: Optional[SchedulePayload] = None
    apply_schedule: Optional[bool] = True

    model_config = {"populate_by_name": True}


class ExternalResponse(BaseModel):
    ok: bool
    message: str = ""
    account: Optional[str] = None
    account_name: Optional[str] = None
    notification: Optional[dict] = None
    cron: Optional[dict] = None


class TaskLogResponse(BaseModel):
    id: int
    account_id: Optional[int] = None
    account_name: Optional[str] = None
    event_type: str
    status: str
    detail: Optional[Any] = None
    message: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}
