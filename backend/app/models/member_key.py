"""会员 Key ORM 模型"""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MemberKey(Base):
    __tablename__ = "member_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True, default="")
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # 绑定账号
    bound_account_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    bound_account = relationship("Account", lazy="selectin")

    # 状态
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
