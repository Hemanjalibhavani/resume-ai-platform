"""RAG career assistant.

Pipeline: documents -> chunking -> embeddings -> vector search (FAISS/NumPy/TF-IDF) -> context -> LLM.
Without an API key the assistant answers deterministically from the same stored documents.
"""
from sqlalchemy.orm import Session

from backend import models
from backend.services import llm_service
from backend.services.embedding_service import embedding_service
from backend.services.resume_analyzer import improve_bullets
from backend.services.skill_extractor import display_name
from backend.services.skill_gap_service import analyze_gaps
from backend.utils.text_cleaner import chunk_text

NOT_FOUND = "I couldn't find this information in the uploaded documents."
MIN_SCORE = {"sentence-transformers": 0.25, "tfidf": 0.06}


def build_corpus(db: Session, resume: models.Resume, match: models.MatchResult | None) -> list[dict]:
    """Collect every knowledge source for the candidate as {source, text} chunks."""
    docs = [{"source": "resume", "text": c} for c in chunk_text(resume.raw_text)]
    p = resume.parsed
    docs.append({"source": "skill profile", "text": "Candidate skills: " + ", ".join(display_name(s) for s in p["skills"])})
    for pr in p["projects"]:
        docs.append({"source": "resume projects", "text": f"Project {pr['title']}: {pr['description']}"})
    if match:
        job = db.get(models.Job, match.job_id)
        res = match.result
        docs += [{"source": "job description", "text": c} for c in chunk_text(job.raw_text)]
        docs.append({"source": "match result", "text": f"Match score for {job.title}: {match.score:.0f}%. {res['explanation']}"})
        for k, v in res["breakdown"].items():
            docs.append({"source": "match result", "text": f"{k.replace('_', ' ')}: {v['points']}/{v['max']} - {v['reason']}"})
        docs.append({"source": "skill gap", "text": "Missing skills: " + (", ".join(display_name(s) for s in res["missing_skills"]) or "none")})
        for g in db.query(models.SkillGap).filter_by(match_id=match.id):
            d = g.details
            docs.append({"source": "skill gap", "text": f"{d['display']} ({g.status}, priority {g.priority}): {d['why']} Learn: {', '.join(d['learn'])}. Project: {d['project']}"})
        for r in db.query(models.Recommendation).filter_by(match_id=match.id):
            docs.append({"source": "recommendation", "text": r.text})
    for s in db.query(models.InterviewSession).filter_by(resume_id=resume.id):
        for q in s.questions:
            if q.score is not None:
                docs.append({"source": "interview history", "text": f"Interview question '{q.question}' scored {q.score}/10."})
    return docs


def _local_answer(question: str, resume: models.Resume, match: models.MatchResult | None, db: Session) -> str | None:
    """Rule-based answers grounded in stored analysis (used when no LLM key is set)."""
    q, p = question.lower(), resume.parsed
    need_match = "This needs a job match first. Please run Job Matching, then ask again."
    skills = ", ".join(display_name(s) for s in p["skills"]) or "none detected"
    if any(k in q for k in ("explain my resume", "summar", "about my resume", "who am i")):
        return (f"{resume.candidate_name} has {len(p['skills'])} detected skills ({skills}), {len(p['projects'])} project(s), "
                f"{len(p['internships'])} internship(s) and {len(p['certifications'])} certification(s). Resume completeness: "
                f"{resume.completeness_score}/100. Missing sections: {', '.join(p['completeness']['missing']) or 'none'}.")
    if any(k in q for k in ("improve my resume", "improve resume", "better resume", "resume improve")):
        tips = improve_bullets(p)
        out = ["Resume improvements:"] + [f"- Replace \"{t['original']}\" with: {t['suggested']}" for t in tips[:3]]
        if p["completeness"]["missing"]:
            out.append("- Add sections: " + ", ".join(p["completeness"]["missing"]))
        return "\n".join(out)
    if "interview" in q:
        return "Open the Interview Preparation page to generate personalised questions from your resume and job description; I can also help you plan answers for your projects."
    if not match:
        if any(k in q for k in ("missing", "score", "suitable", "learn", "project", "fit", "low")):
            return need_match
        return None
    res, job = match.result, db.get(models.Job, match.job_id)
    missing = [display_name(s) for s in res["missing_skills"]]
    gaps = db.query(models.SkillGap).filter_by(match_id=match.id).order_by(models.SkillGap.id).all()
    if any(k in q for k in ("missing", "skills am i", "lack")):
        return "You are missing: " + (", ".join(missing) or "nothing critical") + ". Partial: " + (
            ", ".join(display_name(x["skill"]) for x in res["partial_skills"]) or "none") + "."
    if any(k in q for k in ("why", "score", "low")):
        weakest = sorted(res["breakdown"].items(), key=lambda kv: kv[1]["points"] / kv[1]["max"])[:3]
        return f"Your match score for {job.title} is {match.score:.0f}%. Weakest areas: " + "; ".join(
            f"{k.replace('_', ' ')} {v['points']}/{v['max']} ({v['reason']})" for k, v in weakest)
    if "project" in q:
        ideas = [f"{g.details['display']}: {g.details['project']}" for g in gaps[:3]]
        return "Projects to add: " + (" | ".join(ideas) if ideas else "Your skills already cover this role; deepen existing projects with metrics.")
    if any(k in q for k in ("suitable", "fit", "apply", "qualified")):
        verdict = "a strong fit" if match.score >= 80 else "a reasonable fit with some gaps" if match.score >= 65 else "not yet a strong fit"
        return f"For {job.title} you are {verdict} ({match.score:.0f}%). Strengths: {'; '.join(res['strengths'][:2])}. Gaps: {'; '.join(res['weaknesses'][:2])}."
    if any(k in q for k in ("learn", "first", "priority", "roadmap")):
        top = gaps[:3]
        if not top:
            return "No major gaps found; focus on deepening projects."
        return "Learn in this order: " + "; ".join(f"{i + 1}. {g.details['display']} ({g.priority}) - {', '.join(g.details['learn'][:3])}" for i, g in enumerate(top))
    return None


def answer(db: Session, resume: models.Resume, question: str, match: models.MatchResult | None) -> dict:
    """Answer a question grounded in the candidate's documents."""
    docs = build_corpus(db, resume, match)
    ranked = embedding_service.rank(question, [d["text"] for d in docs], top_k=5)
    threshold = MIN_SCORE.get(embedding_service.name, 0.06)
    hits = [(docs[i], s) for i, s in ranked if s >= threshold]
    sources = [{"source": d["source"], "snippet": d["text"][:160], "score": round(s, 3)} for d, s in hits]
    if llm_service.is_available() and hits:
        context = "\n\n".join(f"[{d['source']}] {d['text']}" for d, _ in hits)
        prompt = (f"Answer ONLY using the context below. If the answer is not in the context, reply exactly: "
                  f"\"{NOT_FOUND}\"\n\nContext:\n{context}\n\nQuestion: {question}")
        text = llm_service.generate(prompt, system="You are a careful career assistant. Never invent candidate facts.")
        if text:
            return {"answer": text.strip(), "sources": sources, "mode": "llm"}
    local = _local_answer(question, resume, match, db)
    if local:
        return {"answer": local, "sources": sources, "mode": "local"}
    if hits:
        body = "\n".join(f"- ({d['source']}) {d['text'][:220]}" for d, _ in hits[:3])
        return {"answer": "Here is the most relevant information I found:\n" + body, "sources": sources, "mode": "local"}
    return {"answer": NOT_FOUND, "sources": [], "mode": llm_service.mode()}
