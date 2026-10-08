"""Job description endpoints."""
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend import models
from backend.database import get_db
from backend.schemas import JobAnalyzeRequest
from backend.services import repository as repo
from backend.services.jd_analyzer import jd_from_file
from backend.services.recommendation_service import sample_jobs
from backend.utils.file_validator import ALLOWED_JD, validate_upload

router = APIRouter(prefix="/api/job", tags=["job"])


@router.post("/analyze")
def analyze_job(req: JobAnalyzeRequest, db: Session = Depends(get_db)):
    """Analyse pasted job-description text and store it."""
    return repo.job_view(repo.save_job(db, req.text, req.title))


@router.post("/upload")
async def upload_job(file: UploadFile = File(...), db: Session = Depends(get_db)):
    data = await file.read()
    name = validate_upload(file.filename or "jd.txt", data, ALLOWED_JD)
    return repo.job_view(repo.save_job(db, jd_from_file(data, name)))


@router.get("/samples")
def samples():
    """Bundled sample job descriptions (Software, Backend, Data, ML, GenAI)."""
    return sample_jobs()


@router.post("/samples/{sample_id}")
def use_sample(sample_id: int, db: Session = Depends(get_db)):
    """Store a sample JD as the user's job and return its analysis."""
    for j in sample_jobs():
        if j["id"] == sample_id:
            return repo.job_view(repo.save_job(db, j["text"], j["title"]))
    from backend.utils.helpers import AppError
    raise AppError("Sample job not found.", 404)


@router.get("s")
def list_jobs(db: Session = Depends(get_db)):
    rows = db.query(models.Job).order_by(models.Job.id.desc()).all()
    return [{"id": j.id, "title": j.title, "skills": len(j.parsed["required_skills"]) + len(j.parsed["preferred_skills"]),
             "created_at": j.created_at.isoformat()} for j in rows]


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    return repo.job_view(repo.get_job(db, job_id))
