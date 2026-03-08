from __future__ import annotations

from core.ports.llm import LLMClient


class OpenAIClient(LLMClient):
    def complete(self, prompt: str) -> str:
        raise NotImplementedError("LLM client integration is not configured")
