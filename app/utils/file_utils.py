"""
utils/file_utils.py
Helper functions for handling files on disk.
"""

import os
import json
import shutil
from fastapi import UploadFile

UPLOAD_DIR = "/tmp/uploads"
EXTRACTED_DIR = "/tmp/extracted_data"

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def ensure_dirs():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(EXTRACTED_DIR, exist_ok=True)


def is_allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def save_upload(file: UploadFile) -> str:
    """Save an uploaded file to the uploads/ directory and return its path."""
    ensure_dirs()
    dest_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return dest_path


def save_extracted_profile(filename: str, profile: dict) -> str:
    """Save the structured candidate profile as JSON in extracted_data/."""
    ensure_dirs()
    base_name = os.path.splitext(filename)[0]
    json_path = os.path.join(EXTRACTED_DIR, f"{base_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    return json_path
