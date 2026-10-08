"""Pydantic request schemas (responses are plain validated dicts)."""
from pydantic import BaseModel, Field


class ResumeAnalyzeRequest(BaseModel):
    resume_id: int
    job_id: int | None = None


class JobAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Job description text")
    title: str | None = None


class MatchRequest(BaseModel):
    resume_id: int
    job_id: int


class RankRequest(BaseModel):
    resume_id: int
    job_ids: list[int] | None = None
    include_samples: bool = False


class ChatRequest(BaseModel):
    resume_id: int
    question: str = Field(..., min_length=1, max_length=1000)
    match_id: int | None = None


class InterviewGenerateRequest(BaseModel):
    resume_id: int
    job_id: int | None = None
    categories: list[str] | None = None
    count: int = Field(12, ge=1, le=40)
    with_answers: bool = False


class InterviewEvaluateRequest(BaseModel):
    question_id: int
    answer: str = Field(..., min_length=1, max_length=5000)
