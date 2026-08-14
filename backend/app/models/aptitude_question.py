"""
SQLAlchemy model for aptitude_questions table.
Matches actual DB schema exactly.
"""

from sqlalchemy import Column, BigInteger, Integer, String, Text, Numeric, Enum, Boolean, TIMESTAMP, text, CheckConstraint
from sqlalchemy.orm import relationship
from .base import Base
import enum


class AptitudeCategoryEnum(str, enum.Enum):
    """All 7 categories present in the DB data."""
    NUMERICAL_REASONING = 'Numerical Reasoning'
    LOGICAL_REASONING = 'Logical Reasoning'
    VERBAL_REASONING = 'Verbal Reasoning'
    PATTERN_RECOGNITION = 'Pattern Recognition'
    SPATIAL_REASONING = 'Spatial Reasoning'
    ANALYTICAL_PROBLEM_SOLVING = 'Analytical Problem Solving'
    DATA_INTERPRETATION = 'Data Interpretation'


class AptitudeDifficultyEnum(str, enum.Enum):
    """Aptitude difficulty uses UPPERCASE in the DB, unlike academic_questions."""
    EASY = 'EASY'
    AVERAGE = 'AVERAGE'
    DIFFICULT = 'DIFFICULT'


class AptitudeQuestion(Base):
    __tablename__ = 'aptitude_questions'

    aptitude_question_id = Column(BigInteger, primary_key=True, autoincrement=True)
    question_code = Column(String(50), nullable=False, unique=True)
    aptitude_slab = Column(String(20), nullable=False, server_default='5-7')
    category = Column(String(100), nullable=False)
    topic = Column(String(150), nullable=False)
    difficulty = Column(Enum(AptitudeDifficultyEnum), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=False)
    option_d = Column(String(500), nullable=False)
    correct_option = Column(String(1), nullable=False)
    correct_answer_text = Column(String(500), nullable=False)
    explanation = Column(Text, nullable=True)
    estimated_time_seconds = Column(Integer, nullable=False)
    marks = Column(Numeric(5, 2), nullable=False, server_default=text('1.00'))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
