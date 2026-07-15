"""
cover_letter_generator.py — generates a short, specific cover letter draft
for a job, grounded in the candidate's real resume content. Meant as a
strong first draft to personalize/review, not a blind auto-submit artifact.
"""


def generate_cover_letter(client, resume_text: str, title: str, company: str, description: str,
                           candidate_name: str) -> str:
    desc_excerpt = (description or "")[:4000]
    prompt = (
        f"Write a concise, specific cover letter (250-350 words) for {candidate_name}, a student "
        f"applying for the '{title}' internship at {company}. Use ONLY real experience from the "
        "resume below — do not invent anything. Reference 1-2 specific, relevant projects. Avoid "
        "generic filler phrases ('I am a hard worker', 'I am passionate about...'). Sound like a "
        "specific, competent student, not a template. No placeholder brackets — write it ready to send, "
        "except for the greeting which should say 'Dear Hiring Team,' unless a specific name is given.\n\n"
        f"RESUME:\n{resume_text}\n\n"
        f"JOB DESCRIPTION:\n{desc_excerpt}\n\n"
        "Output ONLY the letter body text, no subject line, no commentary."
    )
    return client.generate(prompt, max_tokens=800).strip()
