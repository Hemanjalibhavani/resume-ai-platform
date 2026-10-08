"""Resume upload / retrieval / analysis endpoints."""
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend import models
from backend.config import settings
from backend.database import get_db
from backend.schemas import ResumeAnalyzeRequest
from backend.services import repository as repo
from backend.services.resume_analyzer import ats_score, improve_bullets
from backend.services.resume_parser import extract_text
from backend.utils.file_validator import validate_upload
from backend.utils.helpers import get_logger

router = APIRouter(prefix="/api/resume", tags=["resume"])
log = get_logger(__name__)


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Validate, extract text, parse and store a resume (PDF or DOCX)."""
    data = await file.read()
    name = validate_upload(file.filename or "resume.pdf", data)
    text = extract_text(data, name)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    resume = repo.save_resume(db, text, name)
    (Path(settings.upload_dir) / f"{resume.id}_{name}").write_bytes(data)
    log.info("Resume %s uploaded (%s)", resume.id, name)
    return repo.resume_view(resume)


@router.post("/demo")
def demo_resume(db: Session = Depends(get_db)):
    """Create a resume from the bundled sample so the app works without any upload."""
    text = (Path(settings.data_dir) / "sample_resume.txt").read_text(encoding="utf-8")
    return repo.resume_view(repo.save_resume(db, text, "demo_resume.txt"))


@router.get("s")
def list_resumes(db: Session = Depends(get_db)):
    rows = db.query(models.Resume).order_by(models.Resume.id.desc()).all()
    return [{"id": r.id, "filename": r.filename, "candidate_name": r.candidate_name,
             "score": r.completeness_score, "skills": len(r.parsed["skills"]),
             "created_at": r.created_at.isoformat()} for r in rows]


@router.post("/analyze")
def analyze_resume(req: ResumeAnalyzeRequest, db: Session = Depends(get_db)):
    """Completeness, estimated ATS score and bullet improvements (job-aware when job_id given)."""
    resume = repo.get_resume(db, req.resume_id)
    jd = repo.get_job(db, req.job_id).parsed if req.job_id else None
    return {"resume": repo.resume_view(resume), "ats": ats_score(resume.raw_text, resume.parsed, jd),
            "improvements": improve_bullets(resume.parsed, jd)}


@router.get("/{resume_id}")
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    return repo.resume_view(repo.get_resume(db, resume_id))
