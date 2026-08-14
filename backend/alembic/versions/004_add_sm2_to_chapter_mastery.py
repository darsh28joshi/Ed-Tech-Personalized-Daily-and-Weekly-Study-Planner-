"""add_sm2_to_chapter_mastery

Revision ID: 004
Revises: 003
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chapter_mastery', sa.Column('ease_factor', sa.Numeric(precision=4, scale=2), server_default='2.50', nullable=False))
    op.add_column('chapter_mastery', sa.Column('interval_days', sa.Integer(), server_default='1', nullable=False))
    op.add_column('chapter_mastery', sa.Column('repetitions', sa.Integer(), server_default='0', nullable=False))
    op.add_column('chapter_mastery', sa.Column('next_review_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('chapter_mastery', 'next_review_date')
    op.drop_column('chapter_mastery', 'repetitions')
    op.drop_column('chapter_mastery', 'interval_days')
    op.drop_column('chapter_mastery', 'ease_factor')
