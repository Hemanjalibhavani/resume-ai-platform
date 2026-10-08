"""Interview preparation and practice endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend import models
from backend.database import get_db
from backend.schemas import InterviewEvaluateRequest, InterviewGenerateRequest
from backend.services import interview_service as svc
from backend.services import repository as repo
from backend.utils.helpers import AppError

router = APIRouter(prefix="/api/interview", tags=["interview"])


def _q(q: models.InterviewQuestion) -> dict:
    return {"id": q.id, "category": q.category, "question": q.question, "difficulty": q.difficulty,
            "expected_concepts": q.expected_concepts, "follow_ups": q.follow_ups,
            "sample_answer": q.sample_answer, "answer": q.answer, "score": q.score, "feedback": q.feedback}


@router.get("/categories")
def categories():
    return svc.CATEGORIES + ["Project"]


@router.post("/generate")
def generate(req: InterviewGenerateRequest, db: Session = Depends(get_db)):
    resume = repo.get_resume(db, req.resume_id)
    job = repo.get_job(db, req.job_id) if req.job_id else None
    qs = svc.generate_questions(resume.parsed, job.parsed if job else None, req.categories, req.count)
    session = models.InterviewSession(resume_id=resume.id, job_id=job.id if job else None)
    for q in qs:
        session.questions.append(models.InterviewQuestion(
            category=q["category"], question=q["question"], difficulty=q["difficulty"],
            expected_concepts=q["expected_concepts"], follow_ups=q["follow_ups"],
            sample_answer=svc.sample_answer(q) if req.with_answers else ""))
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "questions": [_q(q) for q in session.questions]}


@router.post("/evaluate")
def evaluate(req: InterviewEvaluateRequest, db: Session = Depends(get_db)):
    q = db.get(models.InterviewQuestion, req.question_id)
    if not q:
        raise AppError("Question not found.", 404)
    fb = svc.evaluate_answer(q.question, q.expected_concepts, req.answer)
    q.answer, q.score, q.feedback = req.answer, fb["score"], fb
    session = db.get(models.InterviewSession, q.session_id)
    scored = [x.score for x in session.questions if x.score is not None]
    session.avg_score = round(sum(scored) / len(scored), 2) if scored else 0.0
    db.commit()
    return {"question_id": q.id, **fb, "session_avg": session.avg_score}


@router.get("/session/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    s = db.get(models.InterviewSession, session_id)
    if not s:
        raise AppError("Interview session not found.", 404)
    return {"session_id": s.id, "avg_score": s.avg_score, "questions": [_q(q) for q in s.questions]}
