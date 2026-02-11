"""账号 ORM 模型"""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Boolean, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # Cookie 信息
    cookie_sub: Mapped[str | None] = mapped_column(Text, nullable=True)
    cookie_subp: Mapped[str | None] = mapped_column(Text, nullable=True)
    cookie_twm: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cookie_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 定时配置
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    schedule_time: Mapped[str] = mapped_column(String(10), default="08:00", nullable=False)
    schedule_random_delay: Mapped[int] = mapped_column(Integer, default=300, nullable=False)

    # 运行参数
    retry_count: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    request_interval: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)

    # 推送
    sendkey: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # 签到状态
    last_checkin_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_checkin_status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False
    )

    member_keys = relationship("MemberKey", back_populates="bound_account", lazy="selectin")
