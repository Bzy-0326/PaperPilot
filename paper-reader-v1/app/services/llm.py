from typing import Any, Dict, Optional

from app.services.llm_client import chat_json


def call_ollama_json(
    system_prompt: str,
    user_prompt: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # Historical name kept for compatibility. The implementation now supports
    # Ollama and user-supplied OpenAI-compatible providers.
    return chat_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.2,
        config=config,
    )
