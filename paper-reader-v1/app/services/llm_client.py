import json
import os
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Optional

from openai import OpenAI


_CURRENT_LLM_CONFIG: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "paper_reader_llm_config",
    default=None,
)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_llm_config(config: Optional[Dict[str, Any]]) -> Dict[str, str]:
    if not isinstance(config, dict):
        return {}

    cleaned = {
        "provider": _clean_text(config.get("provider")).lower(),
        "api_key": _clean_text(config.get("api_key")),
        "base_url": _clean_text(config.get("base_url")),
        "model": _clean_text(config.get("model")),
    }
    return {key: value for key, value in cleaned.items() if value}


def _resolve_llm_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    merged = _clean_llm_config(_CURRENT_LLM_CONFIG.get())
    merged.update(_clean_llm_config(config))

    provider = merged.get("provider") or _clean_text(os.getenv("LLM_PROVIDER", "")).lower()

    if provider == "ollama":
        base_url = merged.get("base_url") or _clean_text(os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        model = merged.get("model") or _clean_text(os.getenv("OLLAMA_MODEL", "qwen2.5:7b"))
        api_key = merged.get("api_key") or _clean_text(os.getenv("OLLAMA_API_KEY", "ollama")) or "ollama"
        return {
            "provider": "ollama",
            "base_url": base_url.rstrip("/"),
            "model": model,
            "api_key": api_key,
        }

    if provider == "deepseek":
        base_url = merged.get("base_url") or "https://api.deepseek.com/v1"
        model = merged.get("model") or "deepseek-chat"
        api_key = merged.get("api_key") or _clean_text(os.getenv("DEEPSEEK_API_KEY", "")) or _clean_text(os.getenv("OPENAI_API_KEY", ""))
        return {
            "provider": "deepseek",
            "base_url": base_url.rstrip("/"),
            "model": model,
            "api_key": api_key,
        }

    if provider == "kimi":
        base_url = merged.get("base_url") or "https://api.moonshot.cn/v1"
        model = merged.get("model") or "moonshot-v1-8k"
        api_key = merged.get("api_key") or _clean_text(os.getenv("KIMI_API_KEY", ""))
        return {
            "provider": "kimi",
            "base_url": base_url.rstrip("/"),
            "model": model,
            "api_key": api_key,
        }

    if provider == "qwen":
        base_url = merged.get("base_url") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        model = merged.get("model") or "qwen-plus"
        api_key = merged.get("api_key") or _clean_text(os.getenv("QWEN_API_KEY", ""))
        return {
            "provider": "qwen",
            "base_url": base_url.rstrip("/"),
            "model": model,
            "api_key": api_key,
        }

    base_url = (
        merged.get("base_url")
        or _clean_text(os.getenv("OPENAI_BASE_URL", ""))
        or _clean_text(os.getenv("OLLAMA_BASE_URL", ""))
    )
    model = (
        merged.get("model")
        or _clean_text(os.getenv("OPENAI_MODEL", ""))
        or _clean_text(os.getenv("OLLAMA_MODEL", "qwen2.5:7b"))
        or "qwen2.5:7b"
    )
    api_key = (
        merged.get("api_key")
        or _clean_text(os.getenv("OPENAI_API_KEY", ""))
        or _clean_text(os.getenv("DEEPSEEK_API_KEY", ""))
        or "ollama"
    )

    if base_url:
        return {
            "provider": provider or "openai_compatible",
            "base_url": base_url.rstrip("/"),
            "model": model,
            "api_key": api_key,
        }

    return {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "model": _clean_text(os.getenv("OLLAMA_MODEL", "qwen2.5:7b")) or "qwen2.5:7b",
        "api_key": _clean_text(os.getenv("OLLAMA_API_KEY", "ollama")) or "ollama",
    }


def get_effective_llm_info(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    resolved = _resolve_llm_config(config)
    return {
        "provider": resolved.get("provider", ""),
        "base_url": resolved.get("base_url", ""),
        "model": resolved.get("model", ""),
        "has_api_key": bool(resolved.get("api_key")),
        "uses_local_ollama": resolved.get("provider") == "ollama",
    }


@contextmanager
def temporary_llm_config(config: Optional[Dict[str, Any]] = None):
    token = _CURRENT_LLM_CONFIG.set(_clean_llm_config(config))
    try:
        yield
    finally:
        _CURRENT_LLM_CONFIG.reset(token)


def _build_client(config: Optional[Dict[str, Any]] = None) -> OpenAI:
    resolved = _resolve_llm_config(config)
    base_url = resolved["base_url"]

    # The OpenAI-compatible Ollama endpoint lives under /v1. Keep external
    # providers untouched unless the caller already supplied the full path.
    if resolved.get("provider") == "ollama" and not base_url.rstrip("/").endswith("/v1"):
        base_url = f"{base_url.rstrip('/')}/v1"

    return OpenAI(
        base_url=base_url,
        api_key=resolved["api_key"] or "ollama",
    )


def _get_model_name(config: Optional[Dict[str, Any]] = None) -> str:
    resolved = _resolve_llm_config(config)
    return resolved["model"]


def chat_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    client = _build_client(config)
    model_name = _get_model_name(config)

    response = client.chat.completions.create(
        model=model_name,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or ""
    content = content.strip()

    try:
        return json.loads(content)
    except Exception:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start:end + 1])

        raise ValueError(f"Model response is not valid JSON: {content[:500]}")
