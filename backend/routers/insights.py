"""
insights.py — read access to generated AI Insights reports (see
src/insights/generator.py). Generation itself happens in
src/scheduler/weekly_insights.py, triggered by the weekly GitHub Actions
workflow or POST /api/runs/insights (see runs.py) — this router only reads
what's already been persisted, to keep an expensive Claude call off the
request path.
"""
import json
import os
import sys

from fastapi import APIRouter, Depends, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "storage"))

from models import Insight  # noqa: E402

from ..deps import get_db  # noqa: E402

router = APIRouter(tags=["insights"])


def _insight_row(insight: Insight) -> dict:
    content = json.loads(insight.content)
    return {
        "id": insight.id,
        "period_days": insight.period_days,
        "jobs_scored": insight.jobs_scored,
        "generated_at": insight.generated_at,
        **content,
    }


@router.get("/insights/latest")
def latest_insight(db=Depends(get_db)):
    insight = db.query(Insight).order_by(Insight.generated_at.desc()).first()
    if not insight:
        raise HTTPException(status_code=404, detail="No insights generated yet")
    return _insight_row(insight)


@router.get("/insights")
def list_insights(limit: int = 10, db=Depends(get_db)):
    insights = db.query(Insight).order_by(Insight.generated_at.desc()).limit(limit).all()
    return [_insight_row(i) for i in insights]
