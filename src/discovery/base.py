"""
base.py — shared types and helpers for all discovery sources.
Every source module exposes a fetch(...) function returning a list of
RawJob dicts with this shape:
    {title, company, location, url, source, external_id (optional), description (optional)}
"""
import hashlib
from dataclasses import dataclass, field


@dataclass
class RawJob:
    title: str
    company: str
    location: str
    url: str
    source: str
    external_id: str = ""
    description: str = ""

    def description_hash(self) -> str:
        """Used as a secondary dedup key so the same posting re-listed under
        a new ATS id (common when companies re-post) is still caught."""
        basis = f"{self.company.lower().strip()}|{self.title.lower().strip()}"
        return hashlib.sha256(basis.encode()).hexdigest()


def title_matches(title: str, keywords: list, excludes: list) -> bool:
    t = title.lower()
    if any(ex.lower() in t for ex in excludes):
        return False
    return any(kw.lower() in t for kw in keywords)
