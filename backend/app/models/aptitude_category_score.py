from sqlalchemy import Column, BigInteger, String, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.orm import relationship
from .base import Base

class AptitudeCategoryScore(Base):
    __tablename__ = 'aptitude_category_scores'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey('diagnostic_sessions.session_id', ondelete='CASCADE'), nullable=False)
    category = Column(String(100), nullable=False)
    accuracy = Column(Numeric(5, 2), nullable=False)
    percentile = Column(Numeric(5, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint('session_id', 'category', name='uix_session_category'),
    )

    session = relationship("DiagnosticSession", back_populates="aptitude_category_scores")
