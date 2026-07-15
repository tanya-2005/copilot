"""
test_api.py — smoke test for the FastAPI app wiring (routes mount, health
check responds). Deliberately doesn't hit the DB-backed routes, since those
need a real DATABASE_URL — that's covered by manually exercising the API
against Supabase, same as the rest of this project's DB-dependent code.
Run: python -m pytest tests/test_api.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_routes_registered():
    paths = set(app.openapi()["paths"].keys())
    assert "/api/jobs" in paths
    assert "/api/applications/{job_id}" in paths
    assert "/api/followups" in paths
    assert "/api/stats" in paths
    assert "/api/runs/discovery" in paths


if __name__ == "__main__":
    test_health()
    test_routes_registered()
    print("All API smoke tests passed.")
