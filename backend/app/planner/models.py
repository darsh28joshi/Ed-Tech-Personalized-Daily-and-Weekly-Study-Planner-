"""
Planner Pydantic models.
"""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional, Dict, Any


class GenerateDailyPlanRequest(BaseModel):
    student_id: int
    plan_date: date
    strategy: str = Field(default="knapsack", description="knapsack | greedy")
    force_regenerate: bool = False


class TaskModel(BaseModel):
    task_id: int
    chapter_id: int
    chapter_name: str
    subject_name: str
    allocated_minutes: int
    status: str
    carried_forward_from_task_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class DailyPlanResponse(BaseModel):
    student_id: int
    plan_date: date
    strategy_used: str
    total_allocated_minutes: int
    tasks: List[TaskModel]
    comparison: Optional[Dict[str, Any]] = None


class PatchTaskRequest(BaseModel):
    status: str = Field(..., description="COMPLETED | IN_PROGRESS | SKIPPED")


class PatchTaskResponse(BaseModel):
    task_id: int
    status: str
    message: str


class GenerateWeeklyPlanRequest(BaseModel):
    student_id: int


class WeeklyDayTaskModel(BaseModel):
    chapter_id: int
    chapter_name: str
    subject_name: str
    cost: int


class WeeklyDayPlanModel(BaseModel):
    day_number: int
    allocated_minutes: int
    capacity_minutes: int
    tasks: List[WeeklyDayTaskModel]


class WeeklyPlanResponse(BaseModel):
    student_id: int
    days: List[WeeklyDayPlanModel]
