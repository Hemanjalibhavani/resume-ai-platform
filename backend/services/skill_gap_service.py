"""Skill gap analysis: why it matters, what to learn, a project idea and a priority."""
from backend.services.skill_extractor import display_name

KB = {
    "fastapi": ("Required for building high-performance backend REST APIs in Python.",
                ["REST API basics", "FastAPI routing & dependency injection", "Pydantic validation", "Authentication (JWT)", "Database integration (SQLAlchemy)"],
                "Build a CRUD API with JWT auth and deploy it on Render."),
    "docker": ("Packages applications so they run identically everywhere; expected in most backend/ML roles.",
               ["Images vs containers", "Writing a Dockerfile", "docker-compose", "Volumes & networks", "Pushing to a registry"],
               "Containerise one of your existing projects and run it with docker compose."),
    "kubernetes": ("Orchestrates containers at scale; common for cloud/DevOps-leaning roles.",
                   ["Pods, Deployments, Services", "kubectl basics", "ConfigMaps & Secrets", "Local cluster with minikube/kind"],
                   "Deploy a containerised API to a local kind cluster with 2 replicas."),
    "aws": ("Most employers deploy on the cloud; AWS is the market leader.",
            ["IAM basics", "EC2 & S3", "RDS", "Lambda", "Deploying a container (ECS/App Runner)"],
            "Host a model-serving API on EC2 or App Runner with data in S3."),
    "system design": ("Shows you can structure scalable systems; asked in many interviews.",
                      ["Client-server & REST", "Databases & indexing", "Caching", "Load balancing", "Queues & scaling"],
                      "Write a design doc for a URL shortener and implement a small version."),
    "sql": ("Core skill for data access in nearly every software/data role.",
            ["SELECT/WHERE/GROUP BY", "JOINs", "Subqueries & CTEs", "Window functions", "Indexes"],
            "Analyse a public dataset in SQL and publish queries with insights."),
    "rag": ("Grounds LLM answers in your own documents; a hot Generative AI skill.",
            ["Chunking", "Embeddings", "Vector search", "Prompt grounding", "Evaluation"],
            "Build a PDF question-answering bot with citations."),
    "llm": ("LLMs power modern AI products and are central to GenAI roles.",
            ["How transformers work", "Prompt engineering", "API usage", "Fine-tuning vs RAG", "Evaluation & safety"],
            "Create a prompt-driven assistant that calls an LLM API."),
    "generative ai": ("Many companies are building GenAI features; baseline literacy is expected.",
                      ["LLM basics", "Prompt engineering", "RAG", "Embeddings", "Responsible AI"],
                      "Ship a small GenAI app (summariser or chatbot) with a web UI."),
    "pytorch": ("Leading deep-learning framework for research and production.",
                ["Tensors & autograd", "nn.Module", "Training loops", "Datasets/DataLoaders", "Saving & serving models"],
                "Train an image classifier and serve it with an API."),
    "tensorflow": ("Widely used deep-learning framework in industry.",
                   ["Keras API", "tf.data", "Training & callbacks", "SavedModel", "TF Serving"],
                   "Train a text classifier and export it."),
    "git": ("Version control is mandatory for team development.",
            ["commit/branch/merge", "Pull requests", "Resolving conflicts", "Git workflow"], "Contribute a PR to an open-source repo."),
    "java": ("Java is heavily used in enterprise/MNC services.",
             ["OOP", "Collections", "Exceptions & generics", "Streams", "JDBC / Spring basics"],
             "Build a library-management REST service with Spring Boot."),
    "react": ("Popular frontend framework for modern web apps.",
              ["Components & props", "State & hooks", "Routing", "Fetching APIs"], "Build a dashboard that calls your own API."),
    "ci/cd": ("Automates testing and deployment, expected of production-ready engineers.",
              ["GitHub Actions", "Automated tests", "Build & deploy pipelines"], "Add a GitHub Actions workflow that tests and deploys your project."),
    "mlops": ("Bridges ML models and production reliability.",
              ["Experiment tracking", "Model versioning", "Docker", "Monitoring & drift"], "Track experiments with MLflow and deploy the best model."),
    "power bi": ("Common BI tool for analyst roles.", ["Data modelling", "DAX basics", "Dashboards"], "Create a sales dashboard from a CSV dataset."),
    "tableau": ("Common BI tool for analyst roles.", ["Connecting data", "Calculated fields", "Dashboards"], "Publish a public dashboard."),
    "pandas": ("The standard library for data manipulation in Python.", ["DataFrames", "Cleaning", "GroupBy", "Merging"], "Clean and analyse a messy CSV dataset."),
    "vector database": ("Stores embeddings for fast semantic search in RAG systems.", ["Embeddings", "FAISS / ChromaDB", "Indexing & metadata", "Similarity metrics"], "Index 100 documents and build semantic search."),
    "embeddings": ("Numeric vectors capturing meaning; the base of semantic search.", ["Sentence Transformers", "Cosine similarity", "Chunking"], "Build a semantic FAQ search."),
}
DEFAULT_LEARN = ["Fundamentals & core concepts", "Official documentation / quick-start", "Hands-on tutorial", "A small portfolio project"]


def build_gap(skill: str, status: str, required: bool, reason: str = "") -> dict:
    """Detailed advice for one missing/partial skill."""
    why, learn, project = KB.get(skill, (
        f"{display_name(skill)} appears in the job requirements and is part of the expected skill set.",
        DEFAULT_LEARN, f"Build a small project that uses {display_name(skill)} and add it to your resume."))
    if status == "partial":
        priority = "MEDIUM" if required else "LOW"
    else:
        priority = "HIGH" if required else "MEDIUM"
    return {"skill": skill, "display": display_name(skill), "status": status, "priority": priority,
            "required": required, "why": why, "learn": learn, "project": project, "note": reason}


def analyze_gaps(match: dict, jd: dict) -> list[dict]:
    """Build gap entries for every missing and partially matched skill, highest priority first."""
    req = set(jd["required_skills"])
    gaps = [build_gap(s, "missing", s in req) for s in match["missing_skills"]]
    gaps += [build_gap(p["skill"], "partial", p["skill"] in req, p["reason"]) for p in match["partial_skills"]]
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    return sorted(gaps, key=lambda g: (order[g["priority"]], g["status"] != "missing"))
