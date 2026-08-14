"""
Onboarding Pydantic models — request/response contracts.
Enums mirror the MySQL enums exactly.
"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class OnboardingRequest(BaseModel):
    """All fields needed to create a student profile and trigger entry-point resolution."""
    board_id: int
    standard_id: int
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    username: str = Field(..., max_length=100)
    password: str = Field(..., max_length=100)
    date_of_birth: Optional[date] = None
    school_name: Optional[str] = Field(None, max_length=255)
    # Fields from the original student_profiles schema
    medium: str = Field(default="English", description="English | Marathi | Hindi")
    study_goal: str = Field(..., description="EXAM_PREPARATION | SKILL_BUILDING | GENERAL_LEARNING")
    daily_study_hours: float = Field(..., gt=0, le=12)
    preferred_study_time: str = Field(..., description="MORNING | AFTERNOON | EVENING | NIGHT")
    preferred_study_start_time: Optional[str] = Field(None, max_length=5, description="HH:MM formatted start time")
    # preferred_study_end_time is auto-calculated: start_time + daily_study_hours
    revision_preference: str = Field(..., description="DAILY | WEEKLY | BOTH")
    # Calendar bounds for entry-point resolution
    academic_year_start_date: date
    academic_year_end_date: date


class OnboardingResponse(BaseModel):
    student_id: int
    entry_point: str


class LoginRequest(BaseModel):
    username: str = Field(..., max_length=100)
    password: str = Field(..., max_length=100)


class LoginResponse(BaseModel):
    student_id: int
    entry_point: str
    diagnostic_completed: bool
    session_id: Optional[int] = None


class StudentProfileDetailResponse(BaseModel):
    student_id: int
    board_id: int
    standard_id: int
    first_name: str
    last_name: str
    username: str
    password: str
    date_of_birth: Optional[date] = None
    school_name: Optional[str] = None
    medium: str
    study_goal: str
    daily_study_hours: float
    preferred_study_time: str
    preferred_study_start_time: Optional[str] = None
    preferred_study_end_time: Optional[str] = None
    revision_preference: str
    academic_year_start_date: date
    academic_year_end_date: date


class UpdateProfileRequest(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    password: str = Field(..., max_length=100)
    date_of_birth: Optional[date] = None
    school_name: Optional[str] = Field(None, max_length=255)
    medium: str
    study_goal: str
    daily_study_hours: float
    preferred_study_time: str
    preferred_study_start_time: Optional[str] = Field(None, max_length=5)
    # preferred_study_end_time is auto-calculated: start_time + daily_study_hours
    revision_preference: str
    academic_year_start_date: date
    academic_year_end_date: date
