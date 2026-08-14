"""
Diagnostic Pydantic models — request/response contracts.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class StartDiagnosticRequest(BaseModel):
    student_id: int


class DiagnosticQuestionModel(BaseModel):
    diagnostic_question_id: int
    question_id: int
    source: str
    section: str
    order: int
    # Details for rendering the question
    question_text: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None


class StartDiagnosticResponse(BaseModel):
    session_id: int
    entry_point: str
    questions: List[DiagnosticQuestionModel]


class QuestionResponse(BaseModel):
    question_id: int  # The question_id (either academic_questions or aptitude_questions)
    source: str       # 'ACADEMIC' | 'APTITUDE'
    selected_option: Optional[str] = None
    time_taken_seconds: int


class SubmitDiagnosticRequest(BaseModel):
    session_id: int
    responses: List[QuestionResponse]


class GapAnalysisSuggestion(BaseModel):
    category: str
    accuracy: float
    suggestion: str


class GapAnalysisResponse(BaseModel):
    session_id: int
    suggestions: List[GapAnalysisSuggestion]


class CategoryScoreModel(BaseModel):
    accuracy: float
    percentile: float


class DiagnosticReportResponse(BaseModel):
    session_id: int
    academic_accuracy: float
    aptitude_score: float
    aptitude_percentile: float
    study_health_score: float
    category_scores: Dict[str, CategoryScoreModel]
    weakest_chapter_ids: List[int]
