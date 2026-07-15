"""
generate_for_job.py — orchestrates the three document generators + exporter
for one job, and persists GeneratedDocument rows. Called only for jobs that
clear the strong_match_threshold, to control API cost.
"""
import sys
import os
import json
import datetime

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "storage"))
from models import GeneratedDocument, DocType
import resume_tailor
import cover_letter_generator
import recruiter_email_generator

# NOTE ON FILE PERSISTENCE: GitHub Actions runners are ephemeral — anything
# written to generated/ during a workflow run is gone once that run ends
# (we upload it as a workflow artifact for a 14-day safety net, but that's
# not meant to be the long-term source). So the DATABASE, not the filesystem,
# is the durable store here: content_text always holds everything needed to
# reconstruct the document. The dashboard regenerates the actual .docx file
# on demand from content_text when you click download, rather than reading
# file_path off disk. file_path is left populated for same-run debugging only
# — never rely on it existing later.


def generate_documents_for_job(session, client, job, resume_text: str, candidate_name: str) -> dict:
    company_name = job.company.name if job.company else job.title
    description = job.description_raw or ""

    tailored = resume_tailor.tailor_resume(client, resume_text, job.title, company_name, description)
    letter_text = cover_letter_generator.generate_cover_letter(
        client, resume_text, job.title, company_name, description, candidate_name
    )
    email = recruiter_email_generator.generate_recruiter_email(
        client, resume_text, job.title, company_name, candidate_name
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    session.add(GeneratedDocument(job_id=job.id, doc_type=DocType.resume,
                                   file_path=None, content_text=json.dumps(tailored),
                                   generated_at=now))
    session.add(GeneratedDocument(job_id=job.id, doc_type=DocType.cover_letter,
                                   file_path=None, content_text=letter_text,
                                   generated_at=now))
    session.add(GeneratedDocument(job_id=job.id, doc_type=DocType.recruiter_email,
                                   file_path=None,
                                   content_text=json.dumps(email),
                                   generated_at=now))
    session.flush()

    return {"tailored": tailored, "letter_text": letter_text, "email": email}
