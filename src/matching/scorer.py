"""
scorer.py — scores a job against the resume on a 0-100 scale with a
one-line explanation. Deliberately lightweight (title/company/location +
description) so it's cheap to run against every newly discovered job.
"""
import json
import re


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


def score_job(client, resume_text: str, title: str, company: str, location: str, description: str = "") -> dict:
    desc_excerpt = (description or "")[:3000]  # keep prompt bounded
    prompt = (
        "You are helping a student evaluate internship fit. Given the resume and job posting below, "
        "score how strong a match this is on a 0-100 scale, considering role type (SDE/tech/product/"
        "product-analyst intern), the candidate's demonstrated skills, and internship-appropriateness "
        "(not a senior-level role).\n\n"
        f"RESUME:\n{resume_text}\n\n"
        f"POSTING:\nTitle: {title}\nCompany: {company}\nLocation: {location}\n"
        f"Description: {desc_excerpt}\n\n"
        'Respond with ONLY a JSON object: {"score": <int 0-100>, "reason": "<one sentence>"}'
    )
    text = client.generate(prompt, max_tokens=300)
    try:
        return _extract_json(text)
    except Exception:
        return {"score": 0, "reason": "could not parse model output"}
