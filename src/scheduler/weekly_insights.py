"""
weekly_insights.py — generates the AI Insights report (missing skills,
frequent technologies, companies matched well, resume suggestions, weekly
summary), persists it, and emails a digest. Run weekly via GitHub Actions,
separate from the daily discovery run.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "config"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "insights"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "notifications"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "storage"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ai"))

import client as ai_client
from settings import settings
from db import get_session
from models import Insight
import generator
import notifier


def main():
    settings.validate_for(["DATABASE_URL", "OPENROUTER_API_KEY"])
    client = ai_client.get_client()

    with get_session() as session:
        result = generator.generate_insights(session, client)
        session.add(Insight(
            period_days=result["period_days"],
            jobs_scored=result["jobs_scored"],
            content=json.dumps(result),
        ))
        session.commit()

        print(
            f"=== Insights generated: {result['jobs_scored']} job(s) scored, "
            f"{len(result.get('missing_skills', []))} missing skill(s) identified ==="
        )
        notifier.notify_weekly_insights(result)


if __name__ == "__main__":
    main()
