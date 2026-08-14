"""
ProgressTracker — Orchestrator class.

Combines EMA, SM-2, and PriorityQueue to record session scores and retrieve
due chapters in priority order.
"""

from datetime import date
from typing import List, Dict, Tuple, Any

from .ema import compute_ema_mastery
from .sm2 import calculate_sm2
from .priority_queue import PriorityQueue
from .repository import ProgressRepository


class ProgressTracker:
    def __init__(self, repo: ProgressRepository):
        self.repo = repo

    async def record_session_result(
        self,
        student_id: int,
        chapter_id: int,
        score: float,
        today: date | None = None
    ) -> Tuple[float, int, float, int, date]:
        """
        Records the score of a study/quiz session:
        1. Blends the score with previous mastery using EMA (alpha=0.45).
        2. Updates Spaced Repetition (SM-2) intervals and next review date.
        3. Saves the updated state back to the database.
        """
        if today is None:
            today = date.today()

        # Load existing mastery
        mastery_record = await self.repo.get_chapter_mastery(student_id, chapter_id)

        old_mastery = None
        prev_interval = 1
        ease_factor = 2.5
        repetitions = 0

        if mastery_record:
            old_mastery = float(mastery_record.mastery_score)
            prev_interval = mastery_record.interval_days
            ease_factor = float(mastery_record.ease_factor)
            repetitions = mastery_record.repetitions

        # 1. EMA blending
        new_mastery = compute_ema_mastery(score, old_mastery)

        # 2. SM-2 spaced repetition calculation
        interval, new_ef, new_rep, next_review = calculate_sm2(
            accuracy=score,
            previous_interval=prev_interval,
            ease_factor=ease_factor,
            repetitions=repetitions,
            today=today
        )

        # 3. Save to database
        await self.repo.save_chapter_mastery(
            student_id=student_id,
            chapter_id=chapter_id,
            mastery_score=new_mastery,
            ease_factor=new_ef,
            interval_days=interval,
            repetitions=new_rep,
            next_review_date=next_review
        )

        return new_mastery, interval, new_ef, new_rep, next_review

    async def get_due_chapters_queue(self, student_id: int, today: date | None = None) -> PriorityQueue:
        """
        Builds and returns the PriorityQueue (min-heap) of all chapters in the student's standard,
        sorted by next_review_date and negative urgency_score.
        """
        if today is None:
            today = date.today()

        # 1. Load student profile to get standard_id
        student = await self.repo.get_student_profile(student_id)
        if not student:
            raise ValueError(f"Student with id {student_id} not found.")

        # 2. Load all active chapters for standard
        chapters = await self.repo.get_standard_chapters_with_subjects(student.standard_id)

        # 3. Load all chapter masteries
        masteries = {m.chapter_id: m for m in await self.repo.get_all_chapter_masteries(student_id)}

        pq = PriorityQueue()

        for ch in chapters:
            ch_id = ch['chapter_id']
            mastery_rec = masteries.get(ch_id)

            if mastery_rec:
                mastery_score = float(mastery_rec.mastery_score)
                next_review = mastery_rec.next_review_date or today
                
                # Urgency formula:
                # days_overdue = max(0, (today - next_review).days)
                # weakness = 100.0 - mastery_score
                # urgency = (days_overdue + 1) * weakness
                days_overdue = max(0, (today - next_review).days)
                weakness = 100.0 - mastery_score
                urgency_score = (days_overdue + 1.0) * weakness
            else:
                # Unassessed chapter:
                # Treated as due today, mastery = 0.0, weakness = 100.0, urgency = 100.0
                next_review = today
                mastery_score = 0.0
                urgency_score = 100.0

            # Additional metadata for planning
            meta = {
                "chapter_name": ch['chapter_name'],
                "chapter_number": ch['chapter_number'],
                "subject_id": ch['subject_id'],
                "subject_name": ch['subject_name'],
                "mastery_score": mastery_score
            }

            pq.push(
                chapter_id=ch_id,
                next_review_date=next_review,
                urgency_score=urgency_score,
                data=meta
            )

        return pq
