"""create_aptitude_category_scores

Revision ID: 002
Revises: 001
Create Date: 2026-08-11 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import BIGINT


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('aptitude_category_scores',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', BIGINT(unsigned=True), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('accuracy', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('percentile', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['diagnostic_sessions.session_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'category', name='uix_session_category')
    )


def downgrade() -> None:
    op.drop_table('aptitude_category_scores')
