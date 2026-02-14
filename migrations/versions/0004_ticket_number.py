"""participant ticket number

Revision ID: 0004_ticket_number
Revises: 0003_winner_message
Create Date: 2026-02-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_ticket_number"
down_revision: Union[str, None] = "0003_winner_message"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("participants", sa.Column("ticket_number", sa.Integer(), nullable=False, server_default="1000"))
    op.alter_column("participants", "ticket_number", server_default=None)


def downgrade() -> None:
    op.drop_column("participants", "ticket_number")
