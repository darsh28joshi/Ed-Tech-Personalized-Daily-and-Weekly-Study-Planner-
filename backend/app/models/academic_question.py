"""
SQLAlchemy model for academic_questions table.
Matches actual DB schema column names exactly.
"""

from sqlalchemy import Column, BigInteger, Integer, String, Text, ForeignKey, Enum, Boolean, TIMESTAMP, text
from sqlalchemy.orm import relationship
from .base import Base
import enum


class DifficultyEnum(str, enum.Enum):
    EASY = 'Easy'
    AVERAGE = 'Average'
    DIFFICULT = 'Difficult'


class AcademicQuestion(Base):
    __tablename__ = 'academic_questions'

    question_id = Column(BigInteger, primary_key=True, autoincrement=True)
    course_id = Column(BigInteger, ForeignKey('courses.course_id'), nullable=False)
    subject_id = Column(BigInteger, ForeignKey('subjects.subject_id'), nullable=False)
    chapter_id = Column(BigInteger, ForeignKey('chapters.chapter_id'), nullable=False)
    question_type_id = Column(BigInteger, ForeignKey('question_types.question_type_id'), nullable=False)
    question_code = Column(String(150), nullable=True, unique=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=True)
    option_b = Column(Text, nullable=True)
    option_c = Column(Text, nullable=True)
    option_d = Column(Text, nullable=True)
    correct_option = Column(String(1), nullable=True)
    explanation = Column(Text, nullable=True)
    # DB column is 'difficulty', not 'difficulty_level'
    difficulty = Column(Enum(DifficultyEnum), nullable=True)
    marks = Column(Integer, server_default=text('1'))
    # DB column is 'estimated_seconds', not 'estimated_time_seconds'
    estimated_seconds = Column(Integer, server_default=text('60'))
    created_at = Column(TIMESTAMP, nullable=True, server_default=text('CURRENT_TIMESTAMP'))

    course = relationship("Course", back_populates="academic_questions")
    subject = relationship("Subject", back_populates="academic_questions")
    chapter = relationship("Chapter", back_populates="academic_questions")
    question_type = relationship("QuestionType", back_populates="academic_questions")
