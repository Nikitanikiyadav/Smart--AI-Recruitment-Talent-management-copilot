"""
routes/ats.py
API endpoints for tracking each candidate's stage in the hiring pipeline
(an internal ATS status tracker) per job posting.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import ATSStatus, ATS_STAGES
from app.models.candidate import Candidate
from app.models.job import JobPosting
from app.schemas.interview import ATSStatusResponse, ATSStatusUpdate

router = APIRouter(prefix="/api/ats", tags=["ATS"])


def _to_response(status_row: ATSStatus, db: Session) -> ATSStatusResponse:
    candidate = db.query(Candidate).filter(Candidate.id == status_row.candidate_id).first()
    job = db.query(JobPosting).filter(JobPosting.id == status_row.job_id).first()
    return ATSStatusResponse(
        candidate_id=status_row.candidate_id,
        candidate_name=candidate.name if candidate else None,
        job_id=status_row.job_id,
        job_title=job.title if job else "Unknown",
        stage=status_row.stage,
        updated_at=status_row.updated_at,
    )


@router.get("/", response_model=list[ATSStatusResponse])
def list_ats_statuses(job_id: int | None = None, db: Session = Depends(get_db)):
    """List all candidate ATS statuses, optionally filtered to one job."""
    query = db.query(ATSStatus)
    if job_id is not None:
        query = query.filter(ATSStatus.job_id == job_id)
    rows = query.all()
    return [_to_response(r, db) for r in rows]


@router.put("/{candidate_id}/{job_id}", response_model=ATSStatusResponse)
def update_ats_status(candidate_id: int, job_id: int, update: ATSStatusUpdate, db: Session = Depends(get_db)):
    """Create or update a candidate's pipeline stage for a given job."""
    if update.stage not in ATS_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {ATS_STAGES}")

    row = db.query(ATSStatus).filter(
        ATSStatus.candidate_id == candidate_id, ATSStatus.job_id == job_id
    ).first()

    if row is None:
        row = ATSStatus(candidate_id=candidate_id, job_id=job_id, stage=update.stage)
        db.add(row)
    else:
        row.stage = update.stage

    db.commit()
    db.refresh(row)
    return _to_response(row, db)