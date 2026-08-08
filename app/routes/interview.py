"""
routes/interview.py
API endpoints for generating role-specific interview questions for a job posting.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.job import JobPosting
from app.schemas.interview import QuestionSetResponse
from app.services.interview_gen import generate_questions

router = APIRouter(prefix="/api/interview", tags=["Interview"])


@router.get("/questions/{job_id}", response_model=QuestionSetResponse)
def get_questions(
    job_id: int,
    category: Optional[str] = Query(default=None, description="Technical Skills, Scenario-based, Behavioral, Experience-based"),
    db: Session = Depends(get_db),
):
    """Generate interview questions tailored to a job posting's required skills."""
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")

    questions = generate_questions(
        job_title=job.title,
        required_skills=job.required_skills,
        category_filter=category,
    )

    return QuestionSetResponse(
        job_id=job.id,
        job_title=job.title,
        category_filter=category,
        questions=questions,
    )