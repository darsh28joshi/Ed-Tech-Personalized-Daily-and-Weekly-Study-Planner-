"""
Progress Router — FastAPI endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List

from app.database import get_db
from .models import RecordSessionResultRequest, RecordSessionResultResponse, DueChaptersResponse, DueChapterModel
from .repository import ProgressRepository
from .tracker import ProgressTracker

router = APIRouter(prefix="/progress", tags=["Progress Tracking"])


@router.post("/session", response_model=RecordSessionResultResponse)
async def record_session_result(
    request: RecordSessionResultRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = ProgressRepository(db)
    
    # Verify student exists
    student = await repo.get_student_profile(request.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {request.student_id} not found."
        )

    tracker = ProgressTracker(repo)
    new_mastery, interval, new_ef, new_rep, next_review = await tracker.record_session_result(
        student_id=request.student_id,
        chapter_id=request.chapter_id,
        score=request.score
    )

    return RecordSessionResultResponse(
        success=True,
        new_mastery=new_mastery,
        interval_days=interval,
        ease_factor=new_ef,
        repetitions=new_rep,
        next_review_date=next_review
    )


@router.get("/due-chapters", response_model=DueChaptersResponse)
async def get_due_chapters(
    student_id: int,
    db: AsyncSession = Depends(get_db)
):
    repo = ProgressRepository(db)
    
    # Verify student exists
    student = await repo.get_student_profile(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found."
        )

    tracker = ProgressTracker(repo)
    pq = await tracker.get_due_chapters_queue(student_id)
    
    ordered_list = pq.get_all_ordered()
    due_chapters = []
    for item in ordered_list:
        ch_id, next_review, urgency, meta = item
        due_chapters.append(
            DueChapterModel(
                chapter_id=ch_id,
                chapter_name=meta["chapter_name"],
                subject_name=meta["subject_name"],
                next_review_date=next_review,
                urgency_score=urgency
            )
        )

    return DueChaptersResponse(
        student_id=student_id,
        due_chapters=due_chapters
    )
