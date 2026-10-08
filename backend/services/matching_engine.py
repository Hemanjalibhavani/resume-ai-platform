"""Hybrid, explainable resume <-> job matching engine.

Score (100) = Skills 35 + Semantic 30 + Experience 15 + Projects 10 + Education 5 + Soft skills 5
"""
from backend.services.embedding_service import embedding_service
from backend.services.skill_extractor import display_name, extract_skills, is_basic_level, related_skills
from backend.utils.helpers import clamp

WEIGHTS = {"skills": 35, "semantic": 30, "experience": 15, "projects": 10, "education": 5, "soft_skills": 5}


def classify_skills(resume_text: str, resume_skills: dict, wanted: list[str]) -> dict:
    """Split wanted skills into matched / partial / missing with a reason for each partial."""
    matched, partial, missing = [], [], []
    for sk in wanted:
        if sk in resume_skills:
            if is_basic_level(resume_text, sk):
                partial.append({"skill": sk, "reason": "Only basic-level knowledge shown on the resume"})
            else:
                matched.append(sk)
            continue
        rel = [r for r in related_skills(sk) if r in resume_skills]
        if rel:
            partial.append({"skill": sk, "reason": "Related skill found: " + ", ".join(display_name(r) for r in rel)})
        else:
            missing.append(sk)
    return {"matched": matched, "partial": partial, "missing": missing}


def _skill_ratio(cls: dict, total: int) -> float:
    return (len(cls["matched"]) + 0.5 * len(cls["partial"])) / total if total else 0.0


def compute_match(resume_text: str, resume: dict, jd_text: str, jd: dict) -> dict:
    """Compute the weighted match score with a human-readable explanation of each component."""
    rs = resume["skills"]
    req, pref = jd["required_skills"], jd["preferred_skills"]
    cls_req = classify_skills(resume_text, rs, req)
    cls_pref = classify_skills(resume_text, rs, pref)
    comp: dict[str, dict] = {}

    # 1. skills (required 80%, preferred 20%)
    if req or pref:
        if req and pref:
            ratio = 0.8 * _skill_ratio(cls_req, len(req)) + 0.2 * _skill_ratio(cls_pref, len(pref))
        else:
            ratio = _skill_ratio(cls_req, len(req)) if req else _skill_ratio(cls_pref, len(pref))
        reason = (f"{len(cls_req['matched'])}/{len(req)} required skills matched, "
                  f"{len(cls_req['partial'])} partial, {len(cls_req['missing'])} missing")
    else:
        ratio, reason = 0.0, "No recognisable skills found in the job description"
    comp["skills"] = (ratio, reason)

    # 2. semantic similarity
    sim = embedding_service.similarity(resume_text, jd_text)
    comp["semantic"] = (clamp(sim / embedding_service.calibration),
                        f"Cosine similarity {sim:.2f} using {embedding_service.name} embeddings")

    # 3. experience
    need, have = jd["experience_years"], resume.get("years_experience", 0.0)
    has_practical = bool(resume["internships"] or resume["experience"])
    if need <= 0:
        er = 1.0 if has_practical else 0.75
        ereason = "Role is entry level" + ("; internship/experience present" if has_practical else "; no internship listed")
    else:
        er = clamp((have + (0.25 if resume["projects"] else 0)) / need)
        ereason = f"{have:g} year(s) shown vs {need:g} required"
    comp["experience"] = (er, ereason)

    # 4. project relevance
    projects = resume["projects"]
    if projects:
        ptxt = " ".join(p["title"] + " " + p["description"] for p in projects)
        psk = set(extract_skills(ptxt))
        wanted = set(req) | set(pref)
        direct = len(psk & wanted)
        related = sum(1 for w in wanted - psk if any(r in psk for r in related_skills(w)))
        overlap = (direct + 0.5 * related) / len(wanted) if wanted else 0.0
        psim = clamp(embedding_service.similarity(ptxt, " ".join(jd["responsibilities"]) + " " + jd_text)
                     / embedding_service.calibration)
        pr = clamp(0.6 * clamp(overlap * 3) + 0.4 * psim)
        preason = f"{len(projects)} project(s); {direct} job skills (+{related} related) demonstrated in projects"
    else:
        pr, preason = 0.0, "No projects detected"
    comp["projects"] = (pr, preason)

    # 5. education
    need_lvl, have_lvl = jd["education_level"], resume.get("education_level", 0)
    if need_lvl == 0:
        edr, edreason = 1.0, "No specific degree required"
    elif have_lvl >= need_lvl:
        edr, edreason = 1.0, f"Meets requirement: {jd['education_requirement']}"
    elif have_lvl == need_lvl - 1 and have_lvl > 0:
        edr, edreason = 0.5, f"Slightly below requirement: {jd['education_requirement']}"
    else:
        edr, edreason = 0.0, f"Degree requirement not met: {jd['education_requirement']}"
    comp["education"] = (edr, edreason)

    # 6. soft skills
    from backend.services.skill_extractor import extract_soft_skills
    jd_soft, r_soft = set(jd["soft_skills"]), set(extract_soft_skills(resume_text))
    if jd_soft:
        sr = len(jd_soft & r_soft) / len(jd_soft)
        sreason = f"{len(jd_soft & r_soft)}/{len(jd_soft)} soft skills evidenced"
    else:
        sr, sreason = 1.0, "No soft skills specified"
    comp["soft_skills"] = (sr, sreason)

    breakdown = {k: {"points": round(WEIGHTS[k] * v[0], 1), "max": WEIGHTS[k], "reason": v[1]} for k, v in comp.items()}
    score = round(sum(b["points"] for b in breakdown.values()))
    all_cls = {"matched": cls_req["matched"] + cls_pref["matched"],
               "partial": cls_req["partial"] + cls_pref["partial"],
               "missing": cls_req["missing"] + cls_pref["missing"]}
    strengths, weaknesses = _insights(breakdown, all_cls, resume)
    return {
        "score": score, "label": label_for(score), "breakdown": breakdown,
        "matched_skills": all_cls["matched"], "partial_skills": all_cls["partial"],
        "missing_skills": all_cls["missing"],
        "required_missing": cls_req["missing"],
        "skill_strength": skill_strength(rs, req + pref, all_cls),
        "strengths": strengths, "weaknesses": weaknesses,
        "embedding_backend": embedding_service.name,
        "explanation": f"Score {score}% = " + " + ".join(f"{k.replace('_', ' ')} {v['points']:g}/{v['max']}"
                                                          for k, v in breakdown.items()),
    }


