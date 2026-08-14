from sqlalchemy import Column, BigInteger, String
from sqlalchemy.orm import relationship
from .base import Base


class QuestionType(Base):
    __tablename__ = 'question_types'

    question_type_id = Column(BigInteger, primary_key=True, autoincrement=True)
    type_code = Column(String(50), nullable=False, unique=True)
    type_name = Column(String(100), nullable=False)

    academic_questions = relationship("AcademicQuestion", back_populates="question_type")
