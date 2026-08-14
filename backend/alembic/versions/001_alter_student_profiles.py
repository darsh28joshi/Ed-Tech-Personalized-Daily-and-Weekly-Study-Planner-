"""alter_student_profiles

Revision ID: 001
Revises: 
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns
    op.add_column('student_profiles', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('student_profiles', sa.Column('last_name', sa.String(length=100), nullable=True))
    op.add_column('student_profiles', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('student_profiles', sa.Column('school_name', sa.String(length=255), nullable=True))
    op.add_column('student_profiles', sa.Column('academic_year_start_date', sa.Date(), nullable=True))
    op.add_column('student_profiles', sa.Column('academic_year_end_date', sa.Date(), nullable=True))

    # 2. Migrate existing data (assuming 'Rahul Sharma')
    # Using raw SQL to split student_name into first_name and last_name where possible, and setting default dates
    op.execute("""
        UPDATE student_profiles
        SET first_name = SUBSTRING_INDEX(student_name, ' ', 1),
            last_name = IF(LOCATE(' ', student_name) > 0, SUBSTRING(student_name, LOCATE(' ', student_name) + 1), ''),
            academic_year_start_date = '2026-06-01',
            academic_year_end_date = '2027-04-30'
    """)

    # 3. Alter columns to be NOT NULL as per schema, drop student_name
    op.alter_column('student_profiles', 'first_name', existing_type=sa.String(length=100), nullable=False)
    op.alter_column('student_profiles', 'last_name', existing_type=sa.String(length=100), nullable=False)
    op.alter_column('student_profiles', 'academic_year_start_date', existing_type=sa.Date(), nullable=False)
    op.alter_column('student_profiles', 'academic_year_end_date', existing_type=sa.Date(), nullable=False)
    
    op.drop_column('student_profiles', 'student_name')


def downgrade() -> None:
    op.add_column('student_profiles', sa.Column('student_name', sa.String(length=255), nullable=True))
    
    op.execute("""
        UPDATE student_profiles
        SET student_name = CONCAT(first_name, ' ', last_name)
    """)
    
    op.alter_column('student_profiles', 'student_name', existing_type=sa.String(length=255), nullable=False)

    op.drop_column('student_profiles', 'academic_year_end_date')
    op.drop_column('student_profiles', 'academic_year_start_date')
    op.drop_column('student_profiles', 'school_name')
    op.drop_column('student_profiles', 'date_of_birth')
    op.drop_column('student_profiles', 'last_name')
    op.drop_column('student_profiles', 'first_name')
