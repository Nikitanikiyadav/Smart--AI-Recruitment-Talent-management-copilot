"""
schemas/job.py
Pydantic models for job postings and matching/skill-gap responses.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class JobCreate(BaseModel):
    title: str
    description: Optional[str] = None
    required_skills: str          # comma-separated, e.g. "Python, SQL, AWS"
    min_experience_years: Optional[int] = 0


class JobResponse(JobCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MatchResult(BaseModel):
    candidate_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    match_score: float            # 0-100
    matched_skills: List[str]
    missing_skills: List[str]


class SkillGapItem(BaseModel):
    skill: str
    candidate_has_it: bool


class SkillGapResponse(BaseModel):
    candidate_id: int
    candidate_name: Optional[str] = None
    job_id: int
    job_title: str
    match_score: float
    skill_breakdown: List[SkillGapItem]
    recommendation: str