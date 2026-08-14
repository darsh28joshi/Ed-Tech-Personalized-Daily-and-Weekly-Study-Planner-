from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey, Boolean, TIMESTAMP, text
from sqlalchemy.orm import relationship
from .base import Base


class Chapter(Base):
    __tablename__ = 'chapters'

    chapter_id = Column(BigInteger, primary_key=True, autoincrement=True)
    subject_id = Column(BigInteger, ForeignKey('subjects.subject_id', ondelete='CASCADE'), nullable=False)
    section_id = Column(BigInteger, ForeignKey('sections.section_id', ondelete='SET NULL'), nullable=True)
    chapter_code = Column(String(100), nullable=False, unique=True)
    chapter_number = Column(Integer, nullable=False)
    chapter_name = Column(String(500), nullable=False)
    display_order = Column(Integer, nullable=True, server_default=text('0'))
    is_active = Column(Boolean, nullable=True, server_default=text('1'))
    created_at = Column(TIMESTAMP, nullable=True, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=True, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    subject = relationship("Subject", back_populates="chapters")
    section = relationship("Section", back_populates="chapters")
    academic_questions = relationship("AcademicQuestion", back_populates="chapter")
    chapter_mastery = relationship("ChapterMastery", back_populates="chapter")
    daily_plan_tasks = relationship("DailyPlanTask", back_populates="chapter")
