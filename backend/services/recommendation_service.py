"""Career recommendations and multi-job ranking."""
from backend.services.jd_analyzer import analyze_jd
from backend.services.matching_engine import compute_match, label_for
from backend.services.skill_extractor import display_name
from backend.utils.helpers import load_json


def sample_jobs() -> list[dict]:
    return load_json("sample_jobs.json")


def rank_jobs(resume_text: str, resume: dict, jobs: list[dict]) -> list[dict]:
    """Rank jobs [{id?, title, text}] by match score with per-job preparation advice."""
    rows = []
    for j in jobs:
        jd = analyze_jd(j["text"], j.get("title"))
        m = compute_match(resume_text, resume, j["text"], jd)
        miss = [display_name(s) for s in m["missing_skills"]]
        rows.append({"job_id": j.get("id"), "title": jd["title"], "score": m["score"], "label": label_for(m["score"]),
                     "matched": [display_name(s) for s in m["matched_skills"]], "missing": miss,
                     "partial": [display_name(p["skill"]) for p in m["partial_skills"]],
                     "preparation": ("Prioritise: " + ", ".join(miss[:3])) if miss else "Polish projects and prepare interview answers."})
    return sorted(rows, key=lambda r: -r["score"])


def career_recommendations(match: dict, gaps: list[dict], ranked: list[dict]) -> list[dict]:
    """Turn analysis into actionable recommendation items."""
    recs = []
    for g in gaps[:3]:
        recs.append({"kind": "learn", "text": f"Learn {g['display']} ({g['priority']} priority): {', '.join(g['learn'][:3])}."})
    for g in gaps[:2]:
        recs.append({"kind": "project", "text": f"Add a project: {g['project']}"})
    for w in match["weaknesses"][:2]:
        recs.append({"kind": "improve", "text": w})
    if ranked:
        top = ranked[0]
        recs.append({"kind": "role", "text": f"Best-matching role right now: {top['title']} ({top['score']}%)."})
    return recs
