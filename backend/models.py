"""ORM models. Auth-ready: every resume/job belongs to a user (default user id=1)."""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, default="demo@example.com")
    name: Mapped[str] = mapped_column(String(120), default="Demo User")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), default=1)
    filename: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    candidate_name: Mapped[str] = mapped_column(String(160), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    completeness_score: Mapped[int] = mapped_column(Integer, default=0)
    parsed: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    sections = relationship("ResumeSection", cascade="all, delete-orphan")
    skills = relationship("ResumeSkill", cascade="all, delete-orphan")


class ResumeSection(Base):
    __tablename__ = "resume_sections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"))
    name: Mapped[str] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text)


class ResumeSkill(Base):
    __tablename__ = "resume_skills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"))
    skill: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(40), default="other")
    mentions: Mapped[int] = mapped_column(Integer, default=1)


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), default=1)
    title: Mapped[str] = mapped_column(String(200), default="Untitled role")
    raw_text: Mapped[str] = mapped_column(Text)
    parsed: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    skills = relationship("JobSkill", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    skill: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(40), default="other")
    required: Mapped[bool] = mapped_column(Boolean, default=True)


class MatchResult(Base):
    __tablename__ = "match_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"))
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class SkillGap(Base):
    __tablename__ = "skill_gaps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("match_results.id"))
    skill: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20))  # missing | partial
    priority: Mapped[str] = mapped_column(String(10), default="MEDIUM")
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"))
    role: Mapped[str] = mapped_column(String(12))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"))
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    questions = relationship("InterviewQuestion", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id"))
    category: Mapped[str] = mapped_column(String(40))
    question: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(10), default="Medium")
    expected_concepts: Mapped[list] = mapped_column(JSON, default=list)
    follow_ups: Mapped[list] = mapped_column(JSON, default=list)
    sample_answer: Mapped[str] = mapped_column(Text, default="")
    answer: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[dict] = mapped_column(JSON, default=dict)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("match_results.id"))
    kind: Mapped[str] = mapped_column(String(30))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
