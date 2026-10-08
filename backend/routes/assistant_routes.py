"""RAG career assistant endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend import models
from backend.database import get_db
from backend.schemas import ChatRequest
from backend.services import rag_service, repository as repo

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    resume = repo.get_resume(db, req.resume_id)
    match = repo.get_match(db, req.match_id) if req.match_id else (
        db.query(models.MatchResult).filter_by(resume_id=resume.id).order_by(models.MatchResult.id.desc()).first())
    result = rag_service.answer(db, resume, req.question, match)
    db.add_all([models.ChatHistory(resume_id=resume.id, role="user", message=req.question),
                models.ChatHistory(resume_id=resume.id, role="assistant", message=result["answer"])])
    db.commit()
    return result


@router.get("/history/{resume_id}")
def history(resume_id: int, db: Session = Depends(get_db)):
    rows = db.query(models.ChatHistory).filter_by(resume_id=resume_id).order_by(models.ChatHistory.id).all()
    return [{"role": r.role, "message": r.message, "created_at": r.created_at.isoformat()} for r in rows]
