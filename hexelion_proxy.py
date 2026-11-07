"""Bounded loopback proxy for the Hexelion station; no configured target is NO_DATA."""
from __future__ import annotations

import ipaddress
import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit

import hexelion_book as _hexelion_book

ENDPOINT_ENV = "PRECEPTOROS_HEXELION_ENDPOINT"
MODEL = "hexelion:latest"
PROBE_TIMEOUT_S = 3
GENERATE_TIMEOUT_S = 120
MAX_RESPONSE_B = 65536
MAX_PROMPT_B = _hexelion_book.MAX_PROMPT_B


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _base(endpoint):
    if not endpoint:
        return None, "station_endpoint_not_configured"
    try:
        parts = urlsplit(endpoint)
        if (parts.scheme != "http" or parts.username or parts.password or
                parts.query or parts.fragment or parts.path not in ("", "/")):
            return None, "station_endpoint_invalid"
        ip = ipaddress.ip_address(parts.hostname or "")
        if not (ip == ipaddress.ip_address("127.0.0.1") or ip == ipaddress.ip_address("::1")):
            return None, "station_loopback_required"
        port = parts.port
        if port is None or not 1 <= port <= 65535:
            return None, "station_endpoint_invalid"
        host = "[::1]" if ip.version == 6 else "127.0.0.1"
        return urlunsplit(("http", f"{host}:{port}", "", "", "")), None
    except (ValueError, TypeError):
        return None, "station_endpoint_invalid"


def _read_json(response):
    with response:
        raw = response.read(MAX_RESPONSE_B + 1)
    if len(raw) > MAX_RESPONSE_B:
        raise ValueError("response_too_large")
    return json.loads(raw.decode("utf-8", "strict"))


def _failure(exc):
    if isinstance(exc, TimeoutError):
        return "station_timeout"
    if isinstance(exc, urllib.error.HTTPError):
        return "station_rejected_request"
    if isinstance(exc, urllib.error.URLError):
        return "station_unavailable"
    if isinstance(exc, (json.JSONDecodeError, UnicodeError)):
        return "station_invalid_json"
    if isinstance(exc, ValueError):
        return str(exc) if str(exc) == "response_too_large" else "station_invalid_response"
    return "station_unavailable"


def ask(text, *, endpoint=None, opener=None, clock=time.monotonic):
    """Probe tags, then generate once. Results contain no target or exception text."""
    base, cause = _base(os.environ.get(ENDPOINT_ENV) if endpoint is None else endpoint)
    if cause:
        return {"estado": "NO_DATA", "causa": cause}
    if type(text) is not str or not text.strip():
        return {"estado": "NO_DATA", "causa": "message_invalid"}
    try:
        if len(text.encode("utf-8", "strict")) > MAX_PROMPT_B:
            return {"estado": "NO_DATA", "causa": "prompt_exceeds_context_budget"}
    except UnicodeError:
        return {"estado": "NO_DATA", "causa": "prompt_invalid_utf8"}

    open_url = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect()).open
    try:
        probe_started = clock()
        tags_req = urllib.request.Request(base + "/api/tags", headers={"Accept": "application/json"})
        tags = _read_json(open_url(tags_req, timeout=PROBE_TIMEOUT_S))
        probe_elapsed = clock() - probe_started
        if not isinstance(probe_elapsed, (int, float)) or probe_elapsed < 0 or probe_elapsed > PROBE_TIMEOUT_S:
            return {"estado": "NO_DATA", "causa": "station_probe_timeout"}
        models = tags.get("models") if isinstance(tags, dict) else None
        if not isinstance(models, list) or not any(
                isinstance(item, dict) and item.get("name") == MODEL for item in models):
            return {"estado": "NO_DATA", "causa": "station_model_unavailable"}

        payload = json.dumps({"model": MODEL, "prompt": text, "stream": False,
                              "think": "low", "options": {"num_predict": 512}},
                             ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        req = urllib.request.Request(base + "/api/generate", data=payload,
                                     headers={"Content-Type": "application/json",
                                              "Accept": "application/json"}, method="POST")
        answer = _read_json(open_url(req, timeout=GENERATE_TIMEOUT_S))
        if not isinstance(answer, dict) or answer.get("model") != MODEL:
            return {"estado": "NO_DATA", "causa": "station_model_unconfirmed"}
        response = answer.get("response")
        duration_ns = answer.get("total_duration")
        if not isinstance(response, str) or not response.strip():
            return {"estado": "NO_DATA", "causa": "station_returned_no_text"}
        if type(duration_ns) is not int or duration_ns <= 0:
            return {"estado": "NO_DATA", "causa": "generation_duration_unmeasured"}
        generation_ms = duration_ns / 1_000_000
        if len(response.encode("utf-8")) > 640:
            return {"estado": "NO_DATA", "causa": "station_response_exceeds_receipt_budget"}
        return {"estado": "MEASURED", "texto": response.strip(),
                "modelo": MODEL, "ms": generation_ms}
    except Exception as exc:
        return {"estado": "NO_DATA", "causa": _failure(exc)}
