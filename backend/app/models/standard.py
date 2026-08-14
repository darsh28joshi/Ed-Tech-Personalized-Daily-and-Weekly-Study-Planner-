from sqlalchemy import Column, BigInteger, SmallInteger, String, ForeignKey, Boolean, TIMESTAMP, text, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


class Standard(Base):
    __tablename__ = 'standards'

    standard_id = Column(BigInteger, primary_key=True, autoincrement=True)
    board_id = Column(BigInteger, ForeignKey('boards.board_id', ondelete='RESTRICT'), nullable=False)
    standard_code = Column(String(30), nullable=False, unique=True)
    standard_number = Column(SmallInteger, nullable=False)
    standard_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text('1'))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    __table_args__ = (
        UniqueConstraint('board_id', 'standard_number', name='uq_board_standard'),
    )

    board = relationship("Board", back_populates="standards")
    courses = relationship("Course", back_populates="standard")
    subjects = relationship("Subject", back_populates="standard")
    student_profiles = relationship("StudentProfile", back_populates="standard")
    syllabus_progress = relationship("SyllabusProgress", back_populates="standard")
