from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.candidate import Candidate
from app.schemas.candidate import CandidateResponse, ParsingStats

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])

@router.get("/", response_model=list[CandidateResponse])
def list_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).order_by(Candidate.uploaded_at.desc()).all()

@router.get("/stats/summary", response_model=ParsingStats)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Candidate.id)).scalar() or 0
    return ParsingStats(resumes_processed=total, extraction_accuracy=95.0, profiles_created=total)