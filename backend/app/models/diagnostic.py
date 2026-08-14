"""
SQLAlchemy model for diagnostic_sessions, diagnostic_questions,
diagnostic_responses, and diagnostic_reports tables.

Matches actual DB schema — diagnostic_sessions has entry_point and standard_id.
"""

from sqlalchemy import Column, BigInteger, Integer, String, Enum, ForeignKey, TIMESTAMP, text, JSON, Numeric, Boolean
from sqlalchemy.orm import relationship
from .base import Base
import enum


class SessionStatusEnum(str, enum.Enum):
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    ABANDONED = 'ABANDONED'


class EntryPointEnum(str, enum.Enum):
    """Mirrors the MySQL enum on diagnostic_sessions.entry_point exactly."""
    START_OF_YEAR = 'START_OF_YEAR'
    MID_SEMESTER = 'MID_SEMESTER'
    END_OF_TERM = 'END_OF_TERM'


class QuestionSourceEnum(str, enum.Enum):
    ACADEMIC = 'ACADEMIC'
    APTITUDE = 'APTITUDE'


class DiagnosticSectionEnum(str, enum.Enum):
    APTITUDE = 'APTITUDE'
    ACADEMIC = 'ACADEMIC'


class DiagnosticSession(Base):
    __tablename__ = 'diagnostic_sessions'

    session_id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, ForeignKey('student_profiles.student_id', ondelete='CASCADE'), nullable=False)
    entry_point = Column(Enum(EntryPointEnum), nullable=False)
    standard_id = Column(BigInteger, ForeignKey('standards.standard_id'), nullable=False)
    started_at = Column(TIMESTAMP, nullable=True, server_default=text('CURRENT_TIMESTAMP'))
    completed_at = Column(TIMESTAMP, nullable=True)
    status = Column(Enum(SessionStatusEnum), nullable=False, server_default='IN_PROGRESS')

    student = relationship("StudentProfile", back_populates="diagnostic_sessions")
    diagnostic_questions = relationship("DiagnosticQuestion", back_populates="session", cascade="all, delete-orphan")
    diagnostic_reports = relationship("DiagnosticReport", back_populates="session", uselist=False, cascade="all, delete-orphan")
    diagnostic_responses = relationship("DiagnosticResponse", back_populates="session", cascade="all, delete-orphan")
    aptitude_category_scores = relationship("AptitudeCategoryScore", back_populates="session", cascade="all, delete-orphan")


class DiagnosticQuestion(Base):
    __tablename__ = 'diagnostic_questions'

    diagnostic_question_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey('diagnostic_sessions.session_id', ondelete='CASCADE'), nullable=False)
    question_source = Column(Enum(QuestionSourceEnum), nullable=False)
    question_id = Column(BigInteger, nullable=False)
    question_order = Column(Integer, nullable=False)
    section = Column(Enum(DiagnosticSectionEnum), nullable=False)

    session = relationship("DiagnosticSession", back_populates="diagnostic_questions")


class DiagnosticResponse(Base):
    __tablename__ = 'diagnostic_responses'

    response_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey('diagnostic_sessions.session_id', ondelete='CASCADE'), nullable=False)
    question_source = Column(Enum(QuestionSourceEnum), nullable=False)
    question_id = Column(BigInteger, nullable=False)
    chapter_id = Column(BigInteger, nullable=True)
    selected_option = Column(String(1), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)

    session = relationship("DiagnosticSession", back_populates="diagnostic_responses")


class DiagnosticReport(Base):
    __tablename__ = 'diagnostic_reports'

    session_id = Column(BigInteger, ForeignKey('diagnostic_sessions.session_id', ondelete='CASCADE'), primary_key=True)
    aptitude_score = Column(Numeric(5, 2), nullable=False, server_default=text('0.00'))
    aptitude_percentile = Column(Numeric(5, 2), nullable=False, server_default=text('0.00'))
    academic_accuracy = Column(Numeric(5, 2), nullable=False, server_default=text('0.00'))
    study_health_score = Column(Numeric(5, 2), nullable=False, server_default=text('0.00'))
    weakest_chapter_ids = Column(JSON, nullable=True)
    generated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))

    session = relationship("DiagnosticSession", back_populates="diagnostic_reports")
