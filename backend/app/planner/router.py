"""
Planner Router — FastAPI endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from typing import List, Dict

from app.database import get_db
from app.progress.repository import ProgressRepository
from app.progress.tracker import ProgressTracker
from .models import (
    GenerateDailyPlanRequest, DailyPlanResponse, TaskModel,
    PatchTaskRequest, PatchTaskResponse,
    GenerateWeeklyPlanRequest, WeeklyPlanResponse, WeeklyDayPlanModel, WeeklyDayTaskModel
)
from .repository import PlannerRepository
from .knapsack_planner import KnapsackPlanner
from .greedy_planner import GreedyPlanner
from .comparison_harness import PlannerComparisonHarness
from .task_completion import resolve_carry_forward_candidates, sweep_stale_tasks
from .weekly_planner import WeeklyPlanner

router = APIRouter(prefix="/planner", tags=["Planner"])


def get_default_start_time(slot: str) -> str:
    slot_upper = slot.upper() if slot else ""
    if "MORNING" in slot_upper:
        return "08:00"
    elif "AFTERNOON" in slot_upper:
        return "14:00"
    elif "EVENING" in slot_upper:
        return "18:00"
    elif "NIGHT" in slot_upper:
        return "21:00"
    return "09:00"


def format_time_slot(start_time_str: str, duration_minutes: int):
    from datetime import datetime, timedelta
    try:
        dt = datetime.strptime(start_time_str, "%H:%M")
    except ValueError:
        try:
            dt = datetime.strptime(start_time_str, "%I:%M %p")
        except ValueError:
            dt = datetime.strptime("09:00", "%H:%M")
            
    end_dt = dt + timedelta(minutes=duration_minutes)
    return dt.strftime("%I:%M %p"), end_dt.strftime("%I:%M %p"), end_dt.strftime("%H:%M")


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


BREAK_MINUTES = 5  # Mandatory 5-minute break between consecutive study slots


def assign_time_slots(tasks: list, student) -> list:
    """
    Walk through tasks in order and assign start_time / end_time fields.
    Inserts a 5-minute break between every pair of consecutive tasks.
    
    Uses student.preferred_study_start_time if available, otherwise falls
    back to get_default_start_time(student.preferred_study_time).
    """
    from datetime import datetime, timedelta

    start_str = student.preferred_study_start_time
    if not start_str:
        pst = student.preferred_study_time
        pst_val = pst.value if hasattr(pst, 'value') else pst
        start_str = get_default_start_time(pst_val)

    try:
        cursor = datetime.strptime(start_str, "%H:%M")
    except ValueError:
        cursor = datetime.strptime("09:00", "%H:%M")

    for i, task in enumerate(tasks):
        task.start_time = cursor.strftime("%I:%M %p")
        end_cursor = cursor + timedelta(minutes=task.allocated_minutes)
        task.end_time = end_cursor.strftime("%I:%M %p")

        # Add 5-minute break before next task (skip after last task)
        if i < len(tasks) - 1:
            cursor = end_cursor + timedelta(minutes=BREAK_MINUTES)
        else:
            cursor = end_cursor

    return tasks


@router.post("/daily", response_model=DailyPlanResponse)
async def generate_daily_plan(
    request: GenerateDailyPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    planner_repo = PlannerRepository(db)
    progress_repo = ProgressRepository(db)

    # 1. Verify student profile
    student = await planner_repo.get_student_profile(request.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {request.student_id} not found."
        )

    # Fetch diagnostic section times
    section_times = await planner_repo.get_diagnostic_section_times(request.student_id)

    # 2. Check if plan is already generated for this date
    existing_tasks = await planner_repo.get_daily_plan_tasks(request.student_id, request.plan_date)
    if existing_tasks and not request.force_regenerate:
        # Return existing tasks
        tasks = [
            TaskModel(
                task_id=t['task_id'],
                chapter_id=t['chapter_id'],
                chapter_name=t['chapter_name'],
                subject_name=t['subject_name'],
                allocated_minutes=t['allocated_minutes'],
                status=t['status'],
                carried_forward_from_task_id=t['carried_forward_from_task_id'],
                completed_at=t['completed_at']
            )
            for t in existing_tasks
        ]
        # Assign hourly time slots with 5-min breaks
        tasks = assign_time_slots(tasks, student)
        total_time = sum(t.allocated_minutes for t in tasks)
        return DailyPlanResponse(
            student_id=request.student_id,
            plan_date=request.plan_date,
            strategy_used="existing",
            total_allocated_minutes=total_time,
            tasks=tasks
        )

    completed_time = 0
    if existing_tasks and request.force_regenerate:
        completed_today = [t for t in existing_tasks if t['status'] == 'COMPLETED']
        completed_time = sum(t['allocated_minutes'] for t in completed_today)
        await planner_repo.delete_uncompleted_daily_plan_tasks(request.student_id, request.plan_date)

    # 3. End-of-day sweep: mark stale PENDING tasks as SKIPPED
    stale_ids = await planner_repo.get_stale_pending_tasks(request.student_id, request.plan_date)
    for stale_id in stale_ids:
        await planner_repo.patch_task_status(stale_id, 'SKIPPED')

    # 4. Gather yesterday's incomplete tasks (IN_PROGRESS, SKIPPED)
    incomplete_tasks = await planner_repo.get_yesterday_incomplete_tasks(request.student_id, request.plan_date)
    
    # Process carry forward candidates
    carry_forwards, reserved_time = resolve_carry_forward_candidates(incomplete_tasks, request.plan_date)

    # Total budget in minutes
    total_budget = int(float(student.daily_study_hours) * 60)
    remaining_budget = max(0, total_budget - reserved_time - completed_time)

    # 5. Fetch due chapters from ProgressTracker queue
    tracker = ProgressTracker(progress_repo)
    pq = await tracker.get_due_chapters_queue(request.student_id, request.plan_date)
    all_due = pq.get_all_ordered()

    # Filter out candidates that are already included as carry-forwards
    cf_chapter_ids = set(c['chapter_id'] for c in carry_forwards)
    remaining_candidates = []
    
    for item in all_due:
        ch_id, next_review, urgency, meta = item
        if ch_id in cf_chapter_ids:
            continue
        
        # Build candidate item for strategy
        subj_sec = get_subject_section(meta["subject_name"])
        cost = section_times.get(subj_sec, 45)
        remaining_candidates.append({
            "chapter_id": ch_id,
            "cost": cost,
            "value": urgency,
            "metadata": {
                "chapter_name": meta["chapter_name"],
                "subject_name": meta["subject_name"]
            }
        })

    # Subject-diversity interleaving: round-robin across subjects so the
    # knapsack/greedy planner sees candidates from different subjects first,
    # preventing a single subject from dominating the daily plan.
    from collections import deque
    subject_buckets: dict[str, deque] = {}
    for cand in remaining_candidates:
        sub_name = cand["metadata"]["subject_name"]
        subject_buckets.setdefault(sub_name, deque()).append(cand)
    
    interleaved_candidates: list[dict] = []
    bucket_list = list(subject_buckets.values())
    while bucket_list:
        next_round = []
        for bkt in bucket_list:
            interleaved_candidates.append(bkt.popleft())
            if bkt:
                next_round.append(bkt)
        bucket_list = next_round
    remaining_candidates = interleaved_candidates

    # 6. Run selected strategy
    if request.strategy.lower() == 'greedy':
        planner = GreedyPlanner()
    else:
        planner = KnapsackPlanner()

    selected_new = planner.plan_day(remaining_candidates, remaining_budget)

    # Run comparison harness for reporting
    comparison_results = PlannerComparisonHarness.compare_strategies(
        remaining_candidates,
        remaining_budget
    )

    # Merge carry-forwards and newly selected tasks
    merged_tasks_data = []
    
    # 1. Add forced carry forwards
    for cf in carry_forwards:
        merged_tasks_data.append({
            "student_id": request.student_id,
            "plan_date": request.plan_date,
            "chapter_id": cf['chapter_id'],
            "allocated_minutes": cf['cost'],
            "status": "PENDING",
            "carried_forward_from_task_id": cf['carried_forward_from_task_id'],
            # Carry metadata for rendering
            "chapter_name": cf['metadata']['chapter_name'],
            "subject_name": cf['metadata']['subject_name']
        })

    # 2. Add newly selected candidates
    for sel in selected_new:
        merged_tasks_data.append({
            "student_id": request.student_id,
            "plan_date": request.plan_date,
            "chapter_id": sel['chapter_id'],
            "allocated_minutes": sel['cost'],
            "status": "PENDING",
            "carried_forward_from_task_id": None,
            "chapter_name": sel['metadata']['chapter_name'],
            "subject_name": sel['metadata']['subject_name']
        })

    # Save to database
    await planner_repo.save_daily_plan_tasks(merged_tasks_data)

    # Build response (fetching all today's tasks to include completed and newly added tasks)
    all_today_tasks = await planner_repo.get_daily_plan_tasks(request.student_id, request.plan_date)
    
    tasks = [
        TaskModel(
            task_id=t['task_id'],
            chapter_id=t['chapter_id'],
            chapter_name=t['chapter_name'],
            subject_name=t['subject_name'],
            allocated_minutes=t['allocated_minutes'],
            status=t['status'].value if hasattr(t['status'], 'value') else t['status'],
            carried_forward_from_task_id=t['carried_forward_from_task_id'],
            completed_at=t['completed_at']
        )
        for t in all_today_tasks
    ]

    # Assign hourly time slots with 5-min breaks
    tasks = assign_time_slots(tasks, student)
    total_time = sum(t.allocated_minutes for t in tasks)

    return DailyPlanResponse(
        student_id=request.student_id,
        plan_date=request.plan_date,
        strategy_used=request.strategy,
        total_allocated_minutes=total_time,
        tasks=tasks,
        comparison=comparison_results
    )


@router.patch("/daily/task/{task_id}", response_model=PatchTaskResponse)
async def patch_task(
    task_id: int,
    request: PatchTaskRequest,
    db: AsyncSession = Depends(get_db)
):
    planner_repo = PlannerRepository(db)
    progress_repo = ProgressRepository(db)

    # 1. Verify task exists
    task = await planner_repo.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found."
        )

    # 2. Update task status in database
    updated_task = await planner_repo.patch_task_status(task_id, request.status)

    # 3. If COMPLETED, nudge next_review_date by 1 day in chapter_mastery
    if request.status == 'COMPLETED':
        mastery = await progress_repo.get_chapter_mastery(task.student_id, task.chapter_id)
        if mastery:
            next_date = (mastery.next_review_date or date.today()) + timedelta(days=1)
            # Update next review date
            await progress_repo.save_chapter_mastery(
                student_id=task.student_id,
                chapter_id=task.chapter_id,
                mastery_score=float(mastery.mastery_score),
                ease_factor=float(mastery.ease_factor),
                interval_days=mastery.interval_days,
                repetitions=mastery.repetitions,
                next_review_date=next_date
            )

    # 4. Adaptive weekly re-pack is triggered
    # (Since this is a lightweight prototype, we return success; the dashboard will reload
    # and fetch the updated daily and weekly plans from the API).
    return PatchTaskResponse(
        task_id=task_id,
        status=request.status,
        message="Task status updated successfully."
    )


@router.post("/weekly", response_model=WeeklyPlanResponse)
async def generate_weekly_plan(
    request: GenerateWeeklyPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    planner_repo = PlannerRepository(db)
    progress_repo = ProgressRepository(db)

    # 1. Verify student exists
    student = await planner_repo.get_student_profile(request.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {request.student_id} not found."
        )

    # Fetch diagnostic section times
    section_times = await planner_repo.get_diagnostic_section_times(request.student_id)

    # 2. Get due chapters queue from ProgressTracker
    tracker = ProgressTracker(progress_repo)
    pq = await tracker.get_due_chapters_queue(request.student_id)
    all_due = pq.get_all_ordered()

    # 3. Format candidates for the weekly planner
    due_chapters = []
    for item in all_due:
        ch_id, next_review, urgency, meta = item
        subj_sec = get_subject_section(meta["subject_name"])
        cost = section_times.get(subj_sec, 45)
        due_chapters.append({
            "chapter_id": ch_id,
            "cost": cost,
            "subject_id": meta["subject_id"],
            "subject_name": meta["subject_name"],
            "chapter_name": meta["chapter_name"],
            "chapter_number": meta["chapter_number"],
            "display_order": meta.get("display_order", 0),
            "priority": urgency
        })

    # 4. Generate weekly plan using topological sort and First-Fit-Decreasing bin packing
    weekly_plan = WeeklyPlanner.generate_weekly_plan(
        due_chapters=due_chapters,
        daily_study_hours=float(student.daily_study_hours)
    )

    # 5. Format response
    response_days = []
    for day in weekly_plan:
        response_days.append(
            WeeklyDayPlanModel(
                day_number=day["day_number"],
                allocated_minutes=day["allocated_minutes"],
                capacity_minutes=day["capacity_minutes"],
                tasks=[
                    WeeklyDayTaskModel(
                        chapter_id=t["chapter_id"],
                        chapter_name=t["chapter_name"],
                        subject_name=t["subject_name"],
                        cost=t["cost"]
                    )
                    for t in day["tasks"]
                ]
            )
        )

    return WeeklyPlanResponse(
        student_id=request.student_id,
        days=response_days
    )

