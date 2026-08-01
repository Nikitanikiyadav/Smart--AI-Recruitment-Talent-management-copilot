"""
routes/match.py
API endpoints for candidate-job matching and skill-gap analysis.
Milestone 2: Matching & Skill Analysis.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.job import JobPosting
from app.schemas.job import MatchResult, SkillGapResponse, SkillGapItem
from app.services.matcher import compute_match, build_recommendation, _parse_skill_list

router = APIRouter(prefix="/api/match", tags=["Matching"])


@router.get("/{job_id}", response_model=list[MatchResult])
def match_candidates_to_job(job_id: int, db: Session = Depends(get_db)):
    """
    Rank all candidates against a given job posting by match score (highest first).
    """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")

    candidates = db.query(Candidate).all()
    results = []

    for c in candidates:
        score, matched, missing = compute_match(
            candidate_skills=c.skills or "",
            job_required_skills=job.required_skills,
            candidate_experience_years=c.experience_years,
            job_min_experience_years=job.min_experience_years,
        )
        results.append(
            MatchResult(
                candidate_id=c.id,
                name=c.name,
                email=c.email,
                match_score=score,
                matched_skills=matched,
                missing_skills=missing,
            )
        )

    # highest match score first
    results.sort(key=lambda r: r.match_score, reverse=True)
    return results


@router.get("/skill-gap/{candidate_id}/{job_id}", response_model=SkillGapResponse)
def skill_gap_analysis(candidate_id: int, job_id: int, db: Session = Depends(get_db)):
    """
    Detailed skill-by-skill breakdown of one candidate against one job's requirements,
    plus a short text recommendation.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")

    score, matched, missing = compute_match(
        candidate_skills=candidate.skills or "",
        job_required_skills=job.required_skills,
        candidate_experience_years=candidate.experience_years,
        job_min_experience_years=job.min_experience_years,
    )

    required_skills = _parse_skill_list(job.required_skills)
    matched_lower = {m.lower() for m in matched}

    breakdown = [
        SkillGapItem(skill=skill, candidate_has_it=(skill.lower() in matched_lower))
        for skill in required_skills
    ]

    recommendation = build_recommendation(candidate.name, missing)

    return SkillGapResponse(
        candidate_id=candidate.id,
        candidate_name=candidate.name,
        job_id=job.id,
        job_title=job.title,
        match_score=score,
        skill_breakdown=breakdown,
        recommendation=recommendation,
    )