from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    education = Column(String(255), nullable=True)
    experience_years = Column(String(50), nullable=True)
    skills = Column(Text, nullable=True)
    resume_filename = Column(String(255), nullable=True)
    raw_text_path = Column(String(500), nullable=True)
    status = Column(String(50), default="Processed")
    uploaded_at = Column(DateTime, default=datetime.utcnow)