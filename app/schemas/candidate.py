from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CandidateBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    experience_years: Optional[str] = None
    skills: Optional[str] = None

class CandidateResponse(CandidateBase):
    id: int
    resume_filename: Optional[str] = None
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class ParsingStats(BaseModel):
    resumes_processed: int
    extraction_accuracy: float
    profiles_created: int