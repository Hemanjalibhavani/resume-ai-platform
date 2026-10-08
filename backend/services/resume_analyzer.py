"""Resume completeness score, estimated ATS score and bullet-point improvement."""
import re

from backend.services import llm_service
from backend.services.skill_extractor import extract_skills
from backend.utils.text_cleaner import word_count

WEAK_VERBS = {"worked on": "Developed", "responsible for": "Owned", "helped": "Contributed to",
              "did": "Executed", "made": "Built", "involved in": "Contributed to", "handled": "Managed",
              "assisted": "Supported", "participated in": "Contributed to", "tried": "Explored"}
STRONG_VERBS = ("developed", "built", "designed", "implemented", "created", "engineered", "deployed",
                "optimized", "trained", "automated", "led", "improved", "analyzed", "integrated")


def completeness(parsed: dict) -> dict:
    """Resume completeness score out of 100 with detected/missing sections."""
    c, s = parsed["contact"], parsed["sections"]
    checks = [
        ("Contact", 15, bool(c["email"]) and bool(c["phone"])),
        ("Education", 15, bool(parsed["education"])),
        ("Skills", 20, bool(parsed["skills"])),
        ("Projects", 20, bool(parsed["projects"])),
        ("Internship / Experience", 15, bool(parsed["internships"] or parsed["experience"])),
        ("Certifications", 5, bool(parsed["certifications"])),
        ("Summary / Objective", 5, "summary" in s or "objective" in s),
        ("Achievements", 5, bool(parsed["achievements"])),
    ]
    score = sum(w for _, w, ok in checks if ok)
    return {"score": score, "detected": [n for n, _, ok in checks if ok],
            "missing": [n for n, _, ok in checks if not ok]}


def ats_score(text: str, parsed: dict, jd_parsed: dict | None = None) -> dict:
    """Estimated ATS compatibility (heuristic; NOT any company's real ATS)."""
    issues, tips = [], []
    # 1. keyword relevance (35)
    if jd_parsed:
        wanted = set(jd_parsed["required_skills"]) | set(jd_parsed["preferred_skills"])
        have = set(parsed["skills"])
        kw = 35 * (len(wanted & have) / len(wanted)) if wanted else 35
        missing_kw = sorted(wanted - have)
        if missing_kw:
            issues.append("Missing job keywords: " + ", ".join(missing_kw[:8]))
    else:
        kw = 35 * min(1.0, len(parsed["skills"]) / 12)
        tips.append("Add a job description to get job-specific keyword analysis.")
        missing_kw = []
    # 2. section structure (25)
    core = ["education", "skills", "projects"]
    present = sum(1 for k in core if k in parsed["sections"])
    structure = 25 * (present + (1 if parsed["internships"] or parsed["experience"] else 0)) / 4
    if present < 3:
        issues.append("Use standard section headings: Education, Skills, Projects.")
    # 3. readability (15)
    words = word_count(text)
    readability = 15
    if words < 200:
        readability -= 8; issues.append("Resume looks very short (under 200 words).")
    elif words > 1100:
        readability -= 5; issues.append("Resume is long; aim for one page for freshers.")
    # 4. contact (10)
    contact = 5 * bool(parsed["contact"]["email"]) + 5 * bool(parsed["contact"]["phone"])
    if contact < 10:
        issues.append("Add a visible email and phone number.")
    # 5. formatting (15)
    fmt = 15
    bullets = len(re.findall(r"^\s*[-*]\s", text, re.M))
    if bullets < 4:
        fmt -= 6; issues.append("Use bullet points to describe projects and experience.")
    if re.search(r"[^\x00-\x7F]{5,}", text):
        fmt -= 4; issues.append("Unusual symbols detected; ATS parsers may misread them.")
    if not parsed["contact"]["linkedin"] and not parsed["contact"]["github"]:
        fmt -= 2; tips.append("Add LinkedIn / GitHub links.")
    total = round(kw + structure + readability + contact + fmt)
    return {"score": min(100, total), "label": "Estimated ATS compatibility score",
            "breakdown": {"keyword_relevance": [round(kw), 35], "section_structure": [round(structure), 25],
                          "readability": [readability, 15], "contact_info": [contact, 10],
                          "formatting": [fmt, 15]},
            "missing_keywords": missing_kw, "issues": issues, "tips": tips,
            "disclaimer": "Heuristic estimate only; it does not represent any specific company's ATS."}


def _bullets(parsed: dict) -> list[str]:
    out = []
    for key in ("projects", "internships", "experience"):
        for e in parsed[key]:
            desc = e["description"] or e["title"]
            out.extend([s.strip() for s in re.split(r"(?<=[.!?])\s+", desc) if len(s.strip()) > 3])
    return out


def improve_bullets(parsed: dict, jd_parsed: dict | None = None, limit: int = 8) -> list[dict]:
    """Detect weak bullets and suggest rewrites (LLM when configured, rules otherwise)."""
    results = []
    for b in _bullets(parsed):
        issues = []
        low = b.lower()
        weak = next((w for w in WEAK_VERBS if low.startswith(w) or f" {w} " in f" {low} "), None)
        if weak:
            issues.append(f'Weak phrase "{weak}"')
        if not re.search(r"\d", b):
            issues.append("No measurable result")
        if len(b.split()) < 8:
            issues.append("Too generic / short")
        if not any(low.startswith(v) for v in STRONG_VERBS) and not weak:
            issues.append("Does not start with a strong action verb")
        if issues:
            results.append({"original": b, "issues": issues, "suggested": _rewrite(b, weak, jd_parsed)})
    return results[:limit]


def _rewrite(bullet: str, weak: str | None, jd_parsed: dict | None) -> str:
    if llm_service.is_available():
        kws = ", ".join((jd_parsed or {}).get("required_skills", [])[:8])
        out = llm_service.generate(
            f"Rewrite this resume bullet to be specific, start with a strong action verb and include a "
            f"measurable result placeholder in [brackets] if no number exists. Use job keywords only if truthful: "
            f"{kws}. Return only the bullet.\n\nBullet: {bullet}", system="You are an expert resume writer.")
        if out:
            return out.strip()
    text = bullet.rstrip(".")
    if weak:
        text = re.sub(re.escape(weak), WEAK_VERBS[weak].lower(), text, count=1, flags=re.I)
    text = text[0].upper() + text[1:]
    if not text.split()[0].lower() in STRONG_VERBS and not weak:
        text = "Developed " + text[0].lower() + text[1:]
    tech = ", ".join(display for display in list(extract_skills(bullet))[:3])
    extra = f" using {tech}" if tech and tech.split(",")[0].lower() not in text.lower() else ""
    metric = "" if re.search(r"\d", text) else ", achieving [metric, e.g. accuracy / users / time saved]"
    return f"{text}{extra}{metric}."
