"""Bound complete JSON-RPC UTF-8 lines, including the newline delimiter."""
import json

LIMIT = 1024


def _bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                      sort_keys=True).encode("utf-8") + b"\n"


def _error(code, cause, request_id=None):
    return {"jsonrpc": "2.0", "id": request_id,
            "error": {"code": code, "message": "NO_DATA · " + cause}}


def _reply(response):
    try:
        encoded = _bytes(response)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return _bytes(_error(-32000, "response serialization failed"))
    if len(encoded) < LIMIT:
        return encoded
    error = _error(-32000, "response reaches the 1024-byte line ceiling",
                   response.get("id"))
    encoded = _bytes(error)
    if len(encoded) >= LIMIT:
        error["id"] = None
        encoded = _bytes(error)
    return encoded


def serve(source, sink, handle):
    """Binary streams only; oversized lines are drained without dispatch."""
    initialized = False
    while True:
        line = source.readline(LIMIT)
        if not line:
            return 0
        if len(line) >= LIMIT:
            # Keep memory bounded and resume only at the next line boundary.
            while line and not line.endswith(b"\n"):
                line = source.readline(LIMIT)
            response = _error(-32600, "request reaches the 1024-byte line ceiling")
        elif not line.endswith(b"\n"):
            response = _error(-32700, "incomplete line at EOF")
        else:
            try:
                request = json.loads(line.decode("utf-8"))
                response, initialized = handle(request, initialized)
            except (ValueError, TypeError, UnicodeError, RecursionError):
                response = _error(-32700, "invalid UTF-8 or JSON")
        if response is not None:
            sink.write(_reply(response))
            sink.flush()
