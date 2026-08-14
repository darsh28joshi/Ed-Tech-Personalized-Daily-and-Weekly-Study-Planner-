"""
Onboarding router — the HTTP boundary.

POST /onboarding/student
1. Resolves entry point from academic year dates.
2. Creates the student profile.
3. Seeds syllabus_progress rows for the student's standard.
4. Returns the student_id and entry_point.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime, timedelta

from app.database import get_db
from .models import OnboardingRequest, OnboardingResponse, LoginRequest, LoginResponse, StudentProfileDetailResponse, UpdateProfileRequest
from .repository import OnboardingRepository
from .entry_point_resolver import resolve_entry_point
from .syllabus_pacing_seeder import calculate_last_taught_chapter, compute_percent_elapsed

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


def _get_default_start_time(slot: str) -> str:
    """Map preferred_study_time enum to a sensible default HH:MM start."""
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


def _compute_study_end_time(start_time_str: str, daily_hours: float) -> str:
    """Auto-calculate end time as start_time + daily_study_hours."""
    dt = datetime.strptime(start_time_str, "%H:%M")
    end_dt = dt + timedelta(hours=daily_hours)
    return end_dt.strftime("%H:%M")


@router.post("/student", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
async def onboard_student(
    request: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = OnboardingRepository(db)
    today = date.today()

    # 1. Resolve entry point
    entry_point = resolve_entry_point(
        start_date=request.academic_year_start_date,
        end_date=request.academic_year_end_date,
        today=today,
    )

    # 2. Find the course
    course = await repo.get_course(request.board_id, request.standard_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No course found for board_id={request.board_id}, standard_id={request.standard_id}",
        )

    # 3. Auto-compute preferred_study_end_time from start_time + daily_study_hours
    start_time = request.preferred_study_start_time
    if not start_time:
        start_time = _get_default_start_time(request.preferred_study_time)
    computed_end_time = _compute_study_end_time(start_time, request.daily_study_hours)

    # 4. Create student profile
    student = await repo.create_student(
        board_id=request.board_id,
        standard_id=request.standard_id,
        first_name=request.first_name,
        last_name=request.last_name,
        username=request.username,
        password=request.password,
        medium=request.medium,
        study_goal=request.study_goal,
        daily_study_hours=request.daily_study_hours,
        preferred_study_time=request.preferred_study_time,
        revision_preference=request.revision_preference,
        academic_year_start_date=request.academic_year_start_date,
        academic_year_end_date=request.academic_year_end_date,
        date_of_birth=request.date_of_birth,
        school_name=request.school_name,
        preferred_study_start_time=start_time,
        preferred_study_end_time=computed_end_time,
    )

    # 4. Seed syllabus progress — populate last_taught_chapter_number
    #    for each subject in the student's standard, based on % elapsed
    percent_elapsed = compute_percent_elapsed(
        start_date=request.academic_year_start_date,
        end_date=request.academic_year_end_date,
        today=today,
    )
    subjects = await repo.get_subjects_for_standard(request.standard_id)
    for subject in subjects:
        total_chapters = await repo.get_chapter_count_for_subject(subject.subject_id)
        last_taught = calculate_last_taught_chapter(percent_elapsed, total_chapters)
        await repo.upsert_syllabus_progress(
            standard_id=request.standard_id,
            subject_id=subject.subject_id,
            last_taught_chapter_number=last_taught,
            as_of_date=today,
        )

    return OnboardingResponse(
        student_id=student.student_id,
        entry_point=entry_point.value,
    )


@router.post("/login", response_model=LoginResponse)
async def login_student(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    import logging
    logger = logging.getLogger(__name__)
    
    repo = OnboardingRepository(db)
    student = await repo.get_student_by_username(request.username)
    if not student or student.password != request.password:
        logger.warning(f"Login failed: Invalid credentials for username '{request.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    # Resolve entry point dynamically from their academic dates
    entry_point = resolve_entry_point(
        start_date=student.academic_year_start_date,
        end_date=student.academic_year_end_date,
        today=date.today()
    )

    # Check if they have completed their diagnostic assessment
    completed_session_id = await repo.get_completed_diagnostic_session(student.student_id)
    
    logger.info(f"Student login success: id={student.student_id}, completed_session={completed_session_id}")

    if completed_session_id is not None:
        return LoginResponse(
            student_id=student.student_id,
            entry_point=entry_point.value,
            diagnostic_completed=True,
            session_id=completed_session_id
        )

    return LoginResponse(
        student_id=student.student_id,
        entry_point=entry_point.value,
        diagnostic_completed=False,
        session_id=None
    )


@router.get("/student/{student_id}", response_model=StudentProfileDetailResponse)
async def get_student_profile(
    student_id: int,
    db: AsyncSession = Depends(get_db)
):
    repo = OnboardingRepository(db)
    student = await repo.get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found."
        )
    return StudentProfileDetailResponse(
        student_id=student.student_id,
        board_id=student.board_id,
        standard_id=student.standard_id,
        first_name=student.first_name,
        last_name=student.last_name,
        username=student.username or "",
        password=student.password or "",
        date_of_birth=student.date_of_birth,
        school_name=student.school_name,
        medium=student.medium.value if hasattr(student.medium, 'value') else student.medium,
        study_goal=student.study_goal.value if hasattr(student.study_goal, 'value') else student.study_goal,
        daily_study_hours=float(student.daily_study_hours),
        preferred_study_time=student.preferred_study_time.value if hasattr(student.preferred_study_time, 'value') else student.preferred_study_time,
        preferred_study_start_time=student.preferred_study_start_time,
        preferred_study_end_time=student.preferred_study_end_time,
        revision_preference=student.revision_preference.value if hasattr(student.revision_preference, 'value') else student.revision_preference,
        academic_year_start_date=student.academic_year_start_date,
        academic_year_end_date=student.academic_year_end_date,
    )


@router.put("/student/{student_id}", response_model=StudentProfileDetailResponse)
async def update_student_profile(
    student_id: int,
    request: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = OnboardingRepository(db)
    
    # 1. Auto-compute preferred_study_end_time from start_time + daily_study_hours
    start_time = request.preferred_study_start_time
    if not start_time:
        start_time = _get_default_start_time(request.preferred_study_time)
    computed_end_time = _compute_study_end_time(start_time, request.daily_study_hours)

    # 2. Update the student record
    update_data = request.model_dump()
    update_data['preferred_study_start_time'] = start_time
    update_data['preferred_study_end_time'] = computed_end_time
    updated = await repo.update_student(student_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found."
        )

    # 2. Recalculate last taught chapters if academic dates were modified
    today = date.today()
    percent_elapsed = compute_percent_elapsed(
        start_date=request.academic_year_start_date,
        end_date=request.academic_year_end_date,
        today=today,
    )
    subjects = await repo.get_subjects_for_standard(updated.standard_id)
    for subject in subjects:
        total_chapters = await repo.get_chapter_count_for_subject(subject.subject_id)
        last_taught = calculate_last_taught_chapter(percent_elapsed, total_chapters)
        await repo.upsert_syllabus_progress(
            standard_id=updated.standard_id,
            subject_id=subject.subject_id,
            last_taught_chapter_number=last_taught,
            as_of_date=today,
        )

    return StudentProfileDetailResponse(
        student_id=updated.student_id,
        board_id=updated.board_id,
        standard_id=updated.standard_id,
        first_name=updated.first_name,
        last_name=updated.last_name,
        username=updated.username or "",
        password=updated.password or "",
        date_of_birth=updated.date_of_birth,
        school_name=updated.school_name,
        medium=updated.medium.value if hasattr(updated.medium, 'value') else updated.medium,
        study_goal=updated.study_goal.value if hasattr(updated.study_goal, 'value') else updated.study_goal,
        daily_study_hours=float(updated.daily_study_hours),
        preferred_study_time=updated.preferred_study_time.value if hasattr(updated.preferred_study_time, 'value') else updated.preferred_study_time,
        preferred_study_start_time=updated.preferred_study_start_time,
        preferred_study_end_time=updated.preferred_study_end_time,
        revision_preference=updated.revision_preference.value if hasattr(updated.revision_preference, 'value') else updated.revision_preference,
        academic_year_start_date=updated.academic_year_start_date,
        academic_year_end_date=updated.academic_year_end_date,
    )
