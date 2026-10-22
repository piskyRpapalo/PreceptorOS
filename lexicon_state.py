"""Byte-bounded state envelopes for lexical projections."""
from dataclasses import dataclass
import json
from typing import Any, Mapping


MAX_PAYLOAD_BYTES = 1024
SCHEMA = "preceptoros.lexical-projection/1"
STATUSES = frozenset({"LIVE", "NO_DATA", "ERROR"})


def compact_json(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("state is not finite JSON data") from exc


@dataclass(frozen=True)
class LexiconState:
    status: str
    payload: Mapping[str, Any] | None = None
    cause: str | None = None
    measured_bytes: int = 0

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError("unsupported state stamp")
        if self.status == "NO_DATA":
            if not isinstance(self.cause, str) or not self.cause.strip() or self.payload is not None:
                raise ValueError("NO_DATA requires a cause and no payload")
        elif self.status == "ERROR":
            if not isinstance(self.cause, str) or not self.cause.strip() or self.payload is not None:
                raise ValueError("ERROR requires a cause and no payload")
        elif not isinstance(self.payload, Mapping) or self.cause is not None:
            raise ValueError("LIVE state requires payload and no cause")
        if type(self.measured_bytes) is not int or self.measured_bytes < 0:
            raise ValueError("byte count must be a non-negative integer")

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"v": SCHEMA, "st": self.status,
                                  "bytes": self.measured_bytes}
        if self.payload is not None:
            result["p"] = dict(self.payload)
        if self.cause is not None:
            result["causa"] = self.cause
        return result

    def to_json(self) -> bytes:
        return compact_json(self.as_dict())


def measured(payload: Mapping[str, Any], status: str = "LIVE") -> LexiconState:
    if status != "LIVE":
        raise ValueError("measured state needs LIVE")
    body = dict(payload)
    size = len(compact_json(body))
    if size >= MAX_PAYLOAD_BYTES:
        return LexiconState("NO_DATA", cause="payload is 1024 B or larger",
                            measured_bytes=size)
    return LexiconState(status, payload=body, measured_bytes=size)


def unavailable(cause: str, status: str = "NO_DATA") -> LexiconState:
    if status not in {"NO_DATA", "ERROR"}:
        raise ValueError("unavailable state needs NO_DATA or ERROR")
    return LexiconState(status, cause=cause)
