from backend.services.embedding_service import embedding_service
from backend.services.jd_analyzer import analyze_jd
from backend.services.matching_engine import WEIGHTS, classify_skills, compute_match
from backend.services.recommendation_service import rank_jobs, sample_jobs
from backend.services.resume_parser import parse_resume
from backend.services.skill_gap_service import analyze_gaps
from tests.conftest import SAMPLE

ML_JD = sample_jobs()[3]["text"]


def test_jd_analysis_splits_required_and_preferred():
    jd = analyze_jd(sample_jobs()[1]["text"])
    assert "fastapi" in jd["required_skills"]
    assert "kubernetes" in jd["preferred_skills"] and "kubernetes" not in jd["required_skills"]
    assert jd["experience_years"] == 1.0


def test_weights_sum_to_100():
    assert sum(WEIGHTS.values()) == 100


def test_match_score_is_explained_and_consistent():
    resume, jd = parse_resume(SAMPLE), analyze_jd(ML_JD)
    m = compute_match(SAMPLE, resume, ML_JD, jd)
    assert 0 <= m["score"] <= 100
    assert abs(sum(b["points"] for b in m["breakdown"].values()) - m["score"]) <= 1
    assert all(b["reason"] for b in m["breakdown"].values())
    assert "python" in m["matched_skills"] and "pytorch" in m["missing_skills"] and "docker" in m["matched_skills"]


def test_partial_skill_from_basic_level_and_related():
    resume = parse_resume(SAMPLE)
    cls = classify_skills(SAMPLE, resume["skills"], ["java", "kubernetes", "flask", "numpy", "tensorflow"])
    partial = {p["skill"] for p in cls["partial"]}
    assert {"java", "kubernetes", "flask"} <= partial  # basics / related-skill credit
    assert "numpy" in cls["matched"] and "tensorflow" in cls["missing"]


def test_semantic_similarity_orders_relevant_text_higher():
    a = embedding_service.similarity("python machine learning model training", "machine learning with python")
    b = embedding_service.similarity("python machine learning model training", "cooking pasta recipe tomatoes")
    assert a > b


def test_skill_gap_priorities_and_advice():
    resume, jd = parse_resume(SAMPLE), analyze_jd(ML_JD)
    m = compute_match(SAMPLE, resume, ML_JD, jd)
    gaps = analyze_gaps(m, jd)
    torch = next(g for g in gaps if g["skill"] == "pytorch")
    assert torch["priority"] == "HIGH" and torch["learn"] and torch["project"]
    assert gaps[0]["priority"] == "HIGH"


def test_job_ranking_sorted_descending():
    ranked = rank_jobs(SAMPLE, parse_resume(SAMPLE), sample_jobs())
    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True) and len(ranked) == 5
