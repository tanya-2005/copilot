"""
main.py — FastAPI app. Run locally with:
    uvicorn backend.main:app --reload --port 8000
(from the internship-copilot/ directory, so `backend` resolves as a package)

This wraps the existing src/ modules (discovery, matching, documents,
storage) behind a REST API for the React frontend. It doesn't duplicate any
business logic — every route either reads via SQLAlchemy models already
defined in src/storage/models.py, or calls into the existing
scheduler/documents/exporters functions.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import applications, followups, insights, jobs, runs, stats

app = FastAPI(title="Internship Copilot API")

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", _default_origins).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(followups.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(insights.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
