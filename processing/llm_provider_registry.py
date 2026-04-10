"""Provider-agnostic LLM client used by generation and reranking."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class ProviderConfig:
    provider: str
    model: str


class LLMClient:
    """Minimal multi-provider JSON completion client.

    Supported provider families:
    - OpenAI (GPT models)
    - Anthropic (Claude models)
    - Google (Gemini models)
    - Local Llama endpoint (OpenAI-compatible or Ollama native)
    """

    def __init__(self, model: str):
        self.config = self._resolve_provider(model)

    def complete_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.0, timeout: int = 60) -> Optional[Dict[str, Any]]:
        text = self.complete_text(system_prompt=system_prompt, user_prompt=user_prompt, temperature=temperature, timeout=timeout)
        if not text:
            return None

        try:
            return json.loads(text)
        except Exception:
            match = _JSON_BLOCK_RE.search(text)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except Exception:
                return None

    def complete_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.0, timeout: int = 60) -> Optional[str]:
        provider = self.config.provider
        if provider == "openai":
            return self._openai_chat(system_prompt, user_prompt, temperature, timeout)
        if provider == "anthropic":
            return self._anthropic_messages(system_prompt, user_prompt, temperature, timeout)
        if provider == "gemini":
            return self._gemini_generate(system_prompt, user_prompt, temperature, timeout)
        if provider == "llama_local":
            return self._llama_local_chat(system_prompt, user_prompt, temperature, timeout)
        return None

    def _resolve_provider(self, model: str) -> ProviderConfig:
        normalized = (model or "").strip().lower()
        if not normalized:
            return ProviderConfig(provider="openai", model="gpt-5")

        if "claude" in normalized:
            return ProviderConfig(provider="anthropic", model=model)
        if "gemini" in normalized:
            return ProviderConfig(provider="gemini", model=model)
        if "llama" in normalized:
            return ProviderConfig(provider="llama_local", model=model)
        if normalized.startswith("gpt") or normalized.startswith("o1") or normalized.startswith("o3"):
            return ProviderConfig(provider="openai", model=model)
        return ProviderConfig(provider="openai", model=model)

    def _openai_chat(self, system_prompt: str, user_prompt: str, temperature: float, timeout: int) -> Optional[str]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            import requests  # type: ignore
        except Exception:
            return None

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception:
            return None

    def _anthropic_messages(self, system_prompt: str, user_prompt: str, temperature: float, timeout: int) -> Optional[str]:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        try:
            import requests  # type: ignore
        except Exception:
            return None

        payload = {
            "model": self.config.model,
            "max_tokens": 1500,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            blocks = response.json().get("content", [])
            texts = [block.get("text", "") for block in blocks if isinstance(block, dict) and block.get("type") == "text"]
            return "\n".join([text for text in texts if text]) or None
        except Exception:
            return None

    def _gemini_generate(self, system_prompt: str, user_prompt: str, temperature: float, timeout: int) -> Optional[str]:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None
        try:
            import requests  # type: ignore
        except Exception:
            return None

        model = self.config.model.replace(" ", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}],
                }
            ],
            "generationConfig": {"temperature": temperature},
        }

        try:
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts", [])
            texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
            return "\n".join([text for text in texts if text]) or None
        except Exception:
            return None

    def _llama_local_chat(self, system_prompt: str, user_prompt: str, temperature: float, timeout: int) -> Optional[str]:
        try:
            import requests  # type: ignore
        except Exception:
            return None

        base_url = os.getenv("LLAMA_BASE_URL", "http://localhost:11434/v1").rstrip("/")
        api_key = os.getenv("LLAMA_API_KEY", "")

        openai_url = f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

        try:
            response = requests.post(openai_url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception:
            # Fallback for native Ollama API if OpenAI-compatible path is unavailable.
            native_url = base_url.replace("/v1", "") + "/api/chat"
            native_payload = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"temperature": temperature},
            }
            try:
                response = requests.post(native_url, headers={"Content-Type": "application/json"}, json=native_payload, timeout=timeout)
                response.raise_for_status()
                return response.json().get("message", {}).get("content")
            except Exception:
                return None


def resolve_provider_model(model: str) -> Tuple[str, str]:
    config = LLMClient(model).config
    return config.provider, config.model
