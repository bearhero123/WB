"""初始化数据库表

Revision ID: 001_init
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # accounts 表
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("account_name", sa.String(100), unique=True, nullable=False),
        sa.Column("cookie_sub", sa.Text(), nullable=True),
        sa.Column("cookie_subp", sa.Text(), nullable=True),
        sa.Column("cookie_twm", sa.Text(), nullable=True),
        sa.Column("cookie_updated_at", sa.DateTime(), nullable=True),
        sa.Column("schedule_enabled", sa.Boolean(), server_default="false"),
        sa.Column("schedule_time", sa.String(10), server_default="08:00"),
        sa.Column("schedule_random_delay", sa.Integer(), server_default="300"),
        sa.Column("retry_count", sa.Integer(), server_default="2"),
        sa.Column("request_interval", sa.Float(), server_default="3.0"),
        sa.Column("sendkey", sa.String(200), nullable=True),
        sa.Column("last_checkin_at", sa.DateTime(), nullable=True),
        sa.Column("last_checkin_status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # member_keys 表
    op.create_table(
        "member_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("label", sa.String(100), nullable=True, server_default=""),
        sa.Column("key_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("bound_account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_member_keys_key_hash", "member_keys", ["key_hash"])

    # task_logs 表
    op.create_table(
        "task_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_task_logs_account_id", "task_logs", ["account_id"])
    op.create_index("ix_task_logs_event_type", "task_logs", ["event_type"])
    op.create_index("ix_task_logs_created_at", "task_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("task_logs")
    op.drop_table("member_keys")
    op.drop_table("accounts")
