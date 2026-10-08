import fitz


def _demo(client):
    return client.post("/api/resume/demo").json()


def test_health_runs_in_local_mode(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["ai_mode"] == "local"


def test_pdf_upload_flow(client):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "John Smith\njohn@example.com 9876543210\nSKILLS\nPython SQL Docker FastAPI\nPROJECTS\nChat App\n- Built a chat API with FastAPI")
    r = client.post("/api/resume/upload", files={"file": ("cv.pdf", doc.tobytes(), "application/pdf")})
    assert r.status_code == 200 and "fastapi" in r.json()["skills"]


def test_invalid_upload_returns_friendly_error(client):
    r = client.post("/api/resume/upload", files={"file": ("cv.pdf", b"not a pdf", "application/pdf")})
    assert r.status_code == 400 and r.json()["detail"] == "Please upload a valid PDF resume."


def test_match_without_resume_message(client):
    r = client.post("/api/match", json={"resume_id": 9999, "job_id": 1})
    assert r.status_code == 404 and "upload a resume" in r.json()["detail"]


def test_empty_job_description_rejected(client):
    r = client.post("/api/job/analyze", json={"text": "   "})
    assert r.status_code == 400 and r.json()["detail"] == "Please provide a job description."


def test_full_flow_match_gap_assistant_interview_dashboard(client):
    resume = _demo(client)
    job = client.post("/api/job/samples/5").json()
    m = client.post("/api/match", json={"resume_id": resume["id"], "job_id": job["id"]}).json()
    assert m["breakdown"]["skills"]["max"] == 35
    gap = client.get(f"/api/skills/gap/{m['id']}").json()
    assert "RAG" in gap["missing"]
    chat = client.post("/api/assistant/chat", json={"resume_id": resume["id"], "match_id": m["id"], "question": "What skills am I missing?"}).json()
    assert "RAG" in chat["answer"]
    unknown = client.post("/api/assistant/chat", json={"resume_id": resume["id"], "question": "Who won the 1998 football world cup?"}).json()
    assert unknown["answer"] == "I couldn't find this information in the uploaded documents."
    iv = client.post("/api/interview/generate", json={"resume_id": resume["id"], "job_id": job["id"], "count": 8}).json()
    assert len(iv["questions"]) == 8
    ev = client.post("/api/interview/evaluate", json={"question_id": iv["questions"][0]["id"], "answer": "I built it with Python for example using XGBoost."}).json()
    assert 0 <= ev["score"] <= 10
    dash = client.get("/api/dashboard").json()
    assert dash["totals"]["resumes"] >= 1 and dash["totals"]["matches"] >= 1
    assert client.get("/api/history").json()["matches"]


def test_frontend_is_served(client):
    assert "AI-Powered Career Intelligence" in client.get("/").text or client.get("/").status_code == 200
