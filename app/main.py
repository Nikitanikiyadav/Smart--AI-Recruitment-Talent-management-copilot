from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
from app.routes import upload, candidate

Base.metadata.create_all(bind=engine)   # creates the DB tables on startup

app = FastAPI(title="AI Recruitment Copilot")
app.include_router(upload.router)
app.include_router(candidate.router)

templates = Jinja2Templates(directory="frontend")
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})