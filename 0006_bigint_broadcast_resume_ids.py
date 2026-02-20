"""use bigint for broadcast resume ids

Revision ID: 0006_bigint_broadcast_resume_ids
Revises: 0005_users_broadcast_jobs
Create Date: 2026-02-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_bigint_broadcast_resume_ids"
down_revision: Union[str, None] = "0005_users_broadcast_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "broadcast_jobs",
        "last_participant_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )
    op.alter_column(
        "broadcast_jobs",
        "last_user_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "broadcast_jobs",
        "last_user_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
    op.alter_column(
        "broadcast_jobs",
        "last_participant_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
