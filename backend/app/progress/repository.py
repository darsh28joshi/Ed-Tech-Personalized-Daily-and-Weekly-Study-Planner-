"""
ProgressRepository — SQLAlchemy implementation.
Exposes queries for retrieving and saving chapter mastery and SM-2 data.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text as sa_text
from typing import List, Dict, Tuple
from datetime import date, datetime

from app.models.chapter_mastery import ChapterMastery, ConfidenceEnum
from app.models.student_profile import StudentProfile


class ProgressRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_student_profile(self, student_id: int) -> StudentProfile | None:
        stmt = select(StudentProfile).where(StudentProfile.student_id == student_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_chapter_mastery(self, student_id: int, chapter_id: int) -> ChapterMastery | None:
        stmt = select(ChapterMastery).where(
            ChapterMastery.student_id == student_id,
            ChapterMastery.chapter_id == chapter_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all_chapter_masteries(self, student_id: int) -> List[ChapterMastery]:
        stmt = select(ChapterMastery).where(ChapterMastery.student_id == student_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_standard_chapters_with_subjects(self, standard_id: int) -> List[dict]:
        """
        Fetches all active chapters in the standard, along with their subject name.
        """
        stmt = sa_text("""
            SELECT c.chapter_id, c.chapter_name, c.chapter_number, sub.subject_id, sub.subject_name
            FROM chapters c
            JOIN subjects sub ON c.subject_id = sub.subject_id
            WHERE sub.standard_id = :std_id AND c.is_active = 1 AND sub.is_active = 1
        """)
        result = await self.session.execute(stmt, {"std_id": standard_id})
        rows = result.fetchall()
        return [dict(r._mapping) for r in rows]

    async def save_chapter_mastery(
        self,
        student_id: int,
        chapter_id: int,
        mastery_score: float,
        ease_factor: float,
        interval_days: int,
        repetitions: int,
        next_review_date: date
    ) -> ChapterMastery:
        """
        Saves or updates the chapter mastery record using MySQL INSERT ... ON DUPLICATE KEY UPDATE.
        Also resolves confidence: >=90 -> HIGH, >=50 -> MEDIUM, else LOW.
        """
        rounded_mastery = round(mastery_score, 2)
        rounded_ease = round(ease_factor, 2)
        confidence = "MEDIUM"
        if rounded_mastery >= 90.0:
            confidence = "HIGH"
        elif rounded_mastery < 50.0:
            confidence = "LOW"

        stmt = sa_text("""
            INSERT INTO chapter_mastery (
                student_id, chapter_id, mastery_score, confidence,
                ease_factor, interval_days, repetitions, next_review_date, last_assessed
            )
            VALUES (
                :student_id, :chapter_id, :mastery_score, :confidence,
                :ease_factor, :interval_days, :repetitions, :next_review_date, NOW()
            )
            ON DUPLICATE KEY UPDATE
                mastery_score = VALUES(mastery_score),
                confidence = VALUES(confidence),
                ease_factor = VALUES(ease_factor),
                interval_days = VALUES(interval_days),
                repetitions = VALUES(repetitions),
                next_review_date = VALUES(next_review_date),
                last_assessed = NOW()
        """)
        await self.session.execute(stmt, {
            "student_id": student_id,
            "chapter_id": chapter_id,
            "mastery_score": rounded_mastery,
            "confidence": confidence,
            "ease_factor": rounded_ease,
            "interval_days": interval_days,
            "repetitions": repetitions,
            "next_review_date": next_review_date
        })
        await self.session.commit()

        # Query and return the updated object
        res = await self.get_chapter_mastery(student_id, chapter_id)
        assert res is not None
        return res
