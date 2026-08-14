"""
SQLAlchemy model for student_profiles table.

After migration 001: student_name dropped, first_name/last_name/DOB/school_name/
academic_year dates added. Original columns (medium, study_goal, daily_study_hours,
preferred_study_time, revision_preference) remain from the base schema.
"""

from sqlalchemy import Column, BigInteger, String, Numeric, ForeignKey, Date, Enum, TIMESTAMP, text
from sqlalchemy.orm import relationship
from .base import Base
import enum


class MediumEnum(str, enum.Enum):
    English = 'English'
    Marathi = 'Marathi'
    Hindi = 'Hindi'


class StudyGoalEnum(str, enum.Enum):
    EXAM_PREPARATION = 'EXAM_PREPARATION'
    SKILL_BUILDING = 'SKILL_BUILDING'
    GENERAL_LEARNING = 'GENERAL_LEARNING'


class PreferredStudyTimeEnum(str, enum.Enum):
    MORNING = 'MORNING'
    AFTERNOON = 'AFTERNOON'
    EVENING = 'EVENING'
    NIGHT = 'NIGHT'


class RevisionPreferenceEnum(str, enum.Enum):
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'
    BOTH = 'BOTH'


class StudentProfile(Base):
    __tablename__ = 'student_profiles'

    student_id = Column(BigInteger, primary_key=True, autoincrement=True)
    board_id = Column(BigInteger, ForeignKey('boards.board_id', ondelete='RESTRICT'), nullable=False)
    standard_id = Column(BigInteger, ForeignKey('standards.standard_id', ondelete='RESTRICT'), nullable=False)


    # Original fields from base schema
    medium = Column(Enum(MediumEnum), nullable=False, server_default='English')
    study_goal = Column(Enum(StudyGoalEnum), nullable=False)
    daily_study_hours = Column(Numeric(4, 2), nullable=False)
    preferred_study_time = Column(Enum(PreferredStudyTimeEnum), nullable=False)
    revision_preference = Column(Enum(RevisionPreferenceEnum), nullable=False)

    # Added by migration 001
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    username = Column(String(100), unique=True, nullable=True)
    password = Column(String(255), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    school_name = Column(String(255), nullable=True)
    preferred_study_start_time = Column(String(5), nullable=True)
    preferred_study_end_time = Column(String(5), nullable=True)
    academic_year_start_date = Column(Date, nullable=False)
    academic_year_end_date = Column(Date, nullable=False)

    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    board = relationship("Board", back_populates="student_profiles")
    standard = relationship("Standard", back_populates="student_profiles")
    diagnostic_sessions = relationship("DiagnosticSession", back_populates="student")
    chapter_mastery = relationship("ChapterMastery", back_populates="student")
    daily_plan_tasks = relationship("DailyPlanTask", back_populates="student")
