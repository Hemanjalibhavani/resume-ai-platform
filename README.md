# AI-Powered Resume Screening & Job Matching System
A full-stack AI/ML application that parses resumes, analyses job descriptions, produces an **explainable** match score, finds skill gaps, answers career questions with **RAG**, and runs a scored mock interview.
Live demo:"https://resume-ai-platform-hets.onrender.com"

## Problem statement
Candidates rarely know why a resume is rejected, and keyword-only ATS filters miss semantically relevant profiles. This project combines NLP, embeddings and an LLM-optional assistant to tell a candidate *how well* they match a role, *why*, and *what to do next*.

## Objectives
- Parse PDF/DOCX resumes into structured data
- Match resume to job description with a hybrid, explainable score
- Detect matched / partial / missing skills with learning guidance
- Provide a grounded RAG career assistant and interview practice
- Work with **no API key** (local mode); use Gemini/OpenAI when configured

## Features
Resume parsing · completeness score · ATS estimate · bullet-point improvement · JD analyzer · hybrid matching with score breakdown · skill gap with priorities · multi-job ranking · RAG assistant · interview generation + evaluation · history · Chart.js dashboard · demo mode · SQLite persistence · Docker.

## Architecture
```
Browser (HTML/CSS/JS, Chart.js) --REST--> FastAPI routes --> services --> SQLite (SQLAlchemy)
                                                   |-- resume_parser / skill_extractor / jd_analyzer
                                                   |-- embedding_service (sentence-transformers+FAISS | TF-IDF)
                                                   |-- matching_engine / skill_gap_service
                                                   |-- rag_service --> llm_service (Gemini | OpenAI | none)
                                                   `-- interview_service / recommendation_service
```
FastAPI also serves the `frontend/` folder, so one process runs everything.

## Technology stack
Python, FastAPI, Pydantic, SQLAlchemy, SQLite, PyMuPDF, python-docx, scikit-learn (TF-IDF, cosine), optional sentence-transformers + FAISS, httpx (Gemini/OpenAI REST), HTML/CSS/JS, Chart.js, Docker, pytest.

## Folder structure
See the tree in this repository: `backend/{routes,services,utils,data}`, `frontend/{css,js}`, `tests/`, `docs/`.

## Installation
```bash
python -m venv venv
# Windows:  venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
# optional neural embeddings + FAISS (large):
pip install -r requirements-ai.txt
cp .env.example .env     # Windows: copy .env.example .env
```

## Environment variables
| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | Optional LLM (server-side only, never sent to the browser) |
| `DATABASE_URL` | default `sqlite:///./resume_ai.db` |
| `VECTOR_DB_PATH` | default `./vector_store` |
| `EMBEDDING_BACKEND` | `auto`, `sentence-transformers` or `tfidf` |
| `MAX_UPLOAD_MB`, `CORS_ORIGINS` | upload limit, allowed origins |

## Demo data
`backend/data/sample_resume.txt` is the project author's resume and powers **Try Demo**. If you publish the repository, replace it with a version without your phone number and email.

## Run
```bash
uvicorn backend.main:app --reload
```
Open http://localhost:8000 (frontend + API) and http://localhost:8000/docs (Swagger). To run the frontend separately, open `frontend/index.html` (it calls `http://localhost:8000`).

## API documentation
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/resume/upload` | upload + parse PDF/DOCX |
| POST | `/api/resume/demo` | load bundled sample resume |
| GET | `/api/resume/{id}`, `/api/resumes` | fetch / list resumes |
| POST | `/api/resume/analyze` | ATS estimate + bullet improvements |
| POST | `/api/job/analyze`, `/api/job/upload` | analyse a JD (text / file) |
| GET/POST | `/api/job/samples`, `/api/job/samples/{id}` | 5 sample JDs |
| POST | `/api/match` | run matching |
| GET | `/api/match/{id}` | stored match |
| POST | `/api/match/rank` | rank multiple jobs |
| GET | `/api/skills/gap/{match_id}` | skill gap report |
| POST | `/api/assistant/chat` | RAG assistant |
| POST | `/api/interview/generate`, `/evaluate` | questions / scoring |
| GET | `/api/history`, `/api/dashboard`, `/api/recommendations`, `/api/health` | analytics |

## Database
SQLite + SQLAlchemy 2: `users, resumes, resume_sections, resume_skills, jobs, job_skills, match_results, skill_gaps, chat_history, interview_sessions, interview_questions, recommendations`. All data belongs to a default user (id 1) so authentication can be added later without schema changes.

## AI architecture
1. **Traditional NLP** – regex, a 90+ skill dictionary with aliases, section detection, TF-IDF.
2. **Semantic AI** – sentence-transformer embeddings + cosine similarity (TF-IDF cosine fallback).
3. **Generative AI** – Gemini/OpenAI for rewriting, answering, evaluating (optional).
4. **Match score (100)** = Skills 35 + Semantic 30 + Experience 15 + Projects 10 + Education 5 + Soft skills 5; each component returns points and a reason.

## RAG architecture
Documents (resume, JD, skill profile, gaps, recommendations, interview history) → chunking → embeddings → vector search (FAISS, or NumPy/TF-IDF) → top-k context → LLM prompt that must answer only from context, else: *"I couldn't find this information in the uploaded documents."* Without an LLM key, answers are produced by deterministic rules over the same stored analysis (labelled "local" mode).

## Screenshots
Add screenshots to `docs/screenshots/` (landing, dashboard, match result, skill gap, assistant, interview).

## Testing
```bash
pytest -q
```
22 tests cover parsing, skill extraction, file validation, matching, skill gap, ranking and the API end to end.

## Docker
```bash
docker compose up --build
```
Use `--build-arg INSTALL_AI=true` (edit compose args) to include sentence-transformers + FAISS.

## Deployment (Render)
Push to GitHub → New Web Service → Docker (uses `render.yaml`) → set `GEMINI_API_KEY` if desired. The free tier has 512 MB RAM, so keep `EMBEDDING_BACKEND=tfidf` there. SQLite on Render's free tier is ephemeral; use PostgreSQL for persistence.

## Limitations
- Rule-based parsing can misread unusual resume layouts and scanned/image PDFs (no OCR)
- ATS score is a heuristic estimate, not any company's real ATS
- Skill dictionary covers ~94 skills; unknown skills are not detected
- Local-mode assistant/evaluator is rule-based and less nuanced than an LLM
- Authentication is not implemented (single default user)

## Future enhancements
LinkedIn profile analysis · job scraping via permitted APIs · multi-resume comparison · recruiter dashboard & candidate ranking · multi-agent career assistant · PostgreSQL · authentication · resume version tracking · real-time job recommendations · personalised learning roadmap.

## Author
Gandikota Hemanjali Bhavani · B.Tech AI & ML (2023–2027) · Ramachandra College of Engineering, Vatluru · add your GitHub / LinkedIn links
