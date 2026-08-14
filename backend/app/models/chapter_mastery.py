"""
SQLAlchemy model for chapter_mastery table.
Matches database schema including SM-2 spaced repetition columns.
"""

from sqlalchemy import Column, BigInteger, Numeric, Integer, Date, Enum, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import relationship
from .base import Base
import enum


class ConfidenceEnum(str, enum.Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'


class ChapterMastery(Base):
    __tablename__ = 'chapter_mastery'

    # Composite primary key (student_id, chapter_id)
    student_id = Column(BigInteger, ForeignKey('student_profiles.student_id', ondelete='CASCADE'), primary_key=True)
    chapter_id = Column(BigInteger, ForeignKey('chapters.chapter_id', ondelete='CASCADE'), primary_key=True)
    mastery_score = Column(Numeric(5, 2), nullable=False)
    confidence = Column(Enum(ConfidenceEnum), nullable=False)
    last_assessed = Column(TIMESTAMP, nullable=True, server_default=text('CURRENT_TIMESTAMP'))

    # SM-2 columns added for spaced repetition
    ease_factor = Column(Numeric(4, 2), nullable=False, server_default=text('2.50'))
    interval_days = Column(Integer, nullable=False, server_default=text('1'))
    repetitions = Column(Integer, nullable=False, server_default=text('0'))
    next_review_date = Column(Date, nullable=True)

    student = relationship("StudentProfile", back_populates="chapter_mastery")
    chapter = relationship("Chapter", back_populates="chapter_mastery")