def label_for(score: float) -> str:
    return "Best Match" if score >= 80 else "Recommended" if score >= 65 else "Needs Improvement"


def skill_strength(resume_skills: dict, wanted: list[str], cls: dict) -> dict:
    """Chart helper: matched = 70-100% (more mentions => stronger), partial = 50%, missing = 0%."""
    out = {}
    for sk in wanted:
        if sk in cls["matched"]:
            out[sk] = min(100, 70 + 10 * resume_skills.get(sk, {}).get("mentions", 1))
        elif any(p["skill"] == sk for p in cls["partial"]):
            out[sk] = 50
        else:
            out[sk] = 0
    return out


def _insights(breakdown: dict, cls: dict, resume: dict) -> tuple[list[str], list[str]]:
    strengths, weaknesses = [], []
    if cls["matched"]:
        strengths.append("Strong match on: " + ", ".join(display_name(s) for s in cls["matched"][:6]))
    if breakdown["projects"]["points"] >= 6:
        strengths.append("Projects are relevant to the role")
    if breakdown["semantic"]["points"] >= 18:
        strengths.append("Resume content is semantically close to the job description")
    if breakdown["education"]["points"] >= 5:
        strengths.append("Education requirement met")
    if cls["missing"]:
        weaknesses.append("Missing skills: " + ", ".join(display_name(s) for s in cls["missing"][:6]))
    if cls["partial"]:
        weaknesses.append("Only partial evidence for: " + ", ".join(display_name(p["skill"]) for p in cls["partial"][:5]))
    if breakdown["experience"]["points"] < 8:
        weaknesses.append("Limited experience compared with the requirement")
    if breakdown["projects"]["points"] < 4:
        weaknesses.append("Few projects demonstrate the required skills")
    if not (resume["internships"] or resume["experience"]):
        weaknesses.append("No internship or work experience section found")
    return strengths or ["Add more role-relevant detail to highlight strengths"], weaknesses or ["No major weaknesses detected"]
