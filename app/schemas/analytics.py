"""
schemas/analytics.py
Pydantic models for the aggregate analytics dashboard.
"""

from pydantic import BaseModel
from typing import List, Optional


class SkillFrequency(BaseModel):
    skill: str
    count: int


class ATSStageCount(BaseModel):
    stage: str
    count: int


class JobMatchSummary(BaseModel):
    job_id: int
    job_title: str
    candidate_count: int
    average_match_score: float


class AnalyticsSummary(BaseModel):
    total_candidates: int
    total_jobs: int
    total_ats_tracked: int
    interviews_scheduled: int
    hiring_success_rate: float
    avg_time_to_hire_days: Optional[float] = None
    top_skills: List[SkillFrequency]
    ats_stage_breakdown: List[ATSStageCount]
    job_match_summary: List[JobMatchSummary]