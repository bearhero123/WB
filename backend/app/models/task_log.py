"""任务日志 ORM 模型"""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TaskLog(Base):
    __tablename__ = "task_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    account = relationship("Account", lazy="selectin")

    # checkin / cookie_update / cookie_invalid / push / push_test
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    # success / partial / fail
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    # 详情 (JSON)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 摘要文本
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False, index=True)
