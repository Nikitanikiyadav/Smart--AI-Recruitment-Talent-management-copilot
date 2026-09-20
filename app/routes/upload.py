"""
routes/upload.py
API endpoint(s) for uploading resumes, running the parsing + extraction
pipeline, and storing the resulting candidate profile.

Duplicate handling: if the extracted email already matches an existing
candidate, that candidate's record is UPDATED in place (new resume file,
re-parsed fields) instead of creating a duplicate row.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.candidate import Candidate
from app.services.parser import extract_text
from app.services.extractor import extract_fields
from app.utils.file_utils import save_upload, save_extracted_profile, is_allowed_file

router = APIRouter(prefix="/api/upload", tags=["Upload"])


def _process_one_resume(file: UploadFile, db: Session) -> dict:
    if not is_allowed_file(file.filename):
        raise ValueError("Only PDF and DOCX files are supported.")

    file_path = save_upload(file)

    try:
        raw_text = extract_text(file_path)
    except Exception as e:
        raise ValueError(f"Failed to parse resume: {e}")

    if not raw_text.strip():
        raise ValueError("No extractable text found in resume.")

    profile = extract_fields(raw_text)
    json_path = save_extracted_profile(file.filename, profile)

    email = profile.get("email")
    existing = None
    if email:
        existing = db.query(Candidate).filter(Candidate.email == email).first()

    is_update = existing is not None

    if is_update:
        candidate = existing
        candidate.name = profile.get("name") or candidate.name
        candidate.phone = profile.get("phone") or candidate.phone
        candidate.location = profile.get("location") or candidate.location
        candidate.education = profile.get("education") or candidate.education
        candidate.experience_years = profile.get("experience_years") or candidate.experience_years
        candidate.skills = profile.get("skills") or candidate.skills
        candidate.resume_filename = file.filename
        candidate.raw_text_path = json_path
        candidate.status = "Processed"
    else:
        candidate = Candidate(
            name=profile.get("name"),
            email=profile.get("email"),
            phone=profile.get("phone"),
            location=profile.get("location"),
            education=profile.get("education"),
            experience_years=profile.get("experience_years"),
            skills=profile.get("skills"),
            resume_filename=file.filename,
            raw_text_path=json_path,
            status="Processed",
        )
        db.add(candidate)

    db.commit()
    db.refresh(candidate)

    return {
        "filename": file.filename,
        "candidate_id": candidate.id,
        "extracted_profile": profile,
        "is_duplicate_update": is_update,
    }


@router.post("/")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        result = _process_one_resume(file, db)
    except ValueError as e:
        status = 400 if "PDF and DOCX" in str(e) else 422
        raise HTTPException(status_code=status, detail=str(e))

    message = (
        "Existing candidate profile updated (duplicate email detected)"
        if result["is_duplicate_update"]
        else "Resume processed successfully"
    )

    return {
        "message": message,
        "candidate_id": result["candidate_id"],
        "extracted_profile": result["extracted_profile"],
        "is_duplicate_update": result["is_duplicate_update"],
    }


@router.post("/bulk")
async def upload_resumes_bulk(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    results = []
    for file in files:
        try:
            result = _process_one_resume(file, db)
            results.append({
                "filename": file.filename,
                "success": True,
                "candidate_id": result["candidate_id"],
                "is_duplicate_update": result["is_duplicate_update"],
                "name": result["extracted_profile"].get("name"),
            })
        except ValueError as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e),
            })

    succeeded = sum(1 for r in results if r["success"])
    updated = sum(1 for r in results if r.get("is_duplicate_update"))

    return {
        "total": len(files),
        "succeeded": succeeded,
        "failed": len(files) - succeeded,
        "updated_existing": updated,
        "created_new": succeeded - updated,
        "results": results,
    }