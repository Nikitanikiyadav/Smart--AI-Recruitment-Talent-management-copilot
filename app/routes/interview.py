"""
routes/interview.py
API endpoints for generating role-specific interview questions,
evaluating candidate answers, producing a final interview report,
and assessing voice-screening call transcripts.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.job import JobPosting
from app.models.candidate import Candidate
from app.schemas.interview import (
    QuestionSetResponse, AnswerSubmit, AnswerEvaluation,
    ReportRequest, InterviewReport,
    VoiceScreenRequest, VoiceScreenResponse,
)
from app.services.interview_gen import generate_questions, get_difficulty
from app.services.interview_eval import evaluate_answer, build_report
from app.services.voice_screen import assess_transcript

router = APIRouter(prefix="/api/interview", tags=["Interview"])


@router.get("/questions/{job_id}", response_model=QuestionSetResponse)
def get_questions(
    job_id: int,
    candidate_id: Optional[int] = Query(default=None, description="If given, questions are tailored to this candidate's resume"),
    category: Optional[str] = Query(default=None, description="Technical Skills, Scenario-based, Behavioral, Experience-based"),
    db: Session = Depends(get_db),
):
    """Generate interview questions tailored to a job's required skills (and optionally a candidate's resume)."""
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")

    candidate_skills = None
    if candidate_id is not None:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if candidate:
            candidate_skills = candidate.skills

    questions = generate_questions(
        job_title=job.title,
        required_skills=job.required_skills,
        description=job.description,
        candidate_skills=candidate_skills,
        category_filter=category,
    )

    return QuestionSetResponse(
        job_id=job.id,
        job_title=job.title,
        difficulty=get_difficulty(job.min_experience_years),
        category_filter=category,
        questions=questions,
    )


@router.post("/evaluate", response_model=AnswerEvaluation)
def evaluate(submission: AnswerSubmit):
    """Score a candidate's answer to an interview question (heuristic evaluation)."""
    return evaluate_answer(
        question=submission.question,
        skill=submission.skill,
        answer_text=submission.answer_text,
    )


@router.post("/report", response_model=InterviewReport)
def report(req: ReportRequest):
    """Aggregate all answer scores from an interview into a final report and hiring recommendation."""
    results = [{"skill": r.skill, "overall_score": r.overall_score} for r in req.results]
    return build_report(
        candidate_name=req.candidate_name,
        job_title=req.job_title,
        results=results,
    )


@router.post("/voice-screen", response_model=VoiceScreenResponse)
def voice_screen(req: VoiceScreenRequest, db: Session = Depends(get_db)):
    """Produce a preliminary assessment from a voice-screening call transcript."""
    job = db.query(JobPosting).filter(JobPosting.id == req.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")

    result = assess_transcript(
        transcript=req.transcript,
        job_title=job.title,
        required_skills=job.required_skills,
    )
    return VoiceScreenResponse(**result)