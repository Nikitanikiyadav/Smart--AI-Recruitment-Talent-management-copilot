"""
models/job.py
SQLAlchemy ORM model representing a job posting that candidates
will be matched against.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    required_skills = Column(Text, nullable=False)   # comma-separated skills
    min_experience_years = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)