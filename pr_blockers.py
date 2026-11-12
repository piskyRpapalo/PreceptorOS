"""Why a pull request is not advancing · one deterministic verdict, then (optionally) a question for Hexelion.

The HITL block could list a PR and sign it, but when a signed PR did not merge the
person saw only «blocked». This module reads the same facts GitHub already gives
and says which one is holding the PR, in a fixed order, with what to do next:

  MERGED · CLOSED · CONFLICT · RED_CHECKS · BEHIND_MAIN · NEEDS_SIGNATURE ·
  WAITING_CHECKS · READY · NO_DATA

Pure: no network, no clock of its own (the caller passes `now`), no subprocess.
The verdict is never the model's: `question()` only builds the text the person
may send to Hexelion, and the answer is a suggestion, not a decision.
"""
from __future__ import annotations

import datetime as dt

SCHEMA = "preceptoros.pr-blockers/1"
SIGNATURE_CHECKS = {"hitl"}
RED = {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE"}
NEXT = {
    "MERGED": "Nothing to do: it is on main.",
    "CLOSED": "Nothing to do: it was closed without merging.",
    "CONFLICT": "The branch and main changed the same lines. Its owner rebuilds the branch; then it is announced and signed again.",
    "RED_CHECKS": "A check failed on this head. Its owner fixes it; a new head needs a new signature.",
    "BEHIND_MAIN": "Main moved. Updating the branch makes a new head, and a signature on the old head no longer covers it.",
    "NEEDS_SIGNATURE": "This exact head has no signature yet. Sign it from this block when you have read it.",
    "WAITING_CHECKS": "Signed and waiting for the checks to finish. It merges by itself when they are green; signing again does not speed it up.",
    "READY": "Signed and green. If it is not merging, press Refresh; the merge may be seconds away.",
    "NO_DATA": "GitHub did not answer with the facts needed. Press Refresh.",
}


def _name(check):
    return str(check.get("name") or check.get("context") or "")


def _result(check):
    return str(check.get("conclusion") or check.get("state") or "").upper()


def _running(check):
    status = str(check.get("status") or "COMPLETED").upper()
    return status != "COMPLETED" or _result(check) in {"PENDING", "EXPECTED", "QUEUED", "IN_PROGRESS"}


def _minutes(check, now):
    stamp = check.get("startedAt")
    try:
        started = dt.datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        gap = (now - started).total_seconds()
        return int(gap // 60) if 0 <= gap < 86400 else None
    except (TypeError, ValueError):
        return None


def diagnose(pr, behind_by, now, signing_running=False, both_touched=()):
    """One PR's facts -> {schema, number, head, verdict, causes, next}. Same input, same output."""
    if not isinstance(pr, dict) or not pr.get("headRefOid"):
        return {"schema": SCHEMA, "number": None, "head": None, "verdict": "NO_DATA",
                "causes": [{"code": "NO_DATA", "detail": "pull_request_unreadable"}], "next": NEXT["NO_DATA"]}
    checks = [c for c in (pr.get("statusCheckRollup") or []) if isinstance(c, dict)]
    work = [c for c in checks if _name(c) not in SIGNATURE_CHECKS]
    signed = any(_name(c) in SIGNATURE_CHECKS and _result(c) == "SUCCESS" for c in checks)
    causes = []
    state = str(pr.get("state") or "").upper()
    if state in ("MERGED", "CLOSED"):
        causes.append({"code": state, "detail": ""})
    else:
        if str(pr.get("mergeable") or "").upper() == "CONFLICTING":
            files = sorted(set(both_touched))[:12]
            causes.append({"code": "CONFLICT", "detail": ", ".join(files) if files else "files not listed"})
        red = sorted(_name(c) for c in work if not _running(c) and _result(c) in RED)
        if red:
            causes.append({"code": "RED_CHECKS", "detail": ", ".join(red)})
        if isinstance(behind_by, int) and behind_by > 0:
            causes.append({"code": "BEHIND_MAIN", "detail": "%d commit(s) behind %s" % (behind_by, pr.get("baseRefName") or "main")})
        if not signed:
            causes.append({"code": "NEEDS_SIGNATURE", "detail": "no signature check passed for this head"})
        waiting = sorted(work, key=_name)
        waiting = [c for c in waiting if _running(c)]
        if waiting:
            parts = []
            for c in waiting:
                minutes = _minutes(c, now)
                parts.append(_name(c) + (" (%d min)" % minutes if minutes is not None else ""))
            causes.append({"code": "WAITING_CHECKS", "detail": ", ".join(parts)})
        if not causes:
            causes.append({"code": "READY", "detail": ""})
        if behind_by is None:
            causes.append({"code": "NO_DATA", "detail": "distance_to_main_not_measured"})
    verdict = causes[0]["code"]
    out = {"schema": SCHEMA, "number": pr.get("number"), "head": str(pr["headRefOid"])[:12],
           "verdict": verdict, "causes": causes, "next": NEXT[verdict]}
    if signing_running:
        out["signing"] = "A signing run for this PR is already waiting in the background; do not start another."
    return out


def line(d):
    """The diagnosis as one sentence a person reads first."""
    first = d["causes"][0]
    text = "#%s · %s" % (d.get("number"), d["verdict"])
    if first["detail"]:
        text += " · " + first["detail"]
    return text + " · " + d["next"]


def question(d, title=""):
    """The text the person may send to Hexelion. At most 600 characters, facts only."""
    causes = "; ".join(c["code"] + (" (" + c["detail"] + ")" if c["detail"] else "") for c in d["causes"])
    text = ("Pull request #%s \"%s\", head %s, is held by: %s. Explain in three short steps what the owner of the "
            "branch should do, and which step needs the Sovereign. Do not invent file contents."
            % (d.get("number"), str(title)[:80], d.get("head"), causes))
    return text[:600]
