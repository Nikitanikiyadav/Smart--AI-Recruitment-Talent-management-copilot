from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.candidate import Candidate
from app.services.parser import extract_text
from app.services.extractor import extract_fields
from app.utils.file_utils import save_upload, save_extracted_profile

router = APIRouter(prefix="/api/upload", tags=["Upload"])

@router.post("/")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = save_upload(file)                     # Step 9
    raw_text = extract_text(file_path)                 # Step 7
    profile = extract_fields(raw_text)                  # Step 8
    json_path = save_extracted_profile(file.filename, profile)  # Step 9

    candidate = Candidate(**profile, resume_filename=file.filename,
                           raw_text_path=json_path, status="Processed")  # Step 5
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {"candidate_id": candidate.id, "extracted_profile": profile}