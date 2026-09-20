"""
routes/analytics.py
Aggregate analytics across all milestones: candidates, jobs, matching
scores, and ATS pipeline stages. Reuses the same matching logic from
Milestone 2 rather than duplicating it.

NOTE on "Avg Time to Hire": we don't store a full stage-history log
(only the latest ATS stage + its updated_at timestamp), so this is an
approximation: (time candidate reached "Offer" stage) - (time their
resume was uploaded), averaged across everyone who has reached Offer.
It's a reasonable proxy, not exact HR data.
"""

from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.job import JobPosting
from app.models.interview import ATSStatus, ATS_STAGES
from app.schemas.analytics import (
    AnalyticsSummary, SkillFrequency, ATSStageCount, JobMatchSummary,
)
from app.services.matcher import compute_match

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(db: Session = Depends(get_db)):
    candidates = db.query(Candidate).all()
    jobs = db.query(JobPosting).all()
    ats_rows = db.query(ATSStatus).all()

    candidates_by_id = {c.id: c for c in candidates}

    # --- Top skills across all candidates ---
    skill_counter = Counter()
    for c in candidates:
        for s in (c.skills or "").split(","):
            s = s.strip()
            if s:
                skill_counter[s] += 1
    top_skills = [SkillFrequency(skill=s, count=n) for s, n in skill_counter.most_common(10)]

    # --- ATS pipeline breakdown (include zero-count stages for a complete chart) ---
    stage_counter = Counter(row.stage for row in ats_rows)
    ats_breakdown = [ATSStageCount(stage=stage, count=stage_counter.get(stage, 0)) for stage in ATS_STAGES]

    # --- Interviews scheduled/in progress ---
    interviews_scheduled = stage_counter.get("Interview In Progress", 0) + stage_counter.get("Interview Scheduled", 0)

    # --- Hiring success rate: % of tracked candidates who reached Offer or Hired ---
    offered_or_hired = stage_counter.get("Offer", 0) + stage_counter.get("Hired", 0)
    hiring_success_rate = round((offered_or_hired / len(ats_rows)) * 100, 1) if ats_rows else 0.0

    # --- Avg time to hire (approximation - see module docstring) ---
    hire_durations = []
    for row in ats_rows:
        if row.stage in ("Offer", "Hired"):
            candidate = candidates_by_id.get(row.candidate_id)
            if candidate and candidate.uploaded_at:
                delta = row.updated_at - candidate.uploaded_at
                hire_durations.append(delta.total_seconds() / 86400)
    avg_time_to_hire = round(sum(hire_durations) / len(hire_durations), 1) if hire_durations else None

    # --- Average match score per job (reuses Milestone 2's matcher) ---
    job_summaries = []
    for job in jobs:
        if not candidates:
            job_summaries.append(JobMatchSummary(job_id=job.id, job_title=job.title, candidate_count=0, average_match_score=0.0))
            continue
        scores = []
        for c in candidates:
            score, _, _ = compute_match(
                candidate_skills=c.skills or "",
                job_required_skills=job.required_skills,
                candidate_experience_years=c.experience_years,
                job_min_experience_years=job.min_experience_years,
            )
            scores.append(score)
        avg = round(sum(scores) / len(scores), 1) if scores else 0.0
        job_summaries.append(JobMatchSummary(
            job_id=job.id, job_title=job.title,
            candidate_count=len(candidates), average_match_score=avg,
        ))

    return AnalyticsSummary(
        total_candidates=len(candidates),
        total_jobs=len(jobs),
        total_ats_tracked=len(ats_rows),
        interviews_scheduled=interviews_scheduled,
        hiring_success_rate=hiring_success_rate,
        avg_time_to_hire_days=avg_time_to_hire,
        top_skills=top_skills,
        ats_stage_breakdown=ats_breakdown,
        job_match_summary=job_summaries,
    )