"""Interview question generation (personalised) and answer evaluation."""
import json
import re

from backend.services import llm_service
from backend.services.skill_extractor import display_name, extract_skills

CATEGORIES = ["Technical", "HR", "Project", "Coding", "Behavioral", "System Design", "SQL", "Python",
              "Machine Learning", "Generative AI"]

BANK = {
    "HR": [("Tell me about yourself.", "Easy", ["background", "skills", "goals"], ["Why this role?"]),
           ("Why do you want to join our company?", "Easy", ["research", "alignment", "growth"], ["Where do you see yourself in 3 years?"]),
           ("What are your strengths and weaknesses?", "Easy", ["self-awareness", "example", "improvement"], ["How are you working on the weakness?"])],
    "Behavioral": [("Describe a time you faced a difficult bug or setback and how you solved it.", "Medium", ["situation", "action", "result"], ["What would you do differently?"]),
                   ("Tell me about a time you worked in a team to deliver something.", "Medium", ["role", "collaboration", "outcome"], ["How did you handle disagreement?"])],
    "System Design": [("How would you design a resume screening service that handles 10,000 uploads per day?", "Hard", ["api layer", "queue", "database", "caching", "scaling"], ["Where would you store files?", "How would you monitor it?"]),
                      ("Explain the difference between monolith and microservices.", "Medium", ["coupling", "deployment", "scaling", "trade-offs"], ["When would you choose a monolith?"])],
    "SQL": [("Explain the difference between INNER JOIN and LEFT JOIN.", "Easy", ["matching rows", "null", "example"], ["When would LEFT JOIN give duplicates?"]),
            ("How do you find the second highest salary in a table?", "Medium", ["subquery", "limit offset", "dense_rank", "distinct"], ["How does it change for ties?"]),
            ("What is an index and when can it hurt performance?", "Medium", ["lookup speed", "write overhead", "selectivity"], ["What is a composite index?"])],
    "Python": [("What is the difference between a list and a tuple?", "Easy", ["mutability", "performance", "use cases"], ["Can a tuple be a dict key?"]),
               ("Explain decorators and give a use case.", "Medium", ["higher-order function", "wrapper", "logging", "example"], ["What is functools.wraps?"]),
               ("How does Python manage memory?", "Hard", ["reference counting", "garbage collector", "heap"], ["What are circular references?"])],
    "Coding": [("Write a function to check whether a string is a palindrome and explain its complexity.", "Easy", ["two pointers", "O(n)", "edge cases"], ["How would you ignore punctuation?"]),
               ("Given an array, find two numbers that add up to a target.", "Medium", ["hash map", "O(n)", "brute force comparison"], ["What if the array is sorted?"])],
    "Machine Learning": [("Explain the bias-variance trade-off.", "Medium", ["underfitting", "overfitting", "regularisation", "cross-validation"], ["How do you detect overfitting?"]),
                         ("Why is accuracy a poor metric for imbalanced data? What would you use?", "Medium", ["precision", "recall", "f1", "pr-auc"], ["How do you pick a threshold?"]),
                         ("How does a random forest differ from gradient boosting?", "Hard", ["bagging", "boosting", "variance", "bias"], ["Which would you try first?"])],
    "Generative AI": [("What is RAG and why use it instead of fine-tuning?", "Medium", ["retrieval", "embeddings", "grounding", "hallucination", "cost"], ["How do you choose chunk size?"]),
                      ("What are embeddings and how does cosine similarity work?", "Medium", ["vector", "semantic meaning", "angle", "normalisation"], ["Why use a vector database?"]),
                      ("How do you reduce hallucinations in LLM applications?", "Hard", ["grounding", "prompting", "citations", "evaluation"], ["How would you measure them?"])],
    "Technical": [("What is REST and what makes an API RESTful?", "Easy", ["stateless", "http methods", "resources", "status codes"], ["PUT vs PATCH?"]),
                  ("Explain OOP principles with examples.", "Easy", ["encapsulation", "inheritance", "polymorphism", "abstraction"], ["Composition vs inheritance?"])],
}
SKILL_Q = {
    "python": ("Python", "How do generators work and when would you use one?", "Medium", ["yield", "lazy evaluation", "memory"]),
    "sql": ("SQL", "How would you optimise a slow SQL query?", "Medium", ["explain plan", "index", "joins", "select columns"]),
    "fastapi": ("Technical", "How does FastAPI use Pydantic and dependency injection?", "Medium", ["validation", "type hints", "depends", "async"]),
    "docker": ("Technical", "What is the difference between a Docker image and a container?", "Easy", ["image", "container", "layers", "dockerfile"]),
    "machine learning": ("Machine Learning", "Walk me through the end-to-end ML workflow you follow.", "Medium", ["data cleaning", "features", "training", "evaluation", "deployment"]),
    "nlp": ("Machine Learning", "What are TF-IDF and word embeddings, and how do they differ?", "Medium", ["sparse", "dense", "semantic", "context"]),
    "git": ("Technical", "Explain branching and how you resolve a merge conflict.", "Easy", ["branch", "merge", "conflict", "pull request"]),
    "rag": ("Generative AI", "Describe the pipeline of a RAG system end to end.", "Medium", ["chunking", "embeddings", "vector search", "llm", "prompt"]),
    "llm": ("Generative AI", "What is prompt engineering and what techniques do you use?", "Medium", ["clear instructions", "few-shot", "role", "format"]),
    "java": ("Technical", "What is the difference between an interface and an abstract class in Java?", "Medium", ["multiple inheritance", "default methods", "state"]),
    "javascript": ("Technical", "Explain closures and the event loop in JavaScript.", "Medium", ["scope", "callback queue", "async"]),
}


def _mk(category, q, diff, concepts, follow):
    return {"category": category, "question": q, "difficulty": diff, "expected_concepts": concepts, "follow_ups": follow}


def generate_questions(resume: dict, jd: dict | None, categories: list[str] | None = None, count: int = 12) -> list[dict]:
    """Build a personalised, deterministic question set from resume, JD and skill gaps."""
    qs: list[dict] = []
    for p in resume["projects"][:3]:
        title = p["title"]
        techs = [display_name(s) for s in extract_skills(title + " " + p["description"])][:4]
        qs.append(_mk("Project", f"Walk me through your project \"{title}\". What problem did it solve and what was your role?",
                      "Medium", ["problem statement", "your contribution", "tech stack", "result"], ["What was the hardest part?"]))
        for tech in techs[:2]:
            qs.append(_mk("Project", f"Why did you choose {tech} for \"{title}\"? What alternatives did you consider?",
                          "Medium", ["trade-offs", "alternatives", "justification"], ["How would you scale it?"]))
    wanted = set(resume["skills"]) if not jd else set(jd["required_skills"]) | set(jd["preferred_skills"])
    for sk in sorted(wanted & set(resume["skills"])):
        if sk in SKILL_Q:
            c, q, d, ex = SKILL_Q[sk]
            qs.append(_mk(c, q, d, ex, [f"Where have you used {display_name(sk)} in your projects?"]))
    if jd:
        for sk in jd["required_skills"]:
            if sk not in resume["skills"]:
                qs.append(_mk("Technical", f"This role requires {display_name(sk)}, which is not on your resume. How would you get productive with it quickly?",
                              "Medium", ["learning plan", "related experience", "practice project"], [f"What do you already know that transfers to {display_name(sk)}?"]))
    for cat, items in BANK.items():
        for q in items:
            qs.append(_mk(cat, *q))
    wanted_cats = {c.lower() for c in categories} if categories else None
    if wanted_cats:
        qs = [q for q in qs if q["category"].lower() in wanted_cats]
    seen, uniq = set(), []
    for q in qs:
        if q["question"] not in seen:
            seen.add(q["question"]); uniq.append(q)
    if not wanted_cats:  # balanced mix: round-robin by category
        by: dict[str, list] = {}
        for q in uniq:
            by.setdefault(q["category"], []).append(q)
        mixed = []
        while any(by.values()) and len(mixed) < count:
            for cat in list(by):
                if by[cat]:
                    mixed.append(by[cat].pop(0))
        return mixed[:count]
    return uniq[:count]


def sample_answer(q: dict) -> str:
    """Optional AI answer (LLM) or a concept checklist in local mode."""
    if llm_service.is_available():
        out = llm_service.generate(f"Give a concise, interview-ready answer (max 90 words) to: {q['question']}",
                                   system="You are a senior engineer coaching a fresher.")
        if out:
            return out.strip()
    return "A strong answer covers: " + ", ".join(q["expected_concepts"]) + "."


def evaluate_answer(question: str, concepts: list[str], answer: str) -> dict:
    """Score an answer out of 10 (LLM if available, transparent heuristic otherwise)."""
    if llm_service.is_available():
        out = llm_service.generate(
            f"Question: {question}\nExpected concepts: {', '.join(concepts)}\nCandidate answer: {answer}\n"
            'Return ONLY JSON: {"score": 0-10, "positives": [..], "improvements": [..], "suggestion": ".."}',
            system="You are a strict but fair technical interviewer.")
        try:
            data = json.loads(re.search(r"\{.*\}", out or "", re.S).group(0))
            return {"score": float(data["score"]), "positives": data.get("positives", []),
                    "improvements": data.get("improvements", []), "suggestion": data.get("suggestion", ""), "mode": "llm"}
        except Exception:
            pass
    low = answer.lower()
    hit = [c for c in concepts if any(w in low for w in re.findall(r"[a-z0-9]+", c.lower()) if len(w) > 3) or c.lower() in low]
    coverage = len(hit) / len(concepts) if concepts else 0.5
    words = len(answer.split())
    example = bool(re.search(r"for example|for instance|e\.g\.|such as|in my project|i used|i built", low))
    score = 6.5 * coverage + (1.0 if words >= 25 else 0.4 if words >= 10 else 0) + (1.0 if example else 0) + (1.5 if words >= 50 and coverage >= 0.5 else 0.5 if words >= 35 else 0)
    score = round(min(10.0, score), 1)
    positives, improvements = [], []
    if hit:
        positives.append("Covered key concepts: " + ", ".join(hit))
    if words >= 40:
        positives.append("Good level of explanation")
    missed = [c for c in concepts if c not in hit]
    if missed:
        improvements.append("Mention: " + ", ".join(missed[:4]))
    if not example:
        improvements.append("Add a concrete example from a project")
    if words < 40:
        improvements.append("Add more technical detail")
    suggestion = "Structure your answer as: definition, how it works, example, trade-off."
    return {"score": score, "positives": positives, "improvements": improvements, "suggestion": suggestion, "mode": "local"}
