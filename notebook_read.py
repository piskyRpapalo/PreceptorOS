"""Notebook operational projection · read-only fixed files, no scheduler, no signing.

The CLI builders publish sanitized observations to <casa>/notebook/ only after their
own permissions and evidence checks. This reader never scans worktrees or executes
jobs. State is OBSERVED (a declared recent heartbeat), STALE, or NO_DATA,
never 'running process verified'. Proposed schemas are not Babel contracts.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

MAX_AGENTS = 12
_LIMIT = {"agents": 8192, "wbr": 4096, "mbr": 4096, "receipts": 8320}
_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,39}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


def _utc(value):
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        return None
    try:
        stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return stamp
    except ValueError:
        return None


def _symlink_in_path(path):
    """Reject a symbolic link in any existing path component, including ancestors.

    This closes ordinary ancestor-alias bypasses. A hostile concurrent path
    replacement remains outside this check's guarantee: it is not an openat gate.
    """
    path = Path(path).absolute()
    return any(part.is_symlink() for part in (path, *path.parents))


def _load(directory, name):
    """Fixed basename only; no symlinks, duplicated keys or oversized records."""
    path = directory / (name + ".json")
    try:
        if _symlink_in_path(path):
            return None, "symlink_forbidden"
        if not path.is_file():
            return None, "file_missing"
        if path.stat().st_size > _LIMIT[name]:
            return None, "file_oversized"
        raw = path.read_bytes()
        if len(raw) > _LIMIT[name]:
            return None, "file_oversized"
        def unique(items):
            value = {}
            for key, val in items:
                if key in value:
                    raise ValueError("duplicate_key")
                value[key] = val
            return value
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
        return (obj, None) if isinstance(obj, dict) else (None, "invalid_object")
    except (OSError, UnicodeError, ValueError, RecursionError):
        return None, "invalid_json"


def _short(value, max_len):
    if not isinstance(value, str) or not 1 <= len(value) <= max_len:
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return None
    return value


def _agents(obj, now):
    if not isinstance(obj, dict) or obj.get("schema") != "preceptoros.notebook-agents/0":
        return [], "schema_invalid"
    rows = obj.get("agents")
    if not isinstance(rows, list) or len(rows) > MAX_AGENTS:
        return [], "agent_list_invalid"
    result, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            return [], "agent_invalid"
        agent_id = row.get("id")
        name = _short(row.get("name"), 48)
        role = _short(row.get("role"), 64)
        if not isinstance(agent_id, str) or not _ID.fullmatch(agent_id) or agent_id in seen or not name or not role:
            return [], "agent_invalid"
        seen.add(agent_id)
        seen_at = _utc(row.get("last_seen"))
        receipt = row.get("receipt_sha256")
        if not isinstance(receipt, str) or not _SHA.fullmatch(receipt):
            return [], "receipt_invalid"
        if seen_at is None:
            status, cause = "NO_DATA", "invalid_last_seen"
        else:
            age = (now - seen_at).total_seconds()
            status, cause = ("NO_DATA", "future_timestamp") if age < 0 else (
                ("OBSERVADO", "recent_declared_heartbeat") if age <= 600 else
                ("STALE", "declared_heartbeat_expired"))
        result.append({"id": agent_id, "name": name, "role": role,
                       "last_seen": row.get("last_seen"), "status": status,
                       "cause": cause, "receipt_sha256": receipt})
    return sorted(result, key=lambda x: x["id"]), None


def _report(obj, name, now):
    report = {"kind": name.upper(), "status": "NO_DATA", "cause": "file_missing"}
    if obj is None:
        return report
    if obj.get("schema") != "preceptoros." + name + "/1":
        report["cause"] = "schema_invalid"
        return report
    period = _short(obj.get("period"), 16)
    summary = _short(obj.get("summary"), 420)
    stamp = _utc(obj.get("measured_at"))
    sha = obj.get("receipt_sha256")
    if not period or not summary or stamp is None or not isinstance(sha, str) or not _SHA.fullmatch(sha):
        report["cause"] = "fields_invalid"
        return report
    if (now - stamp).total_seconds() < 0:
        report["cause"] = "future_timestamp"
        return report
    return {"kind": name.upper(), "status": "DECLARADO",
            "cause": "origin_receipt_not_independently_verified",
            "period": period, "summary": summary,
            "measured_at": obj["measured_at"], "receipt_sha256": sha}


def _receipts(obj, now):
    """Command receipts (producer: notebook_receipts.py). Every row is re-checked here: fields, its own fingerprint,
    and its state from `now` (the file's state was true when written, not now). A receipt says a command ran and how
    it ended; it never says the output was right."""
    import notebook_receipts as P
    if not isinstance(obj, dict) or obj.get("schema") != P.SCHEMA or not isinstance(obj.get("receipts"), list):
        return [], "schema_invalid"
    rows = []
    for raw in obj["receipts"][-P.MAX_RECEIPTS:]:
        if not isinstance(raw, dict):
            return [], "receipt_invalid"
        record = {"measured_at": raw.get("measured_at"), "tool": raw.get("tool"), "cmd_sha": raw.get("cmd_sha")}
        if (P._utc(record["measured_at"]) is None or not isinstance(record["tool"], str)
                or not P._TOOL.fullmatch(record["tool"]) or not isinstance(record["cmd_sha"], str)
                or not P._CMD_SHA.fullmatch(record["cmd_sha"])):
            return [], "receipt_invalid"
        for name, (low, high) in P._INTS.items():
            value = raw.get(name)
            if type(value) is not int or not low <= value <= high:
                return [], "receipt_invalid"
            record[name] = value
        record["result"] = "ok" if record["rc"] == 0 else "failed"
        if raw.get("result") != record["result"] or raw.get("receipt_sha256") != P._digest(record):
            return [], "receipt_fingerprint_mismatch"
        record["receipt_sha256"] = raw["receipt_sha256"]
        record["status"], record["cause"] = P._state(record, now, frozenset())
        rows.append(record)
    return rows, None if rows else "no_valid_receipt"


def read(root, now=None):
    """Sanitized projection for the APP. No process-live or signing claims."""
    now = now or dt.datetime.now(dt.timezone.utc)
    directory = Path(root) / "notebook"
    agents_obj, agents_error = _load(directory, "agents")
    agents, agent_cause = _agents(agents_obj, now) if agents_obj is not None else ([], agents_error)
    reports = []
    for name in ("wbr", "mbr"):
        obj, error = _load(directory, name)
        report = _report(obj, name, now)
        if obj is None:
            report["cause"] = error
        reports.append(report)
    receipts_obj, receipts_error = _load(directory, "receipts")
    receipts, receipts_cause = _receipts(receipts_obj, now) if receipts_obj is not None else ([], receipts_error)
    return {"schema": "preceptoros.notebook-readonly/0",
            "observed_at": now.isoformat().replace("+00:00", "Z"),
            "agents": agents, "agents_status": "DECLARADO" if agents_obj is not None and agent_cause is None else "NO_DATA",
            "agents_cause": agent_cause, "reports": reports,
            "receipts": receipts, "receipts_cause": receipts_cause}
