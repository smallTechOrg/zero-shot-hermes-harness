"""OpenRouter provider — OpenAI-compatible chat/completions over httpx.

Any model on OpenRouter works via the ``provider/model`` id. This adapter also
covers self-hosted OpenAI-compatible endpoints (change the base URL in .env).
"""
from __future__ import annotations

import httpx

from src.llm.providers.base import LLMError, LLMProvider
from src.llm.retry import with_retries


class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def __init__(self, api_key: str, model: str, base_url: str = "https://openrouter.ai/api/v1") -> None:
        self._api_key = api_key
        self.model = model
        self._base_url = base_url.rstrip("/")

    def complete(self, system: str, user: str, *, max_tokens: int = 1024) -> str:
     headers = {
      "Authorization": f"Bearer {self._api_key}",
      "Content-Type": "application/json",
      "HTTP-Referer": "https://up-police-data-analyst.local",
      "X-Title": "UP Police Data Analyst",
     }
     def _call() -> str:
      resp = httpx.post(
       f"{self._base_url}/chat/completions",
       headers=headers,
       json={
        "model": self.model,
        "max_tokens": max_tokens,
        "messages": [
         {"role": "system", "content": system},
         {"role": "user", "content": user},
        ],
       },
       timeout=120.0,
      )
      resp.raise_for_status()
      data = resp.json()
      try:
       text = (data["choices"][0]["message"]["content"] or "").strip()
      except (KeyError, IndexError) as exc:
       raise LLMError(f"openrouter returned no choices: {list(data)}") from exc
      if not text:
       raise LLMError("openrouter returned an empty completion")
      return text

     return with_retries(_call, provider=self.name)
