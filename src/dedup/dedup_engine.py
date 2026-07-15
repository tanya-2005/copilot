"""
dedup_engine.py — filters a list of RawJob against what's already stored,
by URL first (primary key) and description_hash second (catches reposts
under a new ATS id). Also handles finding-or-creating the Company row and
persisting genuinely new jobs.
"""
import sys
import os
import datetime

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "storage"))
from models import Company, Job, AtsType, RemoteType


def _infer_remote_type(location: str) -> RemoteType:
    loc = (location or "").lower()
    if "remote" in loc:
        return RemoteType.remote
    if "hybrid" in loc:
        return RemoteType.hybrid
    if loc:
        return RemoteType.onsite
    return RemoteType.unknown


def _get_or_create_company(session, name: str, source: str) -> Company:
    company = session.query(Company).filter_by(name=name).first()
    if company:
        return company
    try:
        ats_type = AtsType(source) if source in AtsType.__members__.values() else AtsType.manual
    except ValueError:
        ats_type = AtsType.manual
    company = Company(name=name, ats_type=ats_type, enabled=True)
    session.add(company)
    session.flush()
    return company


def filter_new_jobs(session, raw_jobs: list) -> list:
    """Returns the subset of raw_jobs not already present in the DB (by URL
    or description_hash among currently-active jobs)."""
    existing_urls = {u for (u,) in session.query(Job.url).all()}
    existing_hashes = {h for (h,) in session.query(Job.description_hash)
                        .filter(Job.is_active == True).all() if h}  # noqa: E712

    new_jobs = []
    for rj in raw_jobs:
        if not rj.url or rj.url in existing_urls:
            continue
        if rj.description_hash() in existing_hashes:
            continue
        new_jobs.append(rj)
    return new_jobs


def persist_new_jobs(session, raw_jobs: list) -> list:
    """Creates Company (if needed) and Job rows for each raw job. Returns
    the list of created Job ORM objects."""
    created = []
    for rj in raw_jobs:
        company = _get_or_create_company(session, rj.company, rj.source)
        try:
            source_enum = AtsType(rj.source)
        except ValueError:
            source_enum = AtsType.manual

        job = Job(
            company_id=company.id,
            source=source_enum,
            external_id=rj.external_id or None,
            title=rj.title,
            location=rj.location,
            remote_type=_infer_remote_type(rj.location),
            url=rj.url,
            description_raw=rj.description,
            description_hash=rj.description_hash(),
            date_discovered=datetime.datetime.now(datetime.timezone.utc),
            last_seen_at=datetime.datetime.now(datetime.timezone.utc),
            is_active=True,
        )
        session.add(job)
        created.append(job)
    session.flush()
    return created
