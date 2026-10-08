"""FastAPI application entrypoint. Run: uvicorn backend.main:app --reload"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import models
from backend.config import settings
from backend.database import Base, SessionLocal, engine
from backend.routes import (analytics_routes, assistant_routes, interview_routes, job_routes,
                            matching_routes, resume_routes)
from backend.utils.helpers import AppError, get_logger

log = get_logger("main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.vector_db_path).mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:  # auth-ready: a default user owns all data until auth is added
        if not db.get(models.User, 1):
            db.add(models.User(id=1, email="demo@example.com", name="Demo User"))
            db.commit()
    log.info("Application started")
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", [])[1:]) or "input"
    return JSONResponse(status_code=422, content={"detail": f"Invalid {field}: {first.get('msg', 'bad request')}."})


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    log.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})


for r in (resume_routes, job_routes, matching_routes, assistant_routes, interview_routes, analytics_routes):
    app.include_router(r.router)

if Path(settings.frontend_dir).exists():  # serve the UI from the same origin (no CORS issues)
    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
