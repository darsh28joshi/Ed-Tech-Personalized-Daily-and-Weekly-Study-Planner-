from sqlalchemy import Column, BigInteger, String, ForeignKey, Boolean, TIMESTAMP, text
from sqlalchemy.orm import relationship
from .base import Base

class Course(Base):
    __tablename__ = 'courses'

    course_id = Column(BigInteger, primary_key=True, autoincrement=True)
    board_id = Column(BigInteger, ForeignKey('boards.board_id', ondelete='CASCADE'), nullable=False)
    standard_id = Column(BigInteger, ForeignKey('standards.standard_id', ondelete='CASCADE'), nullable=False)
    course_code = Column(String(50), nullable=False, unique=True)
    course_name = Column(String(150), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text('1'))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    board = relationship("Board")
    standard = relationship("Standard", back_populates="courses")
    academic_questions = relationship("AcademicQuestion", back_populates="course")

