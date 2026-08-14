"""
SQLAlchemy model for syllabus_progress table.

Matches actual DB schema:
  - standard_id, subject_id, last_taught_chapter_number, as_of_date
  - Unique constraint on (standard_id, subject_id)
  
NOTE: This is NOT per-student. It tracks syllabus pacing at the standard/subject
level — "how far has Std 7 Math been taught as of this date?" A real deployment
would get this from school-reported data; this prototype seeds it at onboarding.
"""

from sqlalchemy import Column, BigInteger, Integer, Date, ForeignKey, TIMESTAMP, text, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


class SyllabusProgress(Base):
    __tablename__ = 'syllabus_progress'

    progress_id = Column(BigInteger, primary_key=True, autoincrement=True)
    standard_id = Column(BigInteger, ForeignKey('standards.standard_id'), nullable=False)
    subject_id = Column(BigInteger, ForeignKey('subjects.subject_id'), nullable=False)
    last_taught_chapter_number = Column(Integer, nullable=False, server_default=text('0'))
    as_of_date = Column(Date, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    __table_args__ = (
        UniqueConstraint('standard_id', 'subject_id', name='uq_standard_subject'),
    )

    standard = relationship("Standard", back_populates="syllabus_progress")
    subject = relationship("Subject", back_populates="syllabus_progress")
