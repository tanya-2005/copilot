"""
test_ai_client.py — unit tests for the OpenRouter + Tavily AI client
wrapper, using mocked HTTP responses (no real network calls).
Run: python -m pytest tests/test_ai_client.py -v
"""
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ai"))
import client as ai_client


def _mock_response(text: str):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {
        "choices": [{"message": {"content": text}}]
    }
    return resp


def _mock_tavily_response(results: list):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"results": results}
    return resp


@patch("client.requests.post")
def test_generate_returns_text(mock_post):
    mock_post.return_value = _mock_response('{"score": 80, "reason": "Strong match"}')

    c = ai_client.AIClient(api_key="fake-key")
    result = c.generate("score this job", max_tokens=300)

    assert result == '{"score": 80, "reason": "Strong match"}'
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer fake-key"


@patch("client.requests.post")
def test_generate_with_search_queries_tavily_then_openrouter(mock_post):
    tavily_resp = _mock_tavily_response(
        [{"title": "SDE Intern", "url": "https://example.com/job/1", "content": "Summer 2027 internship"}]
    )
    openrouter_resp = _mock_response("[]")
    mock_post.side_effect = [tavily_resp, openrouter_resp]

    c = ai_client.AIClient(api_key="fake-key", tavily_api_key="tvly-fake")
    c.generate("find postings", max_tokens=2000, use_search=True, search_query="sde intern remote")

    assert mock_post.call_count == 2

    tavily_call, openrouter_call = mock_post.call_args_list
    assert tavily_call.args[0] == "https://api.tavily.com/search"
    assert tavily_call.kwargs["headers"]["Authorization"] == "Bearer tvly-fake"
    assert tavily_call.kwargs["json"]["query"] == "sde intern remote"

    assert openrouter_call.args[0] == "https://openrouter.ai/api/v1/chat/completions"
    sent_prompt = openrouter_call.kwargs["json"]["messages"][0]["content"]
    assert "https://example.com/job/1" in sent_prompt
    assert "plugins" not in openrouter_call.kwargs["json"]


@patch("client.requests.post")
def test_generate_with_search_falls_back_when_no_results(mock_post):
    tavily_resp = _mock_tavily_response([])
    openrouter_resp = _mock_response("[]")
    mock_post.side_effect = [tavily_resp, openrouter_resp]

    c = ai_client.AIClient(api_key="fake-key", tavily_api_key="tvly-fake")
    c.generate("find postings", use_search=True, search_query="sde intern")

    _, openrouter_call = mock_post.call_args_list
    assert openrouter_call.kwargs["json"]["messages"][0]["content"] == "find postings"


@patch("client.requests.post")
def test_generate_handles_empty_choices(mock_post):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"choices": []}
    mock_post.return_value = resp

    c = ai_client.AIClient(api_key="fake-key")
    assert c.generate("anything") == ""


if __name__ == "__main__":
    test_generate_returns_text()
    test_generate_with_search_queries_tavily_then_openrouter()
    test_generate_with_search_falls_back_when_no_results()
    test_generate_handles_empty_choices()
    print("All AI client tests passed.")
