"""
Onboarding repository — SQLAlchemy data access.
Business logic never talks to SQLAlchemy directly — only this layer does.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text as sa_text
from datetime import date
from typing import List

from app.models.student_profile import StudentProfile
from app.models.course import Course
from app.models.subject import Subject
from app.models.chapter import Chapter
from app.models.syllabus_progress import SyllabusProgress


class OnboardingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_course(self, board_id: int, standard_id: int) -> Course | None:
        """Find the course for a given board + standard combination."""
        stmt = select(Course).where(
            Course.board_id == board_id,
            Course.standard_id == standard_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_student(
        self,
        board_id: int,
        standard_id: int,
        first_name: str,
        last_name: str,
        username: str,
        password: str,
        medium: str,
        study_goal: str,
        daily_study_hours: float,
        preferred_study_time: str,
        revision_preference: str,
        academic_year_start_date: date,
        academic_year_end_date: date,
        date_of_birth: date | None = None,
        school_name: str | None = None,
        preferred_study_start_time: str | None = None,
        preferred_study_end_time: str | None = None,
    ) -> StudentProfile:
        student = StudentProfile(
            board_id=board_id,
            standard_id=standard_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            medium=medium,
            study_goal=study_goal,
            daily_study_hours=daily_study_hours,
            preferred_study_time=preferred_study_time,
            revision_preference=revision_preference,
            academic_year_start_date=academic_year_start_date,
            academic_year_end_date=academic_year_end_date,
            date_of_birth=date_of_birth,
            school_name=school_name,
            preferred_study_start_time=preferred_study_start_time,
            preferred_study_end_time=preferred_study_end_time,
        )
        self.session.add(student)
        await self.session.commit()
        await self.session.refresh(student)
        return student

    async def get_subjects_for_standard(self, standard_id: int) -> List[Subject]:
        """Get all active subjects for a standard (used for syllabus pacing seeding)."""
        stmt = select(Subject).where(
            Subject.standard_id == standard_id,
            Subject.is_active == True,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_chapter_count_for_subject(self, subject_id: int) -> int:
        """Count active chapters for a subject."""
        stmt = select(Chapter.chapter_id).where(
            Chapter.subject_id == subject_id,
            Chapter.is_active == True,
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())

    async def upsert_syllabus_progress(
        self,
        standard_id: int,
        subject_id: int,
        last_taught_chapter_number: int,
        as_of_date: date,
    ):
        """
        Insert or update syllabus_progress for a (standard_id, subject_id) pair.
        Uses MySQL INSERT ... ON DUPLICATE KEY UPDATE for idempotency.
        """
        stmt = sa_text("""
            INSERT INTO syllabus_progress (standard_id, subject_id, last_taught_chapter_number, as_of_date)
            VALUES (:standard_id, :subject_id, :last_taught, :as_of)
            ON DUPLICATE KEY UPDATE
                last_taught_chapter_number = VALUES(last_taught_chapter_number),
                as_of_date = VALUES(as_of_date)
        """)
        await self.session.execute(stmt, {
            "standard_id": standard_id,
            "subject_id": subject_id,
            "last_taught": last_taught_chapter_number,
            "as_of": as_of_date,
        })
        await self.session.commit()

    async def get_student_by_username(self, username: str) -> StudentProfile | None:
        """Look up a student profile by username."""
        stmt = select(StudentProfile).where(StudentProfile.username == username)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_student_by_id(self, student_id: int) -> StudentProfile | None:
        """Look up a student profile by student ID."""
        stmt = select(StudentProfile).where(StudentProfile.student_id == student_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_student(self, student_id: int, update_data: dict) -> StudentProfile | None:
        """Update student profile details in DB."""
        student = await self.get_student_by_id(student_id)
        if not student:
            return None
        for key, val in update_data.items():
            setattr(student, key, val)
        await self.session.commit()
        await self.session.refresh(student)
        return student

    async def get_completed_diagnostic_session(self, student_id: int) -> int | None:
        """Find the completed diagnostic session ID for a student if it exists."""
        from app.models.diagnostic import DiagnosticSession
        stmt = select(DiagnosticSession.session_id).where(
            DiagnosticSession.student_id == student_id,
            DiagnosticSession.status == 'COMPLETED'
        ).order_by(DiagnosticSession.session_id.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()
