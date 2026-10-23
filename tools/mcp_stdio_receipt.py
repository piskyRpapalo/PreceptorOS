#!/usr/bin/env python3
"""Launch the declared local MCP server and emit a scrubbed wire receipt."""
import hashlib
import base64
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

LIMIT = 1024
ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "mcp-client-receipt.json"


class ReceiptError(RuntimeError):
    pass


def _line(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                      sort_keys=True).encode("utf-8") + b"\n"


def _read_line(process, timeout):
    fd = process.stdout.fileno()
    data = bytearray()
    deadline = time.monotonic() + timeout
    while len(data) < LIMIT:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([fd], [], [], remaining)[0]:
            raise ReceiptError("NO_DATA · response timeout")
        chunk = os.read(fd, min(256, LIMIT - len(data)))
        if not chunk:
            raise ReceiptError("NO_DATA · server closed stdout")
        data.extend(chunk)
        if data.endswith(b"\n"):
            if len(data) >= LIMIT:
                raise ReceiptError("NO_DATA · response reaches 1024-byte line ceiling")
            try:
                return json.loads(data[:-1].decode("utf-8")), len(data)
            except (UnicodeDecodeError, ValueError) as exc:
                raise ReceiptError("NO_DATA · invalid UTF-8 or JSON response") from exc
    raise ReceiptError("NO_DATA · response reaches 1024-byte line ceiling")


def _exchange(process, message, timeout):
    encoded = _line(message)
    if len(encoded) >= LIMIT:
        raise ReceiptError("NO_DATA · request reaches 1024-byte line ceiling")
    process.stdin.write(encoded)
    process.stdin.flush()
    response, response_bytes = _read_line(process, timeout)
    if not isinstance(response, dict) or response.get("id") != message.get("id"):
        raise ReceiptError("NO_DATA · JSON-RPC response id mismatch")
    return response, len(encoded), response_bytes


def _validate_config(config):
    fields = {"schema", "server", "transport", "protocol_version",
              "request_limit_bytes_including_lf", "bubble_fixture",
              "bubble_fixture_sha256", "exchange", "tool_calls"}
    if (not isinstance(config, dict) or set(config) != fields
            or config.get("schema") != "preceptoros.mcp-client-receipt/1"
            or config.get("server") != "mcp_thegame_server.py"
            or config.get("transport") != "stdio"
            or config.get("protocol_version") != "2026-07-28"
            or config.get("request_limit_bytes_including_lf") != LIMIT
            or config.get("bubble_fixture") != "tests/fixtures/bubble-frame.json"
            or not isinstance(config.get("bubble_fixture_sha256"), str)
            or len(config["bubble_fixture_sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in config["bubble_fixture_sha256"])
            or config.get("exchange") != ["initialize", "notifications/initialized", "ping", "tools/list"]
            or config.get("tool_calls") is not False):
        raise ReceiptError("NO_DATA · client launch contract is not the closed declaration")


def run_receipt(command=None, timeout=3):
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    _validate_config(config)
    argv = command or [sys.executable, str(ROOT / config["server"])]
    process = subprocess.Popen(argv, cwd=ROOT, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               bufsize=0)
    sizes = []
    try:
        initialized, sent, received = _exchange(process, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": config["protocol_version"],
                       "capabilities": {}, "clientInfo": {
                           "name": "mcp-stdio-receipt", "version": "1"}}}, timeout)
        sizes.append({"method": "initialize", "request_bytes": sent,
                      "response_bytes": received})
        result = initialized.get("result", {})
        if result.get("protocolVersion") != config["protocol_version"]:
            raise ReceiptError("NO_DATA · protocol version mismatch")
        if result.get("serverInfo") != {"name": "preceptoros-thegame", "version": "1.0.0"}:
            raise ReceiptError("NO_DATA · declared server identity mismatch")

        notice = _line({"jsonrpc": "2.0", "method": "notifications/initialized"})
        if len(notice) >= LIMIT:
            raise ReceiptError("NO_DATA · notification reaches 1024-byte line ceiling")
        process.stdin.write(notice)
        process.stdin.flush()

        ping, sent, received = _exchange(process, {
            "jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}}, timeout)
        if "error" in ping:
            raise ReceiptError("NO_DATA · ping rejected")
        sizes.append({"method": "ping", "request_bytes": sent,
                      "response_bytes": received})

        listing, sent, received = _exchange(process, {
            "jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}, timeout)
        tools = listing.get("result", {}).get("tools")
        if not isinstance(tools, list) or any(not isinstance(t, dict) for t in tools):
            raise ReceiptError("NO_DATA · tool inventory missing or invalid")
        names = [t.get("name") for t in tools]
        if any(not isinstance(name, str) for name in names) or len(names) != len(set(names)):
            raise ReceiptError("NO_DATA · tool inventory names invalid or duplicated")
        sizes.append({"method": "tools/list", "request_bytes": sent,
                      "response_bytes": received})

        frame = (ROOT / config["bubble_fixture"]).read_bytes()
        frame_hash = hashlib.sha256(frame).hexdigest()
        if frame_hash != config.get("bubble_fixture_sha256") or len(frame) >= LIMIT:
            raise ReceiptError("NO_DATA · Bubble probe fixture digest or size mismatch")
        probe, sent, received = _exchange(process, {
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "bubble_frame.validate",
                       "arguments": {"frame": base64.b64encode(frame).decode("ascii")}}}, timeout)
        rejection = probe.get("error", {})
        if rejection.get("code") != -32602:
            raise ReceiptError("NO_DATA · Bubble frame probe was not rejected as an absent capability")
        sizes.append({"method": "bubble_frame.validate (absent capability)",
                      "request_bytes": sent, "response_bytes": received})
        process.stdin.close()
        code = process.wait(timeout=timeout)
        if code != 0:
            raise ReceiptError("NO_DATA · declared server exited nonzero")
        return {
            "schema": "preceptoros.mcp-client-receipt/1",
            "server": config["server"], "transport": "stdio",
            "protocol_version": result["protocolVersion"],
            "server_name": result["serverInfo"].get("name", "NO_DATA"),
            "tool_count": len(names),
            "tool_inventory_sha256": hashlib.sha256(_line(tools)[:-1]).hexdigest(),
            "exchange": sizes,
            "max_request_bytes": max(x["request_bytes"] for x in sizes),
            "max_response_bytes": max(x["response_bytes"] for x in sizes),
            "limit_bytes_including_lf": LIMIT,
            "bubble_frame_bytes": len(frame), "bubble_frame_sha256": frame_hash,
            "bubble_frame_probe_request_bytes": sent,
            "bubble_frame_capability": "NO_DATA · server rejected undeclared tool",
            "tool_calls": 0, "process_exit": code,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReceiptError("NO_DATA · local server process unavailable or timed out") from exc
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream and not stream.closed:
                stream.close()


def main():
    try:
        print(json.dumps(run_receipt(), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")))
        return 0
    except (ReceiptError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
