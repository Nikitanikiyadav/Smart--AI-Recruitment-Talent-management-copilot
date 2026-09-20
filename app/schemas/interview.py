"""
schemas/interview.py
Pydantic models for interview question generation, answer evaluation,
final reporting, and ATS status tracking.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class InterviewQuestion(BaseModel):
    question: str
    category: str
    skill: Optional[str] = None
    suggested_response_time: str
    resume_match: Optional[bool] = None


class QuestionSetResponse(BaseModel):
    job_id: int
    job_title: str
    difficulty: str
    category_filter: Optional[str] = None
    questions: List[InterviewQuestion]


class AnswerSubmit(BaseModel):
    question: str
    skill: Optional[str] = None
    answer_text: str


class AnswerEvaluation(BaseModel):
    relevance: float
    technical_accuracy: float
    completeness: float
    overall_score: float
    follow_up_question: Optional[str] = None


class ReportResultItem(BaseModel):
    skill: Optional[str] = None
    overall_score: float


class ReportRequest(BaseModel):
    candidate_name: Optional[str] = None
    job_title: str
    results: List[ReportResultItem]


class SkillCoverageItem(BaseModel):
    skill: str
    average_score: float
    status: str


class InterviewReport(BaseModel):
    candidate_name: Optional[str] = None
    job_title: str
    overall_score: float
    recommendation: str
    summary: str
    skill_coverage: List[SkillCoverageItem]


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
    


class VoiceScreenRequest(BaseModel):
    candidate_id: Optional[int] = None
    job_id: int
    transcript: str


class VoiceScreenResponse(BaseModel):
    assessment: str
    recommended_next_step: str
    skills_mentioned: List[str]