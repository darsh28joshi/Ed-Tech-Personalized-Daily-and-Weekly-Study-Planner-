from sqlalchemy import Column, BigInteger, SmallInteger, String, ForeignKey, Boolean, TIMESTAMP, text, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


class Subject(Base):
    __tablename__ = 'subjects'

    subject_id = Column(BigInteger, primary_key=True, autoincrement=True)
    # DB schema uses standard_id, not course_id
    standard_id = Column(BigInteger, ForeignKey('standards.standard_id', ondelete='RESTRICT'), nullable=False)
    subject_code = Column(String(50), nullable=False, unique=True)
    subject_name = Column(String(200), nullable=False)
    display_order = Column(SmallInteger, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text('1'))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    __table_args__ = (
        UniqueConstraint('standard_id', 'subject_name', name='uq_standard_subject_name'),
    )

    standard = relationship("Standard", back_populates="subjects")
    sections = relationship("Section", back_populates="subject")
    chapters = relationship("Chapter", back_populates="subject")
    academic_questions = relationship("AcademicQuestion", back_populates="subject")
    syllabus_progress = relationship("SyllabusProgress", back_populates="subject")
