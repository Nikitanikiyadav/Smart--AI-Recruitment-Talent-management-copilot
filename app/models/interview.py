"""
models/interview.py
SQLAlchemy ORM model tracking each candidate's status as they move
through the hiring pipeline for a given job (a simple internal ATS tracker).
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from app.database import Base

# The ordered pipeline stages a candidate can be in.
ATS_STAGES = ["Applied", "Screening", "Interview In Progress", "Interview Scheduled", "Offer", "Rejected"]


class ATSStatus(Base):
    __tablename__ = "ats_status"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),)

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    stage = Column(String(50), default="Applied")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)