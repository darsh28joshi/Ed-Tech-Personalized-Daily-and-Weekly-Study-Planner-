from sqlalchemy import Column, BigInteger, String, ForeignKey, Boolean, Integer, TIMESTAMP, text
from sqlalchemy.orm import relationship
from .base import Base


class Section(Base):
    __tablename__ = 'sections'

    section_id = Column(BigInteger, primary_key=True, autoincrement=True)
    subject_id = Column(BigInteger, ForeignKey('subjects.subject_id', ondelete='CASCADE'), nullable=False)
    section_code = Column(String(100), nullable=False, unique=True)
    section_name = Column(String(255), nullable=False)
    display_order = Column(Integer, server_default=text('0'))
    created_at = Column(TIMESTAMP, nullable=True, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=True, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    subject = relationship("Subject", back_populates="sections")
    chapters = relationship("Chapter", back_populates="section")
