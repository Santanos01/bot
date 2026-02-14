"""bigint user ids

Revision ID: 0002_bigint_users
Revises: 0001_init
Create Date: 2026-02-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_bigint_users"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("giveaways", "created_by", existing_type=sa.Integer(), type_=sa.BigInteger())
    op.alter_column("participants", "user_id", existing_type=sa.Integer(), type_=sa.BigInteger())
    op.alter_column("winners", "user_id", existing_type=sa.Integer(), type_=sa.BigInteger())


def downgrade() -> None:
    op.alter_column("winners", "user_id", existing_type=sa.BigInteger(), type_=sa.Integer())
    op.alter_column("participants", "user_id", existing_type=sa.BigInteger(), type_=sa.Integer())
    op.alter_column("giveaways", "created_by", existing_type=sa.BigInteger(), type_=sa.Integer())
