"""winner message

Revision ID: 0003_winner_message
Revises: 0002_bigint_users
Create Date: 2026-02-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_winner_message"
down_revision: Union[str, None] = "0002_bigint_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("giveaways", sa.Column("winner_message", sa.Text()))


def downgrade() -> None:
    op.drop_column("giveaways", "winner_message")
