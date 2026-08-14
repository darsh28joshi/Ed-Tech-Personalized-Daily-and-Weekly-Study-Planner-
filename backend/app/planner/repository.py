"""
PlannerRepository — SQLAlchemy implementation.
Exposes database reads and writes for daily plan tasks.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text as sa_text
from typing import List, Dict, Tuple, Optional
from datetime import date, datetime

from app.models.daily_plan_task import DailyPlanTask
from app.models.student_profile import StudentProfile
from app.models.chapter import Chapter
from app.models.subject import Subject


class PlannerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_student_profile(self, student_id: int) -> StudentProfile | None:
        stmt = select(StudentProfile).where(StudentProfile.student_id == student_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_diagnostic_section_times(self, student_id: int) -> Dict[str, int]:
        """
        Calculates the study slot duration (in minutes) for each section based on the latest completed diagnostic session.
        Formula: max(30, min(90, total_time_taken_seconds // 6))
        Returns a dict of {section_name_lower: duration_minutes}
        """
        stmt = sa_text("""
            SELECT session_id FROM diagnostic_sessions
            WHERE student_id = :sid AND status = 'COMPLETED'
            ORDER BY completed_at DESC LIMIT 1
        """)
        res = await self.session.execute(stmt, {"sid": student_id})
        row = res.fetchone()
        if not row:
            return {}

        session_id = row[0]
        
        stmt_times = sa_text("""
            SELECT dr.question_source, dr.time_taken_seconds, sub.subject_name
            FROM diagnostic_responses dr
            LEFT JOIN academic_questions aq ON dr.question_id = aq.question_id AND dr.question_source = 'ACADEMIC'
            LEFT JOIN chapters c ON aq.chapter_id = c.chapter_id
            LEFT JOIN subjects sub ON c.subject_id = sub.subject_id
            WHERE dr.session_id = :sid
        """)
        res_times = await self.session.execute(stmt_times, {"sid": session_id})
        rows_times = res_times.fetchall()
        
        def get_subject_section(subj_name: str) -> str:
            name_lower = subj_name.lower()
            if "math" in name_lower:
                return "mathematics"
            elif "science" in name_lower or "environmental studies part 1" in name_lower:
                return "science"
            elif "history" in name_lower or "civics" in name_lower or "environmental studies part 2" in name_lower:
                return "history and civics"
            elif "geography" in name_lower:
                return "geography"
            elif "hindi" in name_lower:
                return "hindi"
            elif "marathi" in name_lower:
                return "marathi"
            return "other"
            
        section_raw_times = {}
        for r in rows_times:
            q_src = r.question_source.value if hasattr(r.question_source, 'value') else r.question_source
            if q_src == 'APTITUDE':
                sec_name = "aptitude section"
            else:
                sec_name = get_subject_section(r.subject_name or "")
            
            section_raw_times[sec_name] = section_raw_times.get(sec_name, 0) + (r.time_taken_seconds or 0)
            
        section_times = {}
        for sec, total_seconds in section_raw_times.items():
            duration = max(30, min(90, int(total_seconds // 6)))
            section_times[sec] = duration
            
        return section_times

    async def get_daily_plan_tasks(self, student_id: int, plan_date: date) -> List[dict]:
        """
        Retrieves all daily plan tasks for a student on a specific date, including names.
        """
        stmt = sa_text("""
            SELECT t.task_id, t.student_id, t.plan_date, t.chapter_id, t.allocated_minutes,
                   t.status, t.carried_forward_from_task_id, t.completed_at,
                   c.chapter_name, sub.subject_name
            FROM daily_plan_tasks t
            JOIN chapters c ON t.chapter_id = c.chapter_id
            JOIN subjects sub ON c.subject_id = sub.subject_id
            WHERE t.student_id = :sid AND t.plan_date = :pdate
            ORDER BY t.task_id ASC
        """)
        result = await self.session.execute(stmt, {"sid": student_id, "pdate": plan_date})
        rows = result.fetchall()
        return [dict(r._mapping) for r in rows]

    async def get_task(self, task_id: int) -> DailyPlanTask | None:
        stmt = select(DailyPlanTask).where(DailyPlanTask.task_id == task_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def patch_task_status(self, task_id: int, status: str) -> DailyPlanTask:
        completed_at = datetime.utcnow() if status == 'COMPLETED' else None
        stmt = (
            update(DailyPlanTask)
            .where(DailyPlanTask.task_id == task_id)
            .values(status=status, completed_at=completed_at)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        
        updated = await self.get_task(task_id)
        assert updated is not None
        return updated

    async def get_yesterday_incomplete_tasks(self, student_id: int, plan_date: date) -> List[dict]:
        """
        Finds all incomplete tasks (IN_PROGRESS, SKIPPED) before plan_date.
        """
        stmt = sa_text("""
            SELECT t.task_id, t.chapter_id, t.allocated_minutes, t.status,
                   c.chapter_name, sub.subject_name
            FROM daily_plan_tasks t
            JOIN chapters c ON t.chapter_id = c.chapter_id
            JOIN subjects sub ON c.subject_id = sub.subject_id
            WHERE t.student_id = :sid AND t.plan_date < :pdate AND t.status IN ('IN_PROGRESS', 'SKIPPED')
        """)
        result = await self.session.execute(stmt, {"sid": student_id, "pdate": plan_date})
        rows = result.fetchall()
        return [dict(r._mapping) for r in rows]

    async def get_stale_pending_tasks(self, student_id: int, plan_date: date) -> List[int]:
        """
        Finds all tasks before plan_date that are still PENDING.
        """
        stmt = sa_text("""
            SELECT task_id
            FROM daily_plan_tasks
            WHERE student_id = :sid AND plan_date < :pdate AND status = 'PENDING'
        """)
        result = await self.session.execute(stmt, {"sid": student_id, "pdate": plan_date})
        return [r.task_id for r in result.fetchall()]

    async def save_daily_plan_tasks(self, tasks_data: List[dict]) -> List[DailyPlanTask]:
        """
        Bulk inserts daily plan tasks.
        """
        inserted_tasks = []
        for t in tasks_data:
            task = DailyPlanTask(
                student_id=t['student_id'],
                plan_date=t['plan_date'],
                chapter_id=t['chapter_id'],
                allocated_minutes=t['allocated_minutes'],
                status=t.get('status', 'PENDING'),
                carried_forward_from_task_id=t.get('carried_forward_from_task_id')
            )
            self.session.add(task)
            inserted_tasks.append(task)
        await self.session.commit()
        for task in inserted_tasks:
            await self.session.refresh(task)
        return inserted_tasks

    async def delete_uncompleted_daily_plan_tasks(self, student_id: int, plan_date: date):
        """Deletes uncompleted daily plan tasks (PENDING, IN_PROGRESS, SKIPPED) for a given date."""
        stmt = sa_text("""
            DELETE FROM daily_plan_tasks
            WHERE student_id = :sid AND plan_date = :pdate AND status != 'COMPLETED'
        """)
        await self.session.execute(stmt, {"sid": student_id, "pdate": plan_date})
        await self.session.commit()
