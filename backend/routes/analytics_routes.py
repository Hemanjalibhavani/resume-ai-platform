"""History, dashboard analytics and health endpoints."""
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend import models
from backend.database import get_db
from backend.services import llm_service
from backend.services.embedding_service import embedding_service
from backend.services.skill_extractor import display_name

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/health")
def health():
    """Runtime status: which AI mode and embedding backend are active."""
    return {"status": "ok", "ai_mode": llm_service.mode(), "llm_provider": llm_service.provider(),
            "embedding_backend": embedding_service.backend or "loads on first analysis",
            "message": None if llm_service.is_available() else
            "AI service is currently unavailable. Running in local analysis mode."}


@router.get("/history")
def history(db: Session = Depends(get_db)):
    matches = db.query(models.MatchResult).order_by(models.MatchResult.id.desc()).all()
    out = []
    for m in matches:
        job, r = db.get(models.Job, m.job_id), db.get(models.Resume, m.resume_id)
        out.append({"id": m.id, "resume_id": r.id, "job_id": job.id, "candidate": r.candidate_name,
                    "resume_file": r.filename, "job_title": job.title, "score": m.score,
                    "label": m.result.get("label"), "created_at": m.created_at.isoformat()})
    sessions = [{"id": s.id, "resume_id": s.resume_id, "avg_score": s.avg_score, "questions": len(s.questions),
                 "answered": sum(1 for q in s.questions if q.score is not None), "created_at": s.created_at.isoformat()}
                for s in db.query(models.InterviewSession).order_by(models.InterviewSession.id.desc())]
    return {"matches": out, "interviews": sessions}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    resumes = db.query(models.Resume).all()
    jobs = db.query(models.Job).all()
    matches = db.query(models.MatchResult).order_by(models.MatchResult.id).all()
    skills = Counter()
    for r in resumes:
        for s in r.parsed["skills"]:
            skills[s] += 1
    gaps = Counter(g.skill for g in db.query(models.SkillGap).filter_by(status="missing"))
    cats = Counter(s.category for s in db.query(models.ResumeSkill))
    sessions = db.query(models.InterviewSession).order_by(models.InterviewSession.id).all()
    avg = round(sum(m.score for m in matches) / len(matches), 1) if matches else 0
    return {
        "totals": {"resumes": len(resumes), "jobs": len(jobs), "matches": len(matches), "average_score": avg,
                   "skills_matched": sum(len(m.result.get("matched_skills", [])) for m in matches),
                   "top_skill": display_name(skills.most_common(1)[0][0]) if skills else "-",
                   "biggest_gap": display_name(gaps.most_common(1)[0][0]) if gaps else "-"},
        "match_scores": [{"label": f"#{m.id}", "score": m.score} for m in matches[-10:]],
        "skills_distribution": [{"category": k, "count": v} for k, v in cats.items()],
        "skill_gap": [{"skill": display_name(k), "count": v} for k, v in gaps.most_common(8)],
        "jobs_analyzed": [{"title": j.title, "id": j.id} for j in jobs[-8:]],
        "score_history": [{"label": m.created_at.strftime("%d %b %H:%M"), "score": m.score} for m in matches],
        "interview_performance": [{"label": f"Session {s.id}", "score": s.avg_score} for s in sessions if s.avg_score],
        "recent_resumes": [{"id": r.id, "name": r.candidate_name, "file": r.filename, "score": r.completeness_score}
                           for r in resumes[-5:][::-1]],
        "recent_matches": [{"id": m.id, "score": m.score, "label": m.result.get("label")} for m in matches[-5:][::-1]],
    }
