"""
main.py
FastAPI entry point for the AI Recruitment & Talent Management Copilot.
Milestone 1: Resume Parsing & Candidate Profiling.
Milestone 2: Matching & Skill Analysis.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
# Import models so SQLAlchemy knows about every table before create_all() runs
from app.models import candidate as _candidate_model  # noqa: F401
from app.models import job as _job_model              # noqa: F401
from app.routes import upload, candidate, jobs, match

# Create DB tables on startup (SQLite file: recruitment_copilot.db)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Recruitment & Talent Management Copilot",
    description="Milestone 1 - Resume Parsing & Candidate Profiling | Milestone 2 - Matching & Skill Analysis",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(upload.router)
app.include_router(candidate.router)
app.include_router(jobs.router)
app.include_router(match.router)

# Simple server-rendered UI
templates = Jinja2Templates(directory="frontend")
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/match")
def match_page(request: Request):
    return templates.TemplateResponse("match.html", {"request": request})


@app.get("/api/health")
def health_check():
    return {"status": "ok", "milestone": "2 - Matching & Skill Analysis"}