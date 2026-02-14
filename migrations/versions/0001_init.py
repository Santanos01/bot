"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-02-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "giveaways",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("channel_username", sa.String(length=128), nullable=False),
        sa.Column("winners_mode", sa.String(length=16), nullable=False),
        sa.Column("winners_count", sa.Integer()),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("giveaway_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64)),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("can_dm", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["giveaway_id"], ["giveaways.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("giveaway_id", "user_id", name="uq_participants_giveaway_user"),
    )
    op.create_index("ix_participants_giveaway_id", "participants", ["giveaway_id"], unique=False)

    op.create_table(
        "winners",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("giveaway_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("picked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["giveaway_id"], ["giveaways.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_winners_giveaway_id", "winners", ["giveaway_id"], unique=False)

    op.create_table(
        "broadcasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("giveaway_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_ok", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_fail", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["giveaway_id"], ["giveaways.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_broadcasts_giveaway_id", "broadcasts", ["giveaway_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_broadcasts_giveaway_id", table_name="broadcasts")
    op.drop_table("broadcasts")
    op.drop_index("ix_winners_giveaway_id", table_name="winners")
    op.drop_table("winners")
    op.drop_index("ix_participants_giveaway_id", table_name="participants")
    op.drop_table("participants")
    op.drop_table("giveaways")
