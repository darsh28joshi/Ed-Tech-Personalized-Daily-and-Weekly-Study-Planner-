"""
DiagnosticRepository — SQLAlchemy data access.
Translates domain repository requirements into parameterized SQL/SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text as sa_text
from typing import List, Dict
from datetime import datetime
from app.models.diagnostic import DiagnosticSession, SessionStatusEnum, DiagnosticQuestion, DiagnosticResponse, DiagnosticReport
from app.models.aptitude_category_score import AptitudeCategoryScore
from app.models.student_profile import StudentProfile
from app.models.standard import Standard


class DiagnosticRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_student_profile(self, student_id: int) -> StudentProfile | None:
        stmt = select(StudentProfile).where(StudentProfile.student_id == student_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_session(self, student_id: int, entry_point: str, standard_id: int) -> DiagnosticSession:
        ds = DiagnosticSession(
            student_id=student_id,
            entry_point=entry_point,
            standard_id=standard_id,
            status=SessionStatusEnum.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        self.session.add(ds)
        await self.session.commit()
        await self.session.refresh(ds)
        return ds

    async def get_session(self, session_id: int) -> DiagnosticSession | None:
        stmt = select(DiagnosticSession).where(DiagnosticSession.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def has_completed_diagnostic(self, student_id: int) -> bool:
        stmt = select(DiagnosticSession.session_id).where(
            DiagnosticSession.student_id == student_id,
            DiagnosticSession.status == SessionStatusEnum.COMPLETED
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def get_subjects_by_standard(self, standard_numbers: List[int]) -> Dict[int, List[dict]]:
        """
        Retrieves subjects grouped by standard number (e.g. 5, 6, 7).
        """
        stmt = sa_text("""
            SELECT sub.subject_id, sub.subject_name, s.standard_number
            FROM subjects sub
            JOIN standards s ON sub.standard_id = s.standard_id
            WHERE s.standard_number IN :std_nums AND sub.is_active = 1
        """)
        result = await self.session.execute(stmt, {"std_nums": tuple(standard_numbers)})
        rows = result.fetchall()

        by_std = {n: [] for n in standard_numbers}
        for r in rows:
            by_std[r.standard_number].append({
                "subject_id": r.subject_id,
                "subject_name": r.subject_name
            })
        return by_std

    async def get_academic_questions_pool(self, standard_numbers: List[int]) -> List[dict]:
        """
        Retrieves all academic questions for the given standard numbers.
        """
        stmt = sa_text("""
            SELECT aq.question_id, aq.subject_id, sub.subject_name, aq.difficulty, aq.estimated_seconds,
                   c.chapter_id, c.chapter_number, s.standard_number
            FROM academic_questions aq
            JOIN chapters c ON aq.chapter_id = c.chapter_id
            JOIN subjects sub ON c.subject_id = sub.subject_id
            JOIN standards s ON sub.standard_id = s.standard_id
            WHERE s.standard_number IN :std_nums AND c.is_active = 1 AND sub.is_active = 1
        """)
        result = await self.session.execute(stmt, {"std_nums": tuple(standard_numbers)})
        rows = result.fetchall()

        return [
            {
                "question_id": r.question_id,
                "subject_id": r.subject_id,
                "subject_name": r.subject_name,
                "difficulty": r.difficulty.value if hasattr(r.difficulty, 'value') else r.difficulty,
                "estimated_seconds": r.estimated_seconds,
                "chapter_id": r.chapter_id,
                "chapter_number": r.chapter_number,
                "standard_number": r.standard_number
            }
            for r in rows
        ]

    async def get_aptitude_questions_pool(self) -> List[dict]:
        """
        Retrieves all aptitude questions.
        """
        stmt = sa_text("""
            SELECT aptitude_question_id, category, difficulty, estimated_time_seconds
            FROM aptitude_questions
        """)
        result = await self.session.execute(stmt)
        rows = result.fetchall()

        return [
            {
                "question_id": r.aptitude_question_id,
                "category": r.category,
                "difficulty": r.difficulty.value if hasattr(r.difficulty, 'value') else r.difficulty,
                "estimated_seconds": r.estimated_time_seconds
            }
            for r in rows
        ]

    async def get_syllabus_progress(self, standard_id: int) -> Dict[int, int]:
        """
        Retrieves syllabus pacing mapping (subject_id -> last_taught_chapter_number).
        """
        stmt = sa_text("""
            SELECT subject_id, last_taught_chapter_number
            FROM syllabus_progress
            WHERE standard_id = :standard_id
        """)
        result = await self.session.execute(stmt, {"standard_id": standard_id})
        rows = result.fetchall()
        return {r.subject_id: r.last_taught_chapter_number for r in rows}

    async def get_academic_question_details(self, question_ids: List[int]) -> List[dict]:
        """
        Fetches detailed info for academic questions (including option text for testing).
        """
        if not question_ids:
            return []
        stmt = sa_text("""
            SELECT aq.question_id, aq.question_text, aq.option_a, aq.option_b, aq.option_c, aq.option_d, sub.subject_name
            FROM academic_questions aq
            JOIN chapters c ON aq.chapter_id = c.chapter_id
            JOIN subjects sub ON c.subject_id = sub.subject_id
            WHERE aq.question_id IN :qids
        """)
        result = await self.session.execute(stmt, {"qids": tuple(question_ids)})
        rows = result.fetchall()
        return [dict(r._mapping) for r in rows]

    async def get_aptitude_question_details(self, question_ids: List[int]) -> List[dict]:
        """
        Fetches detailed info for aptitude questions.
        """
        if not question_ids:
            return []
        stmt = sa_text("""
            SELECT aptitude_question_id as question_id, question_text, option_a, option_b, option_c, option_d
            FROM aptitude_questions
            WHERE aptitude_question_id IN :qids
        """)
        result = await self.session.execute(stmt, {"qids": tuple(question_ids)})
        rows = result.fetchall()
        return [dict(r._mapping) for r in rows]

    async def save_diagnostic_questions(self, session_id: int, questions_data: List[dict]):
        # Clear existing ones to prevent duplicates on restart/resume
        await self.session.execute(
            sa_text("DELETE FROM diagnostic_questions WHERE session_id = :sid"),
            {"sid": session_id}
        )
        for q in questions_data:
            dq = DiagnosticQuestion(
                session_id=session_id,
                question_source=q['source'],
                question_id=q['question_id'],
                section=q['section'],
                question_order=q['order']
            )
            self.session.add(dq)
        await self.session.commit()

    async def get_session_questions(self, session_id: int) -> List[DiagnosticQuestion]:
        stmt = select(DiagnosticQuestion).where(DiagnosticQuestion.session_id == session_id).order_by(DiagnosticQuestion.question_order)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_academic_questions_by_ids(self, question_ids: List[int]) -> List[dict]:
        if not question_ids:
            return []
        stmt = sa_text("""
            SELECT question_id, chapter_id, difficulty, estimated_seconds, correct_option
            FROM academic_questions
            WHERE question_id IN :qids
        """)
        result = await self.session.execute(stmt, {"qids": tuple(question_ids)})
        rows = result.fetchall()
        return [
            {
                "question_id": r.question_id,
                "chapter_id": r.chapter_id,
                "difficulty": r.difficulty.value if hasattr(r.difficulty, 'value') else r.difficulty,
                "estimated_seconds": r.estimated_seconds,
                "correct_option": r.correct_option
            }
            for r in rows
        ]

    async def get_aptitude_questions_by_ids(self, question_ids: List[int]) -> List[dict]:
        if not question_ids:
            return []
        stmt = sa_text("""
            SELECT aptitude_question_id as question_id, category, difficulty, estimated_time_seconds, correct_option
            FROM aptitude_questions
            WHERE aptitude_question_id IN :qids
        """)
        result = await self.session.execute(stmt, {"qids": tuple(question_ids)})
        rows = result.fetchall()
        return [
            {
                "question_id": r.question_id,
                "category": r.category,
                "difficulty": r.difficulty.value if hasattr(r.difficulty, 'value') else r.difficulty,
                "estimated_seconds": r.estimated_time_seconds,
                "correct_option": r.correct_option
            }
            for r in rows
        ]

    async def save_diagnostic_responses(self, session_id: int, responses_data: List[dict]):
        await self.session.execute(
            sa_text("DELETE FROM diagnostic_responses WHERE session_id = :sid"),
            {"sid": session_id}
        )
        for r in responses_data:
            dr = DiagnosticResponse(
                session_id=session_id,
                question_source=r['source'],
                question_id=r['question_id'],
                chapter_id=r.get('chapter_id'),
                selected_option=r['selected_option'],
                is_correct=r['is_correct'],
                time_taken_seconds=r['time_taken_seconds']
            )
            self.session.add(dr)
        await self.session.commit()

    async def save_diagnostic_report(self, session_id: int, report_data: dict):
        # Delete existing report if any
        await self.session.execute(
            sa_text("DELETE FROM diagnostic_reports WHERE session_id = :sid"),
            {"sid": session_id}
        )
        dr = DiagnosticReport(
            session_id=session_id,
            aptitude_score=round(report_data['aptitude_score'], 2),
            aptitude_percentile=round(report_data['aptitude_percentile'], 2),
            academic_accuracy=round(report_data['academic_accuracy'], 2),
            study_health_score=round(report_data['study_health_score'], 2),
            weakest_chapter_ids=report_data.get('weakest_chapter_ids', []),
            generated_at=datetime.utcnow()
        )
        self.session.add(dr)
        await self.session.commit()

    async def save_aptitude_category_scores(self, session_id: int, scores_data: Dict[str, dict]):
        await self.session.execute(
            sa_text("DELETE FROM aptitude_category_scores WHERE session_id = :sid"),
            {"sid": session_id}
        )
        for cat, data in scores_data.items():
            acs = AptitudeCategoryScore(
                session_id=session_id,
                category=cat,
                accuracy=round(data['accuracy'], 2),
                percentile=round(data['percentile'], 2)
            )
            self.session.add(acs)
        await self.session.commit()

    async def get_aptitude_category_scores(self, session_id: int) -> List[AptitudeCategoryScore]:
        stmt = select(AptitudeCategoryScore).where(AptitudeCategoryScore.session_id == session_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_diagnostic_report(self, session_id: int) -> DiagnosticReport | None:
        stmt = select(DiagnosticReport).where(DiagnosticReport.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_chapters_by_ids(self, chapter_ids: List[int]) -> List[dict]:
        if not chapter_ids:
            return []
        stmt = sa_text("""
            SELECT chapter_id, chapter_name, subject_id
            FROM chapters
            WHERE chapter_id IN :cids
        """)
        result = await self.session.execute(stmt, {"cids": tuple(chapter_ids)})
        rows = result.fetchall()
        return [dict(r._mapping) for r in rows]

    async def mark_session_completed(self, session_id: int):
        stmt = update(DiagnosticSession).where(
            DiagnosticSession.session_id == session_id
        ).values(
            status=SessionStatusEnum.COMPLETED,
            completed_at=datetime.utcnow()
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def upsert_chapter_mastery(self, student_id: int, chapter_id: int, score: float):
        """
        Upserts chapter mastery for a student.
        Uses 90+ -> HIGH, 50-90 -> MEDIUM, <50 -> LOW.
        """
        rounded_score = round(score, 2)
        confidence = "MEDIUM"
        if rounded_score >= 90.0:
            confidence = "HIGH"
        elif rounded_score < 50.0:
            confidence = "LOW"

        stmt = sa_text("""
            INSERT INTO chapter_mastery (student_id, chapter_id, mastery_score, confidence, last_assessed)
            VALUES (:student_id, :chapter_id, :score, :confidence, NOW())
            ON DUPLICATE KEY UPDATE
                mastery_score = VALUES(mastery_score),
                confidence = VALUES(confidence),
                last_assessed = NOW()
        """)
        await self.session.execute(stmt, {
            "student_id": student_id,
            "chapter_id": chapter_id,
            "score": rounded_score,
            "confidence": confidence
        })
        await self.session.commit()
