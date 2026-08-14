"""
Progress Tracking Pydantic Models.
"""

from pydantic import BaseModel, Field
from datetime import date
from typing import List


class RecordSessionResultRequest(BaseModel):
    student_id: int
    chapter_id: int
    score: float = Field(..., ge=0.0, le=100.0, description="Score percentage achieved in session/quiz")


class RecordSessionResultResponse(BaseModel):
    success: bool
    new_mastery: float
    interval_days: int
    ease_factor: float
    repetitions: int
    next_review_date: date


class DueChapterModel(BaseModel):
    chapter_id: int
    chapter_name: str
    subject_name: str
    next_review_date: date
    urgency_score: float


class DueChaptersResponse(BaseModel):
    student_id: int
    due_chapters: List[DueChapterModel]
