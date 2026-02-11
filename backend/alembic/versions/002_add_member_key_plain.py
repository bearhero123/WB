"""为 member_keys 增加明文字段

Revision ID: 002_add_member_key_plain
Revises: 001_init
Create Date: 2026-02-11 21:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_add_member_key_plain"
down_revision: Union[str, None] = "001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("member_keys", sa.Column("key_plain", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("member_keys", "key_plain")
