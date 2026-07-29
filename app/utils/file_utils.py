import os, json, shutil
from fastapi import UploadFile

UPLOAD_DIR = "uploads"
EXTRACTED_DIR = "extracted_data"

def save_upload(file: UploadFile) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return dest_path

def save_extracted_profile(filename: str, profile: dict) -> str:
    os.makedirs(EXTRACTED_DIR, exist_ok=True)
    base_name = os.path.splitext(filename)[0]
    json_path = os.path.join(EXTRACTED_DIR, f"{base_name}.json")
    with open(json_path, "w") as f:
        json.dump(profile, f, indent=2)
    return json_path