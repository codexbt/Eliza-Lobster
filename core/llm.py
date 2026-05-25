"""core/llm.py
Multi-provider LLM abstraction for Kairos.
Supports:
- Ollama (local, no key)
- Any OpenAI-compatible API (OpenAI, Groq, xAI/Grok, DeepSeek, Together.ai, Fireworks, etc.)
  by providing API key + base_url (auto or manual)

Auto-fetch models via .list_models() after entering key.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger("core.llm")

# Known providers with their OpenAI-compatible endpoints and typical env var
KNOWN_PROVIDERS: dict[str, dict[str, Any]] = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "env": None,
        "requires_key": False,
        "description": "Local Ollama (free, private)",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "env": "OPENAI_API_KEY",
        "requires_key": True,
        "description": "OpenAI (GPT-4o, o1, etc.)",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env": "GROQ_API_KEY",
        "requires_key": True,
        "description": "Groq (fast Llama-3.1, Mixtral, Gemma2)",
    },
    "xai": {
        "base_url": "https://api.x.ai/v1",
        "env": "XAI_API_KEY",
        "requires_key": True,
        "description": "xAI Grok (Grok-2, Grok-3)",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "env": "DEEPSEEK_API_KEY",
        "requires_key": True,
        "description": "DeepSeek (DeepSeek-V3, Coder)",
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "env": "TOGETHER_API_KEY",
        "requires_key": True,
        "description": "Together.ai (many open models)",
    },
    "fireworks": {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "env": "FIREWORKS_API_KEY",
        "requires_key": True,
        "description": "Fireworks.ai",
    },
}


class BaseLLMProvider:
    """Abstract LLM provider."""

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.6,
        max_tokens: int = 8192,
    ) -> str:
        raise NotImplementedError

    def list_models(self) -> list[str]:
        """Return list of available model IDs/names. May require auth."""
        raise NotImplementedError

    def is_ready(self) -> bool:
        return True


class OllamaProvider(BaseLLMProvider):
    """Ollama local provider using official ollama Python client."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or "http://localhost:11434"
        self.client = None
        try:
            from ollama import Client

            self.client = Client(host=self.base_url)
        except ImportError:
            logger.warning("ollama package not installed - pip install ollama")

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.6,
        max_tokens: int = 8192,
    ) -> str:
        if self.client is None:
            return "ERROR: ollama not installed or not running"
        try:
            resp = self.client.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_ctx": min(max_tokens, 32768),
                },
            )
            return resp.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            return f"ERROR: {e}"

    def list_models(self) -> list[str]:
        if self.client is None:
            return []
        try:
            result = self.client.list()
            models = result.get("models", []) if isinstance(result, dict) else []
            return [m.get("name", m.get("model", "")) for m in models if m]
        except Exception as e:
            logger.debug(f"Ollama list failed: {e}")
            return []


class OpenAICompatibleProvider(BaseLLMProvider):
    """Any provider using OpenAI /v1/chat/completions + /v1/models (most modern APIs)."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                logger.warning("openai package not installed - pip install openai")
            except Exception as e:
                logger.error(f"OpenAI client init failed: {e}")

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.6,
        max_tokens: int = 8192,
    ) -> str:
        if self.client is None:
            return "ERROR: No API key or openai package missing for remote provider"
        try:
            resp = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content if resp.choices else ""
            return content or ""
        except Exception as e:
            logger.error(f"Remote LLM call failed: {e}")
            return f"ERROR: {str(e)[:300]}"

    def list_models(self) -> list[str]:
        if self.client is None:
            return []
        try:
            models = self.client.models.list()
            # Return all model IDs (filtering can be done in UI)
            ids = [m.id for m in getattr(models, "data", []) if hasattr(m, "id")]
            return sorted(ids) if ids else []
        except Exception as e:
            logger.error(f"list_models failed for {self.base_url}: {e}")
            return []


class LLMManager:
    """Central manager. Loads config, picks provider, supports model listing + selection."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.config = self._load_config()
        self._active_provider: Optional[BaseLLMProvider] = None
        self._current_key: Optional[str] = None

    def _load_config(self) -> dict[str, Any]:
        cfg_path = self.project_root / "config.yaml"
        try:
            with open(cfg_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _save_llm_config(self, updates: dict[str, Any]) -> bool:
        """Persist llm section into config.yaml"""
        cfg_path = self.project_root / "config.yaml"
        try:
            cfg = dict(self.config)  # shallow copy
            if "llm" not in cfg or not isinstance(cfg.get("llm"), dict):
                cfg["llm"] = {}
            cfg["llm"].update(updates)
            with open(cfg_path, "w", encoding="utf-8") as f:
                yaml.dump(cfg, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
            self.config = cfg
            self._active_provider = None  # force reload
            return True
        except Exception as e:
            logger.error(f"Failed writing config.yaml: {e}")
            return False

    def get_provider_name(self) -> str:
        llm = self.config.get("llm", {}) or {}
        prov = (llm.get("provider") or "").lower().strip()
        if prov in KNOWN_PROVIDERS:
            return prov
        # backward compat: if old ollama section exists and no new llm
        if self.config.get("ollama") and not prov:
            return "ollama"
        return "ollama"

    def get_default_model(self) -> str:
        llm = self.config.get("llm", {}) or {}
        model = llm.get("default_model")
        if model:
            return model
        # old config
        return self.config.get("ollama", {}).get("default_model", "qwen2.5-coder:7b")

    def get_base_url(self, provider: Optional[str] = None) -> str:
        p = (provider or self.get_provider_name()).lower()
        llm = self.config.get("llm", {}) or {}
        if llm.get("base_url"):
            return llm["base_url"]
        return KNOWN_PROVIDERS.get(p, {}).get("base_url", "http://localhost:11434")

    def get_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        p = (provider or self.get_provider_name()).lower()
        llm = self.config.get("llm", {}) or {}
        # explicit in config (not recommended for git, but user requested entering keys)
        if llm.get("api_key"):
            return llm["api_key"]
        env_name = KNOWN_PROVIDERS.get(p, {}).get("env")
        if env_name:
            return os.getenv(env_name)
        return None

    def _build_provider(self, provider: Optional[str] = None, api_key: Optional[str] = None) -> BaseLLMProvider:
        p = (provider or self.get_provider_name()).lower()
        key = api_key or self.get_api_key(p)
        base = self.get_base_url(p)

        if p == "ollama" or not key:
            return OllamaProvider(base_url=base)
        else:
            return OpenAICompatibleProvider(api_key=key or "", base_url=base)

    def get_provider(self, provider: Optional[str] = None, api_key: Optional[str] = None) -> BaseLLMProvider:
        """Return (possibly cached) provider instance."""
        if provider is None and api_key is None and self._active_provider is not None:
            return self._active_provider
        prov = self._build_provider(provider, api_key)
        if provider is None and api_key is None:
            self._active_provider = prov
        return prov

    def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.6,
        max_tokens: int = 8192,
    ) -> str:
        prov = self.get_provider()
        m = model or self.get_default_model()
        return prov.chat(messages, m, temperature=temperature, max_tokens=max_tokens)

    def list_models(self, provider: Optional[str] = None, api_key: Optional[str] = None) -> list[str]:
        """Fetch models. Pass api_key to test a new key without saving."""
        prov = self.get_provider(provider=provider, api_key=api_key)
        return prov.list_models()

    def set_active_model(self, provider: str, model: str, api_key: Optional[str] = None) -> bool:
        """Persist choice + optional key to config.yaml and switch active provider."""
        updates: dict[str, Any] = {"provider": provider, "default_model": model}
        if api_key:
            updates["api_key"] = api_key
        ok = self._save_llm_config(updates)
        if ok:
            self._active_provider = None
        return ok

    def get_supported_providers(self) -> dict[str, str]:
        """For UI: name -> description"""
        return {k: v["description"] for k, v in KNOWN_PROVIDERS.items()}


# Singleton factory (simple, per process)
_manager_cache: dict[str, LLMManager] = {}


def get_llm_manager(project_root: str = ".") -> LLMManager:
    key = str(Path(project_root).resolve())
    if key not in _manager_cache:
        _manager_cache[key] = LLMManager(project_root)
    return _manager_cache[key]
