"""Database helpers shared by the routes (create/load resumes, jobs, matches)."""
from sqlalchemy.orm import Session

from backend import models
from backend.services.jd_analyzer import analyze_jd
from backend.services.resume_analyzer import completeness
from backend.services.resume_parser import parse_resume
from backend.utils.helpers import AppError


def get_resume(db: Session, resume_id: int) -> models.Resume:
    r = db.get(models.Resume, resume_id)
    if not r:
        raise AppError("Please upload a resume before running job matching.", 404)
    return r


def get_job(db: Session, job_id: int) -> models.Job:
    j = db.get(models.Job, job_id)
    if not j:
        raise AppError("Please provide a job description.", 404)
    return j


def get_match(db: Session, match_id: int) -> models.MatchResult:
    m = db.get(models.MatchResult, match_id)
    if not m:
        raise AppError("Match result not found.", 404)
    return m


def save_resume(db: Session, text: str, filename: str) -> models.Resume:
    """Parse text and persist the resume, its sections and skills."""
    parsed = parse_resume(text)
    comp = completeness(parsed)
    c = parsed["contact"]
    resume = models.Resume(filename=filename, raw_text=text, candidate_name=c["name"], email=c["email"],
                           phone=c["phone"], completeness_score=comp["score"],
                           parsed={**parsed, "completeness": comp})
    resume.sections = [models.ResumeSection(name=k, content=v) for k, v in parsed["sections"].items()]
    resume.skills = [models.ResumeSkill(skill=k, category=v["category"], mentions=v["mentions"])
                     for k, v in parsed["skills"].items()]
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def save_job(db: Session, text: str, title: str | None = None) -> models.Job:
    parsed = analyze_jd(text, title)
    job = models.Job(title=parsed["title"], raw_text=text, parsed=parsed)
    job.skills = [models.JobSkill(skill=k, category=v["category"], required=v["required"])
                  for k, v in parsed["skill_details"].items()]
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def resume_view(r: models.Resume) -> dict:
    p = r.parsed
    return {"id": r.id, "filename": r.filename, "candidate_name": r.candidate_name, "email": r.email,
            "phone": r.phone, "linkedin": p["contact"].get("linkedin", ""), "github": p["contact"].get("github", ""),
            "education": p["education"], "skills": p["skills"], "projects": p["projects"],
            "internships": p["internships"], "experience": p["experience"],
            "certifications": p["certifications"], "achievements": p["achievements"],
            "years_experience": p["years_experience"], "sections_detected": p["sections_detected"],
            "completeness": p["completeness"], "created_at": r.created_at.isoformat()}


def job_view(j: models.Job) -> dict:
    return {"id": j.id, "created_at": j.created_at.isoformat(), **j.parsed}
