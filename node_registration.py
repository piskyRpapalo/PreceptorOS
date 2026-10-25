"""Loopback-only preview receiver for the proposed node-registration flow.

This module is deliberately dry-run only. It never creates a signed credential,
verifies a real signature, persists a record, or calls the public Door 1 route.
"""
from __future__ import annotations

import json
import re

SCHEMA = "preceptoros.node-registration-request/1"
NODE = re.compile(r"^nodo\.[0-9]{1,6}\.[a-z0-9][a-z0-9-]{0,30}$")
MAX_BYTES = 1024


def receive_preview(envelope):
    """Return a synthetic node receipt and catalog count; never persist it."""
    try:
        size = len(json.dumps(envelope, ensure_ascii=False,
                              separators=(",", ":")).encode("utf-8"))
    except (TypeError, ValueError):
        return 400, {"state": "rejected", "cause": "invalid_json"}
    if size > MAX_BYTES:
        return 413, {"state": "rejected", "cause": "request_too_large"}
    if not isinstance(envelope, dict) or set(envelope) != {"mode", "request"}:
        return 400, {"state": "rejected", "cause": "invalid_envelope"}
    request = envelope["request"]
    if envelope["mode"] != "test_stub_only":
        return 403, {"state": "rejected", "cause": "dry_run_only"}
    if not isinstance(request, dict) or set(request) != {"schema", "node", "signer", "cedula_sha256"}:
        return 400, {"state": "rejected", "cause": "invalid_request"}
    if request["schema"] != SCHEMA or not NODE.fullmatch(str(request["node"])):
        return 422, {"state": "rejected", "cause": "invalid_request"}
    if not re.fullmatch(r"[0-9a-f]{64}", str(request["cedula_sha256"])):
        return 422, {"state": "rejected", "cause": "invalid_request"}
    if request["signer"] != {"state": "stub", "label": "test_only_no_signature"}:
        return 422, {"state": "rejected", "cause": "real_signer_not_implemented"}
    return 200, {
        "state": "received",
        "receipt": "test_stub_only",
        "receipt_id": "test-receipt",
        "cedula_sha256": request["cedula_sha256"],
        "catalog": {"state": "stub_not_published", "count": 1},
        "persisted": False,
    }
