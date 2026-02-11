"""时间处理工具"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.config import settings


def to_tz_iso(dt: datetime | None, tz_name: str | None = None) -> str:
    """将 datetime 统一序列化为带时区的 ISO 字符串。

    约定：项目历史中数据库内的 naive datetime 代表 UTC 时间，
    因此遇到 naive 时按 UTC 解释，再转换到目标时区。
    """
    if not dt:
        return ""

    target_tz = ZoneInfo(tz_name or settings.TZ)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(target_tz).isoformat(timespec="seconds")


def to_tz_datetime(dt: datetime | None, tz_name: str | None = None) -> datetime | None:
    """将 datetime 转为带时区 datetime（默认 settings.TZ）。"""
    if not dt:
        return None

    target_tz = ZoneInfo(tz_name or settings.TZ)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(target_tz)
