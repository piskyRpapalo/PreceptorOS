"""Small stdlib adapter for the bounded JSON Schema channel event."""
import hashlib
import json
import re
from datetime import datetime

MAX_EVENT_BYTES = 1024
STAMPS = {"LIVE", "STALE", "STATIC", "SIMULATED", "NO_DATA", "ERROR"}


class EventRejected(ValueError):
    pass


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EventRejected("duplicate JSON key")
        result[key] = value
    return result


def validate_event(raw):
    """Return the validated event; reject the complete input on every failure."""
    if not isinstance(raw, (bytes, bytearray)):
        raise EventRejected("event must arrive as bytes")
    if len(raw) > MAX_EVENT_BYTES:
        raise EventRejected("event exceeds 1024 UTF-8 bytes; rejected whole")
    try:
        text = bytes(raw).decode("utf-8", errors="strict")
        event = json.loads(text, object_pairs_hook=_unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(
                               EventRejected("non-finite JSON number")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EventRejected("invalid UTF-8 JSON") from exc
    if not isinstance(event, dict) or set(event) != {
            "version", "ancla", "utc", "sello", "payload"}:
        raise EventRejected("event shape does not match canal_event.schema.json")
    if type(event["version"]) is not int or event["version"] != 1:
        raise EventRejected("unsupported version")
    if not isinstance(event["ancla"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", event["ancla"]):
        raise EventRejected("ancla must be a lowercase SHA-256 digest")
    if not isinstance(event["utc"], str) or not event["utc"].endswith("Z"):
        raise EventRejected("utc must be an ISO-8601 UTC timestamp")
    try:
        datetime.fromisoformat(event["utc"][:-1] + "+00:00")
    except ValueError as exc:
        raise EventRejected("invalid utc timestamp") from exc
    if event["sello"] not in STAMPS:
        raise EventRejected("unknown stamp")
    if not isinstance(event["payload"], dict):
        raise EventRejected("payload must be an object")
    return event


def event_sha256(raw):
    validate_event(raw)
    return hashlib.sha256(raw).hexdigest()
