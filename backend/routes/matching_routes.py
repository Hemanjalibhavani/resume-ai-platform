"""Matching, skill-gap, ranking and recommendation endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend import models
from backend.database import get_db
from backend.schemas import MatchRequest, RankRequest
from backend.services import repository as repo
from backend.services.matching_engine import compute_match
from backend.services.recommendation_service import career_recommendations, rank_jobs, sample_jobs
from backend.services.skill_extractor import display_name
from backend.services.skill_gap_service import analyze_gaps

router = APIRouter(prefix="/api", tags=["matching"])


def _match_view(db: Session, m: models.MatchResult) -> dict:
    job = db.get(models.Job, m.job_id)
    resume = db.get(models.Resume, m.resume_id)
    return {"id": m.id, "resume_id": m.resume_id, "job_id": m.job_id, "job_title": job.title,
            "candidate": resume.candidate_name, "created_at": m.created_at.isoformat(), **m.result}


@router.post("/match")
def run_match(req: MatchRequest, db: Session = Depends(get_db)):
    """Run the hybrid matching engine, persist the result, gaps and recommendations."""
    resume, job = repo.get_resume(db, req.resume_id), repo.get_job(db, req.job_id)
    result = compute_match(resume.raw_text, resume.parsed, job.raw_text, job.parsed)
    gaps = analyze_gaps(result, job.parsed)
    ranked = rank_jobs(resume.raw_text, resume.parsed, sample_jobs())
    recs = career_recommendations(result, gaps, ranked)
    result["gaps"] = gaps
    result["recommendations"] = recs
    result["matched_display"] = [display_name(s) for s in result["matched_skills"]]
    m = models.MatchResult(resume_id=resume.id, job_id=job.id, score=result["score"], result=result)
    db.add(m)
    db.flush()
    for g in gaps:
        db.add(models.SkillGap(match_id=m.id, skill=g["skill"], status=g["status"], priority=g["priority"], details=g))
    for r in recs:
        db.add(models.Recommendation(match_id=m.id, kind=r["kind"], text=r["text"]))
    db.commit()
    db.refresh(m)
    return _match_view(db, m)


@router.get("/match/{match_id}")
def get_match(match_id: int, db: Session = Depends(get_db)):
    return _match_view(db, repo.get_match(db, match_id))


@router.post("/match/rank")
def rank(req: RankRequest, db: Session = Depends(get_db)):
    """Rank several job descriptions (saved jobs and/or the 5 samples) for one resume."""
    resume = repo.get_resume(db, req.resume_id)
    jobs = [{"id": j.id, "title": j.title, "text": j.raw_text}
            for j in (repo.get_job(db, i) for i in (req.job_ids or []))]
    if req.include_samples or not jobs:
        jobs += [{"id": None, "title": j["title"], "text": j["text"]} for j in sample_jobs()]
    return rank_jobs(resume.raw_text, resume.parsed, jobs)


@router.get("/skills/gap/{match_id}")
def skill_gap(match_id: int, db: Session = Depends(get_db)):
    """Skill gap report for a match: your skills, required, matched/partial/missing and advice."""
    m = repo.get_match(db, match_id)
    r, res = db.get(models.Resume, m.resume_id), m.result
    job = db.get(models.Job, m.job_id)
    return {"match_id": m.id, "job_title": job.title, "your_skills": [display_name(s) for s in r.parsed["skills"]],
            "required_skills": [display_name(s) for s in job.parsed["required_skills"]],
            "preferred_skills": [display_name(s) for s in job.parsed["preferred_skills"]],
            "matched": [display_name(s) for s in res["matched_skills"]],
            "partial": [{**p, "display": display_name(p["skill"])} for p in res["partial_skills"]],
            "missing": [display_name(s) for s in res["missing_skills"]],
            "skill_strength": {display_name(k): v for k, v in res["skill_strength"].items()},
            "gaps": res["gaps"]}


@router.get("/recommendations")
def recommendations(resume_id: int | None = None, db: Session = Depends(get_db)):
    """Latest recommendations (optionally for one resume) plus ranked sample roles."""
    q = db.query(models.MatchResult)
    if resume_id:
        q = q.filter_by(resume_id=resume_id)
    latest = q.order_by(models.MatchResult.id.desc()).first()
    if not latest:
        return {"recommendations": [], "ranked_roles": []}
    resume = db.get(models.Resume, latest.resume_id)
    recs = db.query(models.Recommendation).filter_by(match_id=latest.id).all()
    return {"match_id": latest.id, "recommendations": [{"kind": r.kind, "text": r.text} for r in recs],
            "ranked_roles": rank_jobs(resume.raw_text, resume.parsed, sample_jobs())}
