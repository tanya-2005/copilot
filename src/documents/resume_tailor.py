"""
resume_tailor.py — generates ATS-optimized resume bullet suggestions for a
specific job, based on the master resume. Rewrites real experience for
emphasis — never invents experience the candidate doesn't have.
"""
import json
import re


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


def tailor_resume(client, resume_text: str, title: str, company: str, description: str) -> dict:
    desc_excerpt = (description or "")[:4000]
    prompt = (
        "You are an ATS-optimization assistant for a student's internship resume. Given the master "
        "resume and the job description below:\n\n"
        "1. Identify the top 5-8 keywords/skills from the job description an ATS would scan for.\n"
        "2. Rewrite 4-6 resume bullet points (based ONLY on the candidate's real projects/experience "
        "in the master resume — never invent experience, companies, or skills they don't have) to "
        "naturally include those keywords and emphasize the most relevant experience first.\n"
        "3. Suggest a one-line resume summary/objective tailored to this specific role.\n\n"
        f"MASTER RESUME:\n{resume_text}\n\n"
        f"JOB TITLE: {title}\nCOMPANY: {company}\nDESCRIPTION:\n{desc_excerpt}\n\n"
        "Respond with ONLY a JSON object:\n"
        '{"ats_keywords": ["...", "..."], "summary_line": "...", "bullets": ["...", "...", "..."]}'
    )
    text = client.generate(prompt, max_tokens=1200)
    try:
        return _extract_json(text)
    except Exception:
        return {"ats_keywords": [], "summary_line": "", "bullets": []}
