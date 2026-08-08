"""
schemas/interview.py
Pydantic models for interview question generation and ATS status tracking.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class InterviewQuestion(BaseModel):
    question: str
    category: str          # Technical, Behavioral, Scenario-based, Experience-based
    skill: Optional[str] = None
    suggested_response_time: str


class QuestionSetResponse(BaseModel):
    job_id: int
    job_title: str
    category_filter: Optional[str] = None
    questions: List[InterviewQuestion]


class ATSStatusResponse(BaseModel):
    candidate_id: int
    candidate_name: Optional[str] = None
    job_id: int
    job_title: str
    stage: str
    updated_at: datetime

    class Config:
        from_attributes = True


class ATSStatusUpdate(BaseModel):
    stage: str