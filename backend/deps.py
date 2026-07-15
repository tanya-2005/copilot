"""
deps.py — FastAPI dependencies. Wraps the existing storage/db.py session
context manager so routers get the same session lifecycle (commit-on-you,
rollback-on-exception, always-closed) as the scheduler scripts and dashboard.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "storage"))

from db import get_session  # noqa: E402


def get_db():
    with get_session() as session:
        yield session
