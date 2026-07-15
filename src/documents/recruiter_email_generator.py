"""
recruiter_email_generator.py — generates a short, personalized outreach
email for contacting a recruiter/hiring manager directly (in addition to
the formal application), grounded in real resume content.
"""
import json
import re


def generate_recruiter_email(client, resume_text: str, title: str, company: str,
                              candidate_name: str, recruiter_name: str = "") -> dict:
    greeting_hint = f"Address it to {recruiter_name}." if recruiter_name else \
        "No specific name is known — use a generic professional greeting."
    prompt = (
        f"Write a short (120-180 word) outreach email from {candidate_name}, a student, to a "
        f"recruiter/hiring manager at {company}, about the '{title}' internship they just applied to. "
        f"{greeting_hint} Goal: politely flag the application and briefly highlight the single most "
        "relevant piece of real experience from the resume below. No invented experience. No generic "
        "flattery. Professional but not stiff.\n\n"
        f"RESUME:\n{resume_text}\n\n"
        'Respond with ONLY a JSON object: {"subject": "...", "body": "..."}'
    )
    text = client.generate(prompt, max_tokens=500)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {"subject": f"Application for {title}", "body": text.strip()}
