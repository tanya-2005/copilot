"""
load_resume.py — (re)loads the master resume text into the database.
Run this once initially, and again any time you update your resume.

Usage:
    python scripts/load_resume.py resume/master_resume.txt
"""
import sys
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "storage"))
from db import get_session
from models import Resume


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/load_resume.py <path-to-resume-text-file>")
        sys.exit(1)

    resume_path = sys.argv[1]
    with open(resume_path) as f:
        text = f.read()

    version_label = f"master-{datetime.date.today().isoformat()}"

    with get_session() as session:
        session.query(Resume).filter_by(is_master=True).update({"is_master": False})
        resume = Resume(
            version_label=version_label,
            file_path=resume_path,
            text_content=text,
            is_master=True,
        )
        session.add(resume)
        session.commit()
        print(f"Loaded master resume '{version_label}' ({len(text)} chars). Previous master versions kept, no longer marked as master.")


if __name__ == "__main__":
    main()
