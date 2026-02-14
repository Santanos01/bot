"""users and broadcast jobs

Revision ID: 0005_users_broadcast_jobs
Revises: 0004_ticket_number
Create Date: 2026-02-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_users_broadcast_jobs"
down_revision: Union[str, None] = "0004_ticket_number"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64)),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("can_dm", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("user_id", name="uq_users_user_id"),
    )

    op.create_table(
        "broadcast_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("giveaway_id", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("organizer", sa.String(length=128)),
        sa.Column("is_global", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_participant_id", sa.Integer()),
        sa.Column("last_user_id", sa.Integer()),
        sa.Column("sent_ok", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_fail", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["giveaway_id"], ["giveaways.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_broadcast_jobs_status", "broadcast_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_broadcast_jobs_status", table_name="broadcast_jobs")
    op.drop_table("broadcast_jobs")
    op.drop_table("users")
