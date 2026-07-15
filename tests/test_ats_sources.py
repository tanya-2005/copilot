"""
test_ats_sources.py — unit tests for the Workday and SmartRecruiters
fetchers, using mocked HTTP responses (no real network calls).
Run: python -m pytest tests/test_ats_sources.py -v
"""
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "discovery"))
import ats_workday
import ats_smartrecruiters

KEYWORDS = ["software engineering intern"]
EXCLUDES = ["senior"]


def _mock_response(json_data):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


@patch("ats_workday.requests.get")
@patch("ats_workday.requests.post")
def test_workday_fetch_matches_and_paginates(mock_post, mock_get):
    page = {
        "total": 1,
        "jobPostings": [
            {
                "title": "Software Engineering Intern",
                "locationsText": "Remote",
                "externalPath": "/job/Remote/Software-Engineering-Intern_R-123",
                "bulletFields": ["R-123"],
            },
        ],
    }
    mock_post.return_value = _mock_response(page)
    mock_get.return_value = _mock_response({"jobPostingInfo": {"jobDescription": "<p>Build things.</p>"}})

    results = ats_workday.fetch("Acme", "acme/wd5/External", KEYWORDS, EXCLUDES)

    assert len(results) == 1
    job = results[0]
    assert job.title == "Software Engineering Intern"
    assert job.url == "https://acme.wd5.myworkdayjobs.com/en-US/External/job/Remote/Software-Engineering-Intern_R-123"
    assert job.source == "workday"
    assert job.external_id == "R-123"
    assert "Build things." in job.description
    mock_post.assert_called_once()


def test_workday_fetch_bad_token_format():
    assert ats_workday.fetch("Acme", "not-a-valid-token", KEYWORDS, EXCLUDES) == []


@patch("ats_smartrecruiters.requests.get")
def test_smartrecruiters_fetch_matches_and_excludes(mock_get):
    postings_page = _mock_response({
        "content": [
            {
                "id": "123",
                "name": "Software Engineering Intern",
                "location": {"city": "Austin", "region": "TX", "country": "US", "remote": False},
                "postingUrl": "https://jobs.smartrecruiters.com/Acme/123",
            },
            {
                "id": "456",
                "name": "Senior Software Engineer",
                "location": {"remote": True},
                "postingUrl": "https://jobs.smartrecruiters.com/Acme/456",
            },
        ]
    })
    description_page = _mock_response({"jobAd": {"sections": {"jobDescription": {"text": "Build things."}}}})
    mock_get.side_effect = [postings_page, description_page]

    results = ats_smartrecruiters.fetch("Acme", "Acme", KEYWORDS, EXCLUDES)

    assert len(results) == 1
    job = results[0]
    assert job.title == "Software Engineering Intern"
    assert job.location == "Austin, TX, US"
    assert job.external_id == "123"
    assert "Build things." in job.description


if __name__ == "__main__":
    test_workday_fetch_matches_and_paginates()
    test_workday_fetch_bad_token_format()
    test_smartrecruiters_fetch_matches_and_excludes()
    print("All ATS source tests passed.")
