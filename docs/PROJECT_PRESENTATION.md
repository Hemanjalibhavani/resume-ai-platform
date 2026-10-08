# Project Presentation Guide

## A. 30-second explanation
"I built an AI resume screening and job matching platform. You upload a resume and a job description; it extracts skills with NLP, compares them using keyword and semantic embeddings, gives an explainable match score, shows skill gaps with a learning plan, and includes a RAG assistant and interview practice. It runs on FastAPI and works even without an LLM key."

## B. 1-minute explanation
The backend parses PDF/DOCX with PyMuPDF, detects sections and extracts skills using regex and a skill dictionary. A job-description analyzer separates required and preferred skills. The matching engine mixes six signals — skills (35), semantic similarity (30), experience (15), projects (10), education (5), soft skills (5) — and explains every component. Skill gaps get priority, why-it-matters, topics and a project. A RAG assistant retrieves chunks from the candidate's own documents and either sends them to Gemini/OpenAI or answers locally. Everything is stored in SQLite via SQLAlchemy, shipped in Docker, and deployable on Render.

## C. Architecture
Frontend (HTML/JS/Chart.js) → FastAPI routes → service layer (parser, extractor, matching, gap, RAG, LLM, interview) → SQLite. The `llm_service` is optional; `embedding_service` falls back from sentence-transformers to TF-IDF so the app always starts.

## D. Technologies
FastAPI (async REST, auto docs, Pydantic validation) · SQLAlchemy/SQLite (ORM) · PyMuPDF/python-docx (text extraction) · scikit-learn (TF-IDF, cosine) · sentence-transformers + FAISS (semantic search, optional) · Gemini/OpenAI (generation, optional) · Chart.js · Docker · pytest.

## E. 15 interview questions
1. **What does the project do?** Matches resumes to jobs, explains the score, finds skill gaps, answers questions via RAG, practises interviews.
2. **Why not only keyword matching?** It misses synonyms and context ("ML" vs "machine learning"); embeddings capture meaning, and a skill dictionary with aliases handles exact skills.
3. **How is the score calculated?** Weighted sum of six components totalling 100; each returns points plus a reason string.
4. **What is cosine similarity?** The cosine of the angle between two vectors; 1 = same direction (similar meaning), 0 = unrelated.
5. **What are embeddings?** Dense numeric vectors where similar meanings are close together.
6. **What is RAG?** Retrieve relevant chunks from your documents, then give them to the LLM as context so answers are grounded.
7. **Why RAG over fine-tuning?** Cheaper, data stays fresh (new resume = new context), reduces hallucination, no training needed.
8. **What is a vector database/index?** Stores embeddings for fast nearest-neighbour search; I use FAISS (or NumPy) for it.
9. **How do you reduce hallucination?** Answer only from retrieved context, fixed "not found" reply, source snippets shown.
10. **What happens without an API key?** Local mode: TF-IDF similarity, rule-based assistant and evaluator; the UI shows "local analysis mode".
11. **How do you handle partial skill matches?** Related-skill map (Flask↔FastAPI) and "basics" detection (Java basics) give 50% credit.
12. **Why FastAPI?** Fast, typed, Pydantic validation, automatic Swagger docs, easy async.
13. **How is file upload secured?** Extension + size + magic-byte checks, filename sanitisation, friendly errors.
14. **How did you test it?** 22 pytest tests: parser, extractor, validator, matching, gaps, ranking, API flow.
15. **How would you scale it?** PostgreSQL, a task queue for parsing, a hosted vector DB, caching embeddings, authentication.

## F. Why RAG?
It lets the assistant answer from the candidate's own data and admit when information is missing.

## G. Why embeddings?
They measure meaning, not just words, so related experience still scores.

## H. Why a vector database?
Fast similarity search over many chunks; FAISS gives exact inner-product search in memory with an easy path to scale.

## I. Why FastAPI?
Type hints → validation + docs for free, excellent performance, clean dependency injection for DB sessions.

## J. How the matching score is calculated
Skills 35 (required 80%/preferred 20%, partial = 0.5) + Semantic 30 (cosine, calibrated per backend) + Experience 15 + Projects 10 (skill overlap + similarity) + Education 5 + Soft skills 5.

## K. Biggest technical challenge
Making the score trustworthy: separating required from preferred skills, handling aliases/partial knowledge, and calibrating cosine similarity, which behaves differently for TF-IDF and neural embeddings.

## L. Limitations
Rule-based parsing on odd layouts, no OCR, heuristic ATS score, finite skill dictionary, no authentication.

## M. Future improvements
Auth + PostgreSQL, OCR, resume versioning, recruiter ranking, learning roadmaps, LLM-based parsing fallback, evaluation dataset for the score.

## N. Resume bullets
- Built a full-stack AI resume screening platform (FastAPI, SQLAlchemy, Docker) that parses PDF/DOCX resumes and matches them to job descriptions using a hybrid keyword + embedding score with per-component explanations.
- Implemented a RAG career assistant with chunking, embeddings, FAISS/TF-IDF retrieval and grounded LLM prompts, plus a local fallback so the system runs without paid APIs.
- Designed skill-gap analysis, interview generation/scoring and a Chart.js analytics dashboard, backed by 22 pytest tests and Render-ready deployment.

## O. GitHub description
AI-powered resume screening & job matching: explainable match scores, skill-gap analysis, RAG career assistant and interview practice. FastAPI · NLP · embeddings · RAG · SQLite · Docker.

## P. Demo flow
Landing → Try Demo → match result with score breakdown → Skill Gap page → ask the assistant "What should I learn first?" → generate interview questions → practise one answer → Dashboard and History.
