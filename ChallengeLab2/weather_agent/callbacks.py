"""ADK callbacks for the weather agent.

Three callbacks are provided and wired into the agent in ``agent.py``:

* ``log_user_prompt``    - before-model: logs the incoming user prompt.
* ``validate_user_input`` - before-model: validates the prompt (Model Armor
  malicious-content screen + US-location check) and blocks the model call by
  returning an ``LlmResponse`` when the input is not acceptable.
* ``log_model_response`` - after-model: logs the model's response.

The heavy lifting for validation lives in ``validation.py`` (pure, testable
logic); this module is the thin ADK-facing layer.
"""

import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

from .validation import evaluate_user_prompt, extract_latest_user_text

logger = logging.getLogger("weather_agent")


def _response_text(llm_response: LlmResponse) -> str:
    """Extract the text from a model response, or "" if there is none."""
    content = getattr(llm_response, "content", None)
    parts = getattr(content, "parts", None) or []
    return " ".join(p.text for p in parts if getattr(p, "text", None)).strip()


def _refusal_message(reason: str) -> str:
    """Return a user-facing message explaining why a prompt was blocked."""
    if "non-US" in reason:
        return (
            "Sorry - I can only provide weather for locations in the United "
            "States, because the National Weather Service API does not cover "
            "other countries. Please ask about a US city."
        )
    if "model-armor" in reason or "flagged" in reason:
        return (
            "Sorry - I can't process that request because it was flagged by "
            "our safety filter. Please rephrase and ask about US weather."
        )
    return "Sorry - I can't process that request."


def log_user_prompt(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Before-model callback: log the incoming user prompt.

    Args:
        callback_context: The ADK callback context (unused).
        llm_request: The request about to be sent to the model.

    Returns:
        None - this callback only logs and never blocks.
    """
    text = extract_latest_user_text(llm_request.contents)
    logger.info("[USER PROMPT] %s", text)
    return None


def validate_user_input(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Before-model callback: validate the prompt and block bad input.

    Runs Model Armor malicious-content screening and a US-location check. If
    the prompt is rejected, returns an ``LlmResponse`` (which short-circuits
    the model call and is shown to the user); otherwise returns None so the
    request proceeds.

    Args:
        callback_context: The ADK callback context (unused).
        llm_request: The request about to be sent to the model.

    Returns:
        An ``LlmResponse`` to block the request, or None to allow it.
    """
    text = extract_latest_user_text(llm_request.contents)
    allowed, reason = evaluate_user_prompt(text)
    if allowed:
        return None

    logger.warning("[BLOCKED] reason=%s prompt=%r", reason, text)
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text=_refusal_message(reason))],
        )
    )


def log_model_response(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    """After-model callback: log the model's response.

    Args:
        callback_context: The ADK callback context (unused).
        llm_response: The response returned by the model.

    Returns:
        None - this callback only logs and does not modify the response.
    """
    logger.info("[MODEL RESPONSE] %s", _response_text(llm_response))
    return None
