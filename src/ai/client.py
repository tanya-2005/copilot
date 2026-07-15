"""
client.py — thin wrapper around the OpenRouter API
(openrouter.ai/api/v1/chat/completions), using plain HTTP requests — no SDK
dependency, consistent with the rest of this project's discovery modules.

Previously used Google's Gemini API directly, but its free tier gets
overloaded ("model is overloaded, please try again later") under normal,
low-volume use. OpenRouter's free router (`openrouter/free`) spreads
requests across ~20 different free models instead of hammering one, which
is far more reliable in practice. Every module that needs AI generation
goes through this wrapper, so swapping providers again later means editing
one file, not every call site.

Web-search grounding (use_search=True) does NOT use OpenRouter's built-in
web plugin, because that costs money on every call even for free models.
Instead it uses Tavily's search API (1,000 free searches/month, no card
required) to fetch real results, which get stitched into the prompt as
context before the free OpenRouter model writes the answer — keeping the
whole pipeline free.
"""
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "config"))
from settings import settings  # noqa: E402

API_BASE = "https://openrouter.ai/api/v1"
TAVILY_API_BASE = "https://api.tavily.com"
# openrouter/free randomly routes each request across OpenRouter's pool of
# free-tier models, which avoids the single-model rate-limit/overload issue
# Gemini's free tier had. Override with a specific model (e.g.
# "meta-llama/llama-3.3-70b-instruct:free") via OPENROUTER_MODEL if you want
# consistent model behavior instead of the pool.
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")


class AIClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, tavily_api_key: str = ""):
        self.api_key = api_key
        self.model = model
        self.tavily_api_key = tavily_api_key

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        use_search: bool = False,
        search_query: str = None,
    ) -> str:
        """Sends one prompt, returns the plain text response. Set use_search=True
        to ground the answer in live web search results (used by the
        discovery/contact-finding modules; not needed for scoring or writing).
        Pass search_query for a short, focused search string — falls back to
        the full prompt if omitted, which works but returns noisier results."""
        if use_search:
            prompt = self._add_search_context(prompt, search_query or prompt)

        url = f"{API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/internship-copilot",
            "X-Title": "internship-copilot",
        }
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }

        resp = requests.post(url, headers=headers, json=body, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""

    def _add_search_context(self, prompt: str, query: str) -> str:
        results = self._tavily_search(query)
        if not results:
            return prompt
        block = "\n\n".join(
            f"- {r.get('title', '')}\n  URL: {r.get('url', '')}\n  {r.get('content', '')}"
            for r in results
        )
        return (
            f"{prompt}\n\n"
            "Live web search results for reference (base your answer ONLY on "
            f"these — do not invent URLs or facts beyond what's shown here):\n\n{block}"
        )

    def _tavily_search(self, query: str, max_results: int = 5) -> list:
        resp = requests.post(
            f"{TAVILY_API_BASE}/search",
            headers={"Authorization": f"Bearer {self.tavily_api_key}"},
            json={"query": query, "max_results": max_results},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])


def get_client() -> AIClient:
    settings.validate_for(["OPENROUTER_API_KEY"])
    return AIClient(api_key=settings.OPENROUTER_API_KEY, tavily_api_key=settings.TAVILY_API_KEY)
