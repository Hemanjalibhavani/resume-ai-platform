try:
    import pymupdf as fitz
except ImportError:
    import fitz
import pytest

from backend.services.resume_parser import detect_sections, extract_contact, extract_text, parse_resume
from backend.services.skill_extractor import extract_skills, is_basic_level
from backend.utils.file_validator import sanitize_filename, validate_upload
from backend.utils.helpers import AppError
from tests.conftest import SAMPLE


def test_contact_extraction():
    c = extract_contact(SAMPLE, SAMPLE.split("Professional Summary")[0])
    assert c["name"] == "Gandikota Hemanjali Bhavani"
    assert "@" in c["email"]
    assert sum(ch.isdigit() for ch in c["phone"]) >= 10


def test_section_detection():
    sections = detect_sections(SAMPLE)
    for key in ("education", "skills", "projects", "internships", "certifications", "summary", "extracurricular"):
        assert key in sections


def test_skill_extraction_aliases_and_special_chars():
    found = extract_skills("Worked with sklearn, Node.js, C++ and CI/CD pipelines using Postgres. Go to market.")
    assert {"scikit-learn", "node.js", "c++", "ci/cd", "postgresql"} <= set(found)
    assert "go" not in found  # the plain English word must not match the Go language


def test_basic_level_detection():
    assert is_basic_level("Skills: Java basics, Python", "java")
    assert not is_basic_level("Skills: Java, Python", "java")


def test_parse_resume_structure():
    parsed = parse_resume(SAMPLE)
    assert [p["title"] for p in parsed["projects"]][1:] == ["Interactive Quiz Game", "Blog Platform Website"]
    assert len(parsed["projects"]) == 3 and "XGBoost" in parsed["projects"][0]["description"]
    assert parsed["education_level"] == 2
    assert {"python", "fastapi", "docker", "xgboost"} <= set(parsed["skills"])


def test_internship_duration_and_certifications_split():
    parsed = parse_resume(SAMPLE)
    assert len(parsed["internships"]) == 1 and parsed["years_experience"] == 0.25
    assert len(parsed["certifications"]) == 8 and "Web Development – AWS" in parsed["certifications"]


def test_pdf_text_extraction():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Jane Doe\njane@example.com\nSKILLS\nPython, SQL, Docker and FastAPI experience for backend work")
    text = extract_text(doc.tobytes(), "resume.pdf")
    assert "jane@example.com" in text


def test_corrupted_pdf_rejected():
    with pytest.raises(AppError) as e:
        extract_text(b"%PDF-1.4 garbage", "resume.pdf")
    assert "valid PDF" in e.value.message


def test_file_validation_rules():
    with pytest.raises(AppError):
        validate_upload("a.exe", b"data")
    with pytest.raises(AppError):
        validate_upload("a.pdf", b"")
    with pytest.raises(AppError):
        validate_upload("a.pdf", b"not a pdf")
    assert sanitize_filename("../../etc/pass wd.pdf") == "pass wd.pdf"
