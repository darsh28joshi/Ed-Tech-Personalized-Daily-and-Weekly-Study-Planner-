from sqlalchemy import Column, BigInteger, String, Boolean, TIMESTAMP, text
from sqlalchemy.orm import relationship
from .base import Base

class Board(Base):
    __tablename__ = 'boards'

    board_id = Column(BigInteger, primary_key=True, autoincrement=True)
    board_code = Column(String(20), nullable=False, unique=True)
    board_name = Column(String(150), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text('1'))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    standards = relationship("Standard", back_populates="board")
    student_profiles = relationship("StudentProfile", back_populates="board")
