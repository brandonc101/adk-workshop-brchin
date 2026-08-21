"""Model selection shared by the agents.

The coordinator and weather agents honor the ``MODEL_BACKEND`` environment
variable (Gemini default; Claude/GPT via LiteLLM). The search agent must use a
Gemini model, because the built-in Google Search tool only supports Gemini.
"""

import os

from google.adk.models.lite_llm import LiteLlm


def gemini_model() -> str:
    """Return the Gemini model id (used by the search agent)."""
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def resolve_model():
    """Return the model for the coordinator/weather agent per MODEL_BACKEND.

    Returns:
        A Gemini model-name ``str`` or a ``LiteLlm`` instance (Claude/GPT).
    """
    backend = os.getenv("MODEL_BACKEND", "gemini").lower()

    if backend == "gemini":
        return gemini_model()

    if backend in ("claude", "anthropic"):
        model_id = os.getenv("CLAUDE_MODEL", "vertex_ai/claude-sonnet-4-5")
        if model_id.startswith("vertex_ai/"):
            os.environ.setdefault(
                "VERTEXAI_PROJECT", os.getenv("GOOGLE_CLOUD_PROJECT", "")
            )
            os.environ.setdefault(
                "VERTEXAI_LOCATION", os.getenv("CLAUDE_LOCATION", "us-east5")
            )
        return LiteLlm(model=model_id)

    if backend in ("gpt", "openai"):
        return LiteLlm(model=os.getenv("OPENAI_MODEL", "openai/gpt-4o"))

    raise ValueError(
        f"Unknown MODEL_BACKEND '{backend}'. Use 'gemini', 'claude', or 'gpt'."
    )
