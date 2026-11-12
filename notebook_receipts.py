"""Notebook receipts producer · private MCP audit log -> sanitized local projection.

The native MCP server appends one receipt per command to a private JSONL file.
That file holds the full command text, so it must never be served. This module
reads it locally and writes `<home>/notebook/receipts.json`: for each receipt
only its time, tool, command fingerprint, return code, duration and output
size, plus a fingerprint of the sanitized record itself.

What a receipt proves: that a command ran and how it ended. It does not prove
the output was correct, that a worker is alive, or that anyone reviewed it. So
the states are:

  DECLARED   a recent execution receipt; the result is not independently checked
  STALE      the same, older than FRESH_S seconds
  VERIFIED   only when the caller passes the receipt's fingerprint as checked
  NO_DATA    with its cause (missing file, future timestamp, nothing valid...)

Nothing in the tree records independent checks yet, so in real use VERIFIED
does not appear. No network, no subprocess, no scheduler, no signing. The
reader of the Notebook tab is a separate module and is not changed here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

SCHEMA = "preceptoros.notebook-receipts/0"
SOURCE = "mcp-native-audit"
MAX_SOURCE = 1 << 20      # read at most the last 1 MiB of the log
MAX_RECEIPTS = 20
MAX_OUT = 8192            # the projection stays under 8 KiB
FRESH_S = 600

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_TOOL = re.compile(r"^[a-z][a-z_]{0,23}$")
_CMD_SHA = re.compile(r"^[0-9a-f]{16}$")
_INTS = {"rc": (-255, 255), "ms": (0, 3_600_000), "out_bytes": (0, 1 << 31)}
_VOICE = re.compile(r"^[a-z][a-z0-9-]{1,23}$")


def optional(raw):
    """S-3 receipts (2026-11-12) say WHO acted (`voz`) and whether the fence refused it (`denied`). Both are optional:
    a receipt without them keeps its old fingerprint. The refusal cause is never copied (it can hold typed text)."""
    extra = {}
    voice = raw.get("voz", raw.get("voice"))
    if isinstance(voice, str) and _VOICE.fullmatch(voice) and voice != "none":
        extra["voice"] = voice
    if raw.get("denied") is True:
        extra["denied"] = True
    return extra


def result(record):
    return "refused" if record.get("denied") else ("ok" if record["rc"] == 0 else "failed")


def _utc(value):
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _unique(items):
    value = {}
    for key, val in items:
        if key in value:
            raise ValueError("duplicate_key")
        value[key] = val
    return value


def clean(line):
    """One raw log line -> (sanitized record, None) or (None, cause).

    Only allowlisted fields are rebuilt from validated values; the command
    text and any unknown key are never copied.
    """
    try:
        raw = json.loads(line, object_pairs_hook=_unique)
    except (ValueError, RecursionError):
        return None, "invalid_json"
    if not isinstance(raw, dict):
        return None, "invalid_object"
    if _utc(raw.get("ts")) is None:
        return None, "invalid_timestamp"
    tool, cmd_sha = raw.get("tool"), raw.get("cmd_sha")
    if not isinstance(tool, str) or not _TOOL.fullmatch(tool):
        return None, "invalid_tool"
    if not isinstance(cmd_sha, str) or not _CMD_SHA.fullmatch(cmd_sha):
        return None, "invalid_cmd_sha"
    record = {"measured_at": raw["ts"], "tool": tool, "cmd_sha": cmd_sha}
    for name, (low, high) in _INTS.items():
        value = raw.get(name)
        if type(value) is not int or not low <= value <= high:
            return None, "invalid_" + name
        record[name] = value
    record.update(optional(raw))
    record["result"] = result(record)
    record["receipt_sha256"] = _digest(record)
    return record, None


def _state(record, now, verified):
    age = (now - _utc(record["measured_at"])).total_seconds()
    if age < 0:
        return "NO_DATA", "future_timestamp"
    if record["receipt_sha256"] in verified:
        return "VERIFIED", "independent_check_recorded"
    if age <= FRESH_S:
        return "DECLARED", "execution_receipt_only_result_not_checked"
    return "STALE", "receipt_older_than_%ds" % FRESH_S


def project(lines, now, verified=frozenset(), source_cause=None):
    """Raw lines -> the projection dict. Pure: same input, same output."""
    receipts, rejected, read = [], {}, 0
    for line in lines:
        if not line.strip():
            continue
        read += 1
        record, cause = clean(line)
        if record is None:
            rejected[cause] = rejected.get(cause, 0) + 1
            continue
        record["status"], record["cause"] = _state(record, now, verified)
        receipts.append(record)
    receipts = receipts[-MAX_RECEIPTS:]
    if receipts:
        status, cause = receipts[-1]["status"], receipts[-1]["cause"]
    else:
        status, cause = "NO_DATA", source_cause or ("no_valid_receipt" if read else "source_empty")
    out = {"schema": SCHEMA, "source": SOURCE,
           "observed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "status": status, "cause": cause,
           "counts": {"read": read, "kept": len(receipts), "rejected": dict(sorted(rejected.items()))},
           "receipts": receipts}
    while len(_encode(out)) > MAX_OUT and out["receipts"]:
        out["receipts"].pop(0)
        out["counts"]["kept"] = len(out["receipts"])
    out["projection_sha256"] = _digest(out["receipts"])
    return out


def _encode(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def read_source(path):
    """The tail of the private log -> (lines, None) or ([], cause). Never follows a symlink."""
    path = Path(path)
    try:
        if path.is_symlink() or path.parent.is_symlink():
            return [], "symlink_forbidden"
        if not path.is_file():
            return [], "file_missing"
        size = path.stat().st_size
        with open(path, "rb") as handle:
            if size > MAX_SOURCE:
                handle.seek(size - MAX_SOURCE)
                handle.readline()          # drop the line cut by the seek
            data = handle.read(MAX_SOURCE)
        return data.decode("utf-8", errors="replace").splitlines(), None
    except OSError:
        return [], "file_unreadable"


def write(root, projection):
    """Atomically replace <root>/notebook/receipts.json (mode 0600). Returns the path."""
    directory = Path(root) / "notebook"
    target = directory / "receipts.json"
    if Path(root).is_symlink() or directory.is_symlink() or target.is_symlink():
        raise OSError("symlink_forbidden")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = _encode(projection)
    if len(payload) > MAX_OUT + 128:
        raise ValueError("projection_oversized")
    temp = directory / (".receipts.%d.tmp" % os.getpid())
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    return target


def refresh(root, source=None):
    """Re-project the private log into <root>/notebook/receipts.json now (the Notebook calls this when it opens).
    Returns the projection status, or NO_DATA with its cause; never raises."""
    try:
        home = Path(os.environ.get("PRECEPTOROS_MCP_HOME") or Path.home() / ".preceptoros-mcp")
        lines, cause = read_source(source or home / "audit.jsonl")
        projection = project(lines, dt.datetime.now(dt.timezone.utc), source_cause=cause)
        write(root, projection)
        return projection["status"], projection["cause"]
    except (OSError, ValueError) as e:
        return "NO_DATA", "refresh_failed_" + type(e).__name__


def main(argv=None):
    parser = argparse.ArgumentParser(description="Project private MCP receipts into the local Notebook folder.")
    parser.add_argument("--source", default=str(Path.home() / ".preceptoros-mcp" / "audit.jsonl"))
    parser.add_argument("--root", default=None, help="personal folder (default: the product's own)")
    parser.add_argument("--dry-run", action="store_true", help="measure and print counts, write nothing")
    args = parser.parse_args(argv)
    lines, cause = read_source(args.source)
    projection = project(lines, dt.datetime.now(dt.timezone.utc), source_cause=cause)
    if not args.dry_run:
        root = args.root
        if root is None:
            import casa
            root = casa.raiz()
        write(root, projection)
    # Counts and states only: the receipts themselves stay in the local file.
    print(json.dumps({"schema": SCHEMA, "status": projection["status"], "cause": projection["cause"],
                      "counts": projection["counts"], "written": not args.dry_run,
                      "projection_sha256": projection["projection_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
