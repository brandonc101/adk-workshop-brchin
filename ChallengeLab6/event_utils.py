"""Pure helpers for parsing Vertex AI Agent Engine streamed events.

Kept free of any cloud imports so the parsing logic can be unit-tested in
isolation. Agent Engine's ``stream_query`` yields events that may be dicts or
objects, so these helpers read fields from either shape.
"""


def get_field(obj, key):
    """Read ``key`` from a dict or as an object attribute.

    Args:
        obj: A dict, an object, or None.
        key: The field name to read.

    Returns:
        The value, or None if it is absent.
    """
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def extract_texts(event) -> list:
    """Return the non-empty text parts of a streamed Agent Engine event.

    Args:
        event: One event from ``stream_query`` (dict or object) with an
            optional ``content`` that has ``parts`` carrying ``text``.

    Returns:
        A list of stripped text strings (empty if the event has no text).
    """
    content = get_field(event, "content")
    parts = get_field(content, "parts") if content is not None else None
    texts = []
    for part in parts or []:
        text = get_field(part, "text")
        if text and str(text).strip():
            texts.append(str(text).strip())
    return texts
