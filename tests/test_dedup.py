"""
test_dedup.py — pure unit tests for RawJob.description_hash(), no DB or
API calls needed. Run: python -m pytest tests/test_dedup.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "discovery"))
from base import RawJob, title_matches


def test_same_company_and_title_same_hash():
    a = RawJob(title="SDE Intern", company="Acme", location="Remote", url="https://a.com/1", source="greenhouse")
    b = RawJob(title="SDE Intern", company="Acme", location="Onsite", url="https://a.com/2", source="lever")
    assert a.description_hash() == b.description_hash()


def test_different_title_different_hash():
    a = RawJob(title="SDE Intern", company="Acme", location="Remote", url="https://a.com/1", source="greenhouse")
    b = RawJob(title="Product Intern", company="Acme", location="Remote", url="https://a.com/1", source="greenhouse")
    assert a.description_hash() != b.description_hash()


def test_title_matches_keyword():
    keywords = ["sde intern", "product analyst intern"]
    excludes = ["senior", "staff"]
    assert title_matches("SDE Intern - Summer 2027", keywords, excludes)
    assert not title_matches("Senior SDE Intern", keywords, excludes)
    assert not title_matches("Backend Engineer", keywords, excludes)


if __name__ == "__main__":
    test_same_company_and_title_same_hash()
    test_different_title_different_hash()
    test_title_matches_keyword()
    print("All dedup tests passed.")
