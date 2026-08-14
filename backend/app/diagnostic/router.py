"""
Diagnostic Router — FastAPI endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict

from app.database import get_db
from app.onboarding.entry_point_resolver import resolve_entry_point
from .models import (
    StartDiagnosticRequest, StartDiagnosticResponse, DiagnosticQuestionModel,
    SubmitDiagnosticRequest, DiagnosticReportResponse, CategoryScoreModel,
    GapAnalysisResponse, GapAnalysisSuggestion
)
from .repository import DiagnosticRepository
from .test_picker import TestPicker
from .scoring import ScoringEngine
from .gap_analysis import GapAnalysisEngine

router = APIRouter(prefix="/diagnostic", tags=["Diagnostic"])


def get_subject_section(subj_name: str) -> str:
    name_lower = subj_name.lower()
    if "math" in name_lower:
        return "Mathematics"
    elif "science" in name_lower or "environmental studies part 1" in name_lower:
        return "Science"
    elif "history" in name_lower or "civics" in name_lower or "environmental studies part 2" in name_lower:
        return "History and Civics"
    elif "geography" in name_lower:
        return "Geography"
    elif "hindi" in name_lower:
        return "Hindi"
    elif "marathi" in name_lower:
        return "Marathi"
    return "Other"


@router.post("/start", response_model=StartDiagnosticResponse)
async def start_diagnostic(
    request: StartDiagnosticRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = DiagnosticRepository(db)

    # 1. Verify student exists
    student = await repo.get_student_profile(request.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {request.student_id} not found."
        )

    # 2. One-time-only constraint
    has_completed = await repo.has_completed_diagnostic(request.student_id)
    if has_completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Diagnostic already completed — mastery now updates from daily study activity."
        )

    # 3. Resolve entry point from student profile dates
    entry_point = resolve_entry_point(
        start_date=student.academic_year_start_date,
        end_date=student.academic_year_end_date
    )

    # 4. Create diagnostic session
    session = await repo.create_session(
        student_id=request.student_id,
        entry_point=entry_point.value,
        standard_id=student.standard_id
    )



    # If END_OF_TERM, go straight to planner (empty question list)
    if entry_point.value == "END_OF_TERM":
        await repo.mark_session_completed(session.session_id)
        return StartDiagnosticResponse(
            session_id=session.session_id,
            entry_point=entry_point.value,
            questions=[]
        )

    # 5. Fetch question pools
    # We need questions from Std 5, 6, 7
    academic_pool = await repo.get_academic_questions_pool([5, 6, 7])
    aptitude_pool = await repo.get_aptitude_questions_pool()

    # Get syllabus pacing mapping for Std 7 (filter for MID_SEMESTER Std 7 questions)
    syllabus_pacing = await repo.get_syllabus_progress(student.standard_id)

    # Get active subjects for standard 5, 6, 7
    subjects_by_std = await repo.get_subjects_by_standard([5, 6, 7])

    # 6. Pick questions
    picked_questions_meta = TestPicker.pick_questions(
        entry_point=entry_point,
        academic_pool=academic_pool,
        aptitude_pool=aptitude_pool,
        syllabus_progress=syllabus_pacing,
        subjects_by_std=subjects_by_std
    )

    # Save selected metadata to DB
    await repo.save_diagnostic_questions(session.session_id, picked_questions_meta)

    # Load complete questions from DB for frontend display
    session_questions = await repo.get_session_questions(session.session_id)
    
    academic_ids = [q.question_id for q in session_questions if q.question_source.value == 'ACADEMIC']
    aptitude_ids = [q.question_id for q in session_questions if q.question_source.value == 'APTITUDE']

    academic_details = {q['question_id']: q for q in await repo.get_academic_question_details(academic_ids)}
    aptitude_details = {q['question_id']: q for q in await repo.get_aptitude_question_details(aptitude_ids)}

    response_questions = []
    for q in session_questions:
        qid = q.question_id
        q_source = q.question_source.value
        details = academic_details.get(qid) if q_source == 'ACADEMIC' else aptitude_details.get(qid)
        
        if details:
            if q_source == 'APTITUDE':
                section_name = "Aptitude section"
            else:
                section_name = get_subject_section(details.get('subject_name', ''))

            response_questions.append(
                DiagnosticQuestionModel(
                    diagnostic_question_id=q.diagnostic_question_id,
                    question_id=qid,
                    source=q_source,
                    section=section_name,
                    order=q.question_order,
                    question_text=details['question_text'],
                    option_a=details['option_a'],
                    option_b=details['option_b'],
                    option_c=details['option_c'],
                    option_d=details['option_d']
                )
            )



    return StartDiagnosticResponse(
        session_id=session.session_id,
        entry_point=entry_point.value,
        questions=response_questions
    )


@router.post("/submit", response_model=DiagnosticReportResponse)
async def submit_diagnostic(
    request: SubmitDiagnosticRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = DiagnosticRepository(db)

    # Verify session exists
    session = await repo.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {request.session_id} not found."
        )

    # Get student profile to calculate syllabus coverage confidence
    student = await repo.get_student_profile(session.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    # Load session questions
    session_questions = await repo.get_session_questions(request.session_id)
    academic_meta = {q.question_id: q for q in session_questions if q.question_source.value == 'ACADEMIC'}
    aptitude_meta = {q.question_id: q for q in session_questions if q.question_source.value == 'APTITUDE'}

    academic_ids = list(academic_meta.keys())
    aptitude_ids = list(aptitude_meta.keys())

    # Fetch correct options and metadata
    academic_questions_db = {q['question_id']: q for q in await repo.get_academic_questions_by_ids(academic_ids)}
    aptitude_questions_db = {q['question_id']: q for q in await repo.get_aptitude_questions_by_ids(aptitude_ids)}

    # Grade responses
    academic_responses_scored = []
    aptitude_responses_scored = []
    db_responses_to_save = []

    # Maps chapter_id -> list of graded responses for chapter mastery calculation
    chapter_responses = {}

    for resp in request.responses:
        qid = resp.question_id
        source = resp.source.upper()
        selected = resp.selected_option
        time_taken = resp.time_taken_seconds

        if source == 'ACADEMIC':
            q_db = academic_questions_db.get(qid)
            if not q_db:
                continue
            # Skipped questions (selected_option is None) are treated as incorrect
            is_correct = (selected is not None and selected == q_db['correct_option'])
            scored_item = {
                "question_id": qid,
                "is_correct": is_correct,
                "difficulty": q_db['difficulty'],
                "time_taken_seconds": time_taken,
                "estimated_seconds": q_db['estimated_seconds'],
                "chapter_id": q_db['chapter_id']
            }
            academic_responses_scored.append(scored_item)
            chapter_responses.setdefault(q_db['chapter_id'], []).append(scored_item)
            db_responses_to_save.append({
                "source": "ACADEMIC",
                "question_id": qid,
                "chapter_id": q_db['chapter_id'],
                "selected_option": selected,
                "is_correct": is_correct,
                "time_taken_seconds": time_taken
            })
        elif source == 'APTITUDE':
            q_db = aptitude_questions_db.get(qid)
            if not q_db:
                continue
            # Skipped questions (selected_option is None) are treated as incorrect
            is_correct = (selected is not None and selected == q_db['correct_option'])
            scored_item = {
                "question_id": qid,
                "is_correct": is_correct,
                "difficulty": q_db['difficulty'],
                "category": q_db['category']
            }
            aptitude_responses_scored.append(scored_item)
            db_responses_to_save.append({
                "source": "APTITUDE",
                "question_id": qid,
                "selected_option": selected,
                "is_correct": is_correct,
                "time_taken_seconds": time_taken
            })

    # Save diagnostic responses to DB
    await repo.save_diagnostic_responses(request.session_id, db_responses_to_save)

    # 1. Chapter Mastery & baseline chapter_mastery population
    chapter_masteries = {}
    for ch_id, ch_resps in chapter_responses.items():
        mastery = ScoringEngine.compute_chapter_mastery(ch_resps)
        chapter_masteries[ch_id] = mastery
        await repo.upsert_chapter_mastery(session.student_id, ch_id, mastery)

    # 2. Aptitude overall & category breakdown
    apt_percentage, apt_percentile = ScoringEngine.compute_aptitude_score_and_percentile(aptitude_responses_scored)
    category_breakdown = ScoringEngine.compute_aptitude_category_breakdown(aptitude_responses_scored)
    await repo.save_aptitude_category_scores(request.session_id, category_breakdown)

    # 3. Academic accuracy (overall)
    academic_accuracy = ScoringEngine.compute_chapter_mastery(academic_responses_scored)

    # 4. Syllabus coverage confidence
    # Compute: total taught chapters / total chapters in subject * 100
    pacing_map = await repo.get_syllabus_progress(student.standard_id)
    total_chapters_taught = sum(pacing_map.values())
    
    # Get total chapters for standard subjects
    subjects = await repo.get_subjects_by_standard([student.standard_id])
    std_subjects = subjects.get(student.standard_id, [])
    total_chapters_count = 0
    for s in std_subjects:
        total_chapters_count += await repo.get_chapter_count_for_subject(s['subject_id'])

    syllabus_coverage_confidence = 100.0
    if total_chapters_count > 0:
        syllabus_coverage_confidence = (total_chapters_taught / total_chapters_count) * 100.0

    # 5. Study health score
    avg_mastery = sum(chapter_masteries.values()) / len(chapter_masteries) if chapter_masteries else 0.0
    study_health = ScoringEngine.compute_study_health_score(
        avg_chapter_mastery=avg_mastery,
        aptitude_percentile=apt_percentile,
        syllabus_coverage_confidence=syllabus_coverage_confidence
    )

    # Identify weakest chapters (mastery < 60%, sorted ascending)
    weak_chapters = [ch_id for ch_id, score in chapter_masteries.items() if score < 60.0]
    # If none below 60%, pick the lowest ones
    if not weak_chapters and chapter_masteries:
        sorted_ch = sorted(chapter_masteries.items(), key=lambda x: x[1])
        weak_chapters = [ch[0] for ch in sorted_ch[:5]]

    report_data = {
        "aptitude_score": apt_percentage,
        "aptitude_percentile": apt_percentile,
        "academic_accuracy": academic_accuracy,
        "study_health_score": study_health,
        "weakest_chapter_ids": weak_chapters
    }
    await repo.save_diagnostic_report(request.session_id, report_data)

    # Mark session completed
    await repo.mark_session_completed(request.session_id)

    response_cats = {
        cat: CategoryScoreModel(accuracy=data['accuracy'], percentile=data['percentile'])
        for cat, data in category_breakdown.items()
    }

    return DiagnosticReportResponse(
        session_id=request.session_id,
        academic_accuracy=academic_accuracy,
        aptitude_score=apt_percentage,
        aptitude_percentile=apt_percentile,
        study_health_score=study_health,
        category_scores=response_cats,
        weakest_chapter_ids=weak_chapters
    )


@router.get("/{session_id}/report", response_model=DiagnosticReportResponse)
async def get_diagnostic_report(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    repo = DiagnosticRepository(db)
    report = await repo.get_diagnostic_report(session_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic report for session {session_id} not found."
        )

    cat_scores = await repo.get_aptitude_category_scores(session_id)
    category_scores_map = {
        cs.category: CategoryScoreModel(accuracy=float(cs.accuracy), percentile=float(cs.percentile))
        for cs in cat_scores
    }

    return DiagnosticReportResponse(
        session_id=session_id,
        academic_accuracy=float(report.academic_accuracy),
        aptitude_score=float(report.aptitude_score),
        aptitude_percentile=float(report.aptitude_percentile),
        study_health_score=float(report.study_health_score),
        category_scores=category_scores_map,
        weakest_chapter_ids=report.weakest_chapter_ids or []
    )


@router.get("/{session_id}/gap-analysis", response_model=GapAnalysisResponse)
async def get_gap_analysis(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    repo = DiagnosticRepository(db)
    cat_scores = await repo.get_aptitude_category_scores(session_id)
    if not cat_scores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aptitude category scores for session {session_id} not found."
        )

    category_scores_dict = {
        cs.category: {"accuracy": float(cs.accuracy), "percentile": float(cs.percentile)}
        for cs in cat_scores
    }

    suggestions = GapAnalysisEngine.generate_suggestions(category_scores_dict)

    response_suggestions = [
        GapAnalysisSuggestion(
            category=s['category'],
            accuracy=s['accuracy'],
            suggestion=s['suggestion']
        )
        for s in suggestions
    ]

    return GapAnalysisResponse(
        session_id=session_id,
        suggestions=response_suggestions
    )
