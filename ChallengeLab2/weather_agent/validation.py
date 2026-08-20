"""Input-validation and content-screening logic for the weather agent.

This module holds the *pure* validation logic used by the ADK callbacks in
``callbacks.py``. It deliberately imports no ADK types, and takes its external
dependencies (the geocoder and the Model Armor call) as injectable arguments,
so every branch can be unit-tested without the ADK, the network, or the
``google-cloud-modelarmor`` library installed.

Two checks are provided:

* **Malicious-input screening** via Google Cloud Model Armor
  (``screen_user_prompt``).
* **US-location enforcement** via the Geocoding API country code
  (``us_location_check``) - the National Weather Service API only covers the
  United States.
"""

import logging
import os
from typing import Callable, Optional, Tuple

logger = logging.getLogger("weather_agent")


def extract_latest_user_text(contents) -> str:
    """Return the text of the most recent user message in an ADK request.

    Args:
        contents: The ``llm_request.contents`` sequence. Each item is expected
            to have a ``role`` attribute and a ``parts`` list whose items may
            carry a ``text`` attribute.

    Returns:
        The concatenated text of the last ``user``-role message, or "" if
        there is no user text.
    """
    for content in reversed(list(contents or [])):
        if getattr(content, "role", None) == "user":
            parts = getattr(content, "parts", None) or []
            texts = [p.text for p in parts if getattr(p, "text", None)]
            if texts:
                return " ".join(texts).strip()
    return ""


def us_location_check(
    text: str,
    geocode: Optional[Callable[[str], dict]] = None,
) -> Tuple[bool, str]:
    """Check that the user's request is not for a confirmed non-US location.

    The National Weather Service API only covers the United States, so a
    request that geocodes to another country is rejected. Input that cannot be
    geocoded to a definite country is *allowed* through (the agent's own tools
    will handle it), to avoid false rejections of valid US queries.

    Args:
        text: The user's prompt text.
        geocode: Optional geocoding function (defaults to the real
            ``geocode_place`` tool). Injected in tests.

    Returns:
        ``(allowed, reason)`` - ``allowed`` is False only when the location
        geocodes to a country other than the US.
    """
    if geocode is None:
        from .tools import geocode_place as geocode

    result = geocode(text)
    country = result.get("country") if isinstance(result, dict) else None
    if result.get("status") == "success" and country and country != "US":
        return False, f"non-US location (country={country})"
    return True, "us-or-undetermined"


def _real_model_armor_call(text: str, template_id: str) -> str:
    """Call Google Cloud Model Armor and return the filter match-state name.

    Args:
        text: The user prompt to screen.
        template_id: The Model Armor template id (short id, not full path).

    Returns:
        The name of the ``filter_match_state`` enum, e.g. ``"MATCH_FOUND"`` or
        ``"NO_MATCH_FOUND"``.
    """
    from google.api_core.client_options import ClientOptions
    from google.cloud import modelarmor_v1

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("MODEL_ARMOR_LOCATION", "us-central1")

    client = modelarmor_v1.ModelArmorClient(
        client_options=ClientOptions(
            api_endpoint=f"modelarmor.{location}.rep.googleapis.com"
        )
    )
    request = modelarmor_v1.SanitizeUserPromptRequest(
        name=f"projects/{project}/locations/{location}/templates/{template_id}",
        user_prompt_data=modelarmor_v1.DataItem(text=text),
    )
    response = client.sanitize_user_prompt(request=request)
    return response.sanitization_result.filter_match_state.name


def screen_user_prompt(
    text: str,
    armor_call: Optional[Callable[[str, str], str]] = None,
    template_id: Optional[str] = None,
) -> Tuple[bool, str]:
    """Screen a user prompt for malicious content with Google Cloud Model Armor.

    Args:
        text: The user's prompt text.
        armor_call: Optional callable ``(text, template_id) -> match_state_name``
            (defaults to the real Model Armor call). Injected in tests.
        template_id: Optional Model Armor template id (defaults to the
            ``MODEL_ARMOR_TEMPLATE_ID`` environment variable).

    Returns:
        ``(is_safe, reason)``. If Model Armor is not configured or errors, the
        prompt is allowed through (``is_safe=True``) and a reason is logged.
    """
    template_id = template_id or os.getenv("MODEL_ARMOR_TEMPLATE_ID")
    if not template_id:
        logger.warning("Model Armor template not configured; skipping screen.")
        return True, "model-armor-not-configured"

    call = armor_call or _real_model_armor_call
    try:
        match_state = call(text, template_id)
    except Exception as exc:  # noqa: BLE001 - never let screening crash the agent
        logger.warning("Model Armor call failed (%s); allowing prompt.", exc)
        return True, "model-armor-error"

    if match_state == "MATCH_FOUND":
        return False, "flagged-by-model-armor"
    return True, "clean"


def evaluate_user_prompt(
    text: str,
    geocode: Optional[Callable[[str], dict]] = None,
    armor_call: Optional[Callable[[str, str], str]] = None,
    template_id: Optional[str] = None,
) -> Tuple[bool, str]:
    """Run all input validation for a user prompt.

    Malicious-content screening runs first (security), then the US-location
    check. An empty prompt is allowed (nothing to validate yet).

    Args:
        text: The user's prompt text.
        geocode: Optional geocoder for the US check (injected in tests).
        armor_call: Optional Model Armor call (injected in tests).
        template_id: Optional Model Armor template id.

    Returns:
        ``(allowed, reason)`` - ``allowed`` is False if the prompt is flagged
        as malicious or geocodes to a non-US country.
    """
    if not text:
        return True, "empty-prompt"

    is_safe, reason = screen_user_prompt(text, armor_call, template_id)
    if not is_safe:
        return False, reason

    return us_location_check(text, geocode)
