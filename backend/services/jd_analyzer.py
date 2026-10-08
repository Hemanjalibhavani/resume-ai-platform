"""Job-description analysis: title, required/preferred skills, education, experience, duties."""
import re

from backend.services.resume_parser import degree_level, extract_text
from backend.services.skill_extractor import category_of, extract_skills, extract_soft_skills
from backend.utils.helpers import AppError
from backend.utils.text_cleaner import clean_text

PREFERRED_MARKERS = ("preferred", "nice to have", "good to have", "bonus", "desired", "a plus", "plus:", "optional")
REQUIRED_MARKERS = ("requirements", "required", "qualifications", "must have", "must-have", "what you need",
                    "what you'll need", "skills", "you have", "eligibility")
RESP_MARKERS = ("responsibilities", "what you'll do", "what you will do", "duties", "role overview", "the role")


def _mode_for(line: str, current: str):
    low = line.lower().strip().rstrip(":")
    if len(low) > 70:
        return current, line
    for m in PREFERRED_MARKERS:
        if low.startswith(m) or (low.endswith(m) and len(low) < 45):
            return "preferred", line.split(":", 1)[1] if ":" in line else ""
    for m in RESP_MARKERS:
        if low.startswith(m):
            return "resp", line.split(":", 1)[1] if ":" in line else ""
    for m in REQUIRED_MARKERS:
        if low.startswith(m) or low.endswith(m):
            return "required", line.split(":", 1)[1] if ":" in line else ""
    return current, line


def analyze_jd(text: str, title: str | None = None) -> dict:
    """Parse a job description into structured requirements."""
    text = clean_text(text)
    if not text:
        raise AppError("Please provide a job description.", 400)
    lines = [l for l in text.split("\n") if l.strip()]
    found_title = title
    if not found_title:
        m = re.search(r"(?im)^\s*(?:job title|role|position|title)\s*[:\-]\s*(.+)$", text)
        found_title = m.group(1).strip() if m else (lines[0].strip()[:90] if len(lines[0]) <= 90 else "Untitled role")
    mode, req_txt, pref_txt, resp = "required", [], [], []
    for line in lines:
        mode, rest = _mode_for(line, mode)
        content = rest if rest is not line and rest != line else line
        if content is line or content == line:
            (pref_txt if mode == "preferred" else req_txt).append(line)
            if mode == "resp" and re.match(r"^\s*[-*]", line):
                resp.append(re.sub(r"^\s*[-*]\s*", "", line))
        elif content.strip():
            (pref_txt if mode == "preferred" else req_txt).append(content)
    req_sk, pref_sk = extract_skills("\n".join(req_txt)), extract_skills("\n".join(pref_txt))
    pref_only = {k: v for k, v in pref_sk.items() if k not in req_sk}
    if not resp:
        resp = [re.sub(r"^\s*[-*]\s*", "", l) for l in lines if re.match(r"^\s*[-*]\s", l)][:8]
    exp_years, low = 0.0, text.lower()
    for m in re.finditer(r"(\d+)\s*(?:\+|-\s*\d+|to\s*\d+)?\s*years?", low):
        if "experience" in low[max(0, m.start() - 60): m.end() + 60]:
            exp_years = float(m.group(1)); break
    if re.search(r"fresher|entry[- ]level|graduate|0\s*-\s*1\s*years?", low) and exp_years > 2:
        exp_years = 0.0
    level = 2 if re.search(r"bachelor|b\.?\s?tech|\bb\.?e\b|b\.?sc|undergraduate|engineering degree", text, re.I) else degree_level(text)
    edu = {0: "Not specified", 1: "Diploma", 2: "Bachelor's degree", 3: "Master's degree", 4: "Doctorate"}[level]
    all_sk = {**req_sk, **pref_only}
    return {
        "title": found_title,
        "required_skills": sorted(req_sk),
        "preferred_skills": sorted(pref_only),
        "languages": sorted(k for k in all_sk if category_of(k) == "language"),
        "frameworks": sorted(k for k in all_sk if category_of(k) == "framework"),
        "tools": sorted(k for k in all_sk if category_of(k) == "cloud_tool"),
        "databases": sorted(k for k in all_sk if category_of(k) == "database"),
        "cloud": sorted(k for k in all_sk if k in ("aws", "azure", "gcp", "kubernetes", "docker", "terraform")),
        "soft_skills": extract_soft_skills(text),
        "education_requirement": edu, "education_level": level,
        "experience_years": exp_years,
        "responsibilities": resp[:10],
        "skill_details": {k: {"category": v["category"], "required": k in req_sk} for k, v in all_sk.items()},
    }


def jd_from_file(data: bytes, filename: str) -> str:
    return extract_text(data, filename)
