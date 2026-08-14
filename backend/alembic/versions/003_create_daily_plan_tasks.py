"""create_daily_plan_tasks

Revision ID: 003
Revises: 002
Create Date: 2026-08-11 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import BIGINT


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('daily_plan_tasks',
        sa.Column('task_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('student_id', BIGINT(unsigned=True), nullable=False),
        sa.Column('plan_date', sa.Date(), nullable=False),
        sa.Column('chapter_id', BIGINT(unsigned=True), nullable=False),
        sa.Column('allocated_minutes', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'IN_PROGRESS', 'SKIPPED', name='task_status_enum'), server_default='PENDING', nullable=False),
        sa.Column('carried_forward_from_task_id', sa.BigInteger(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.student_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.chapter_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['carried_forward_from_task_id'], ['daily_plan_tasks.task_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('task_id')
    )


def downgrade() -> None:
    op.drop_table('daily_plan_tasks')
