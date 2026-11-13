"""What happened to each delegated task · P2 journal receipts read as one sentence for eye, ear and machine.

Autonomy parity S4. The durable store is Codex CLI's (LAB `meta_harness/execution_journal.py`, P2): it claims a
run before dispatch, replays a finished receipt after a restart and lets unknown work block new claims. This module
does NOT store, claim, retry or authorise anything. It reads records the host hands it, shaped as

    {"run_id": label, "task_sha256": hex64, "receipt": <preceptoros.meta-receipt/1> | None, "replayed": bool}

and tells each one as a state, a cause, a sentence, the next step, a reader line and an Acho class, the same way
turnos_hexelion tells a request. Which component hands it those records (the "mirror") is not built yet:
NO_DATA(p2_mirror_not_built). Only the fields used here are checked; full verification belongs to the journal.

States:
  DONE_CHECKED              finished, and its output passed its own check
  DONE_UNCHECKED            finished, but nobody evaluated the output
  NEEDS_YOUR_AUTHORIZATION  blocked on permission: nothing ran; only the person's gate can open it
  FAILED                    stopped with a known failure class and its next step
  CANCELLED                 cancelled; if it may have started, it says so
  OUTCOME_UNKNOWN           it may have run; never retried automatically
  NO_RESULT_RECORDED        claimed, and no result is recorded: it may have stopped (never "running")
  NO_DATA                   the record cannot be read; the cause says why

Uncertainty (LAB #188, UNCERTAINTY-PROJECTION-01): an OUTCOME_UNKNOWN or NO_RESULT_RECORDED record may carry the
host's projection of that claim (`preceptoros.lab.uncertainty-ack/1`, kind=projection). Its `summary` is the one
sentence every modality says; its `projection_ref` binds the eye, the ear and the JSON to the same record. The APP
recomputes that ref (integrity, never authority), shows the acknowledgement word the host reported, the retained
reservation or its NO_DATA cause, no retry and no memory promotion. TTL is 0: it is never cached as currently valid.
It adds no control, and the state stays uncertain and keeps blocking new work.

A model's words never change a state: states come from typed receipt fields only, and permission is only ever
reported as missing, never granted. Pure: no network, no clock, no writes.
"""
from __future__ import annotations

import hashlib
import json
import re

import audio_feedback as AF

SCHEMA = "preceptoros.hexelion-tasks/1"
RECEIPT_SCHEMA = "preceptoros.meta-receipt/1"
MAX_TASKS = 12
# One told task is one row of the HTTP projection. The row keeps 1,024 B like the host's own records: an uncertain
# task carries full refs once in its JSON, 12-hex prefixes in its words (measured in test_uncertainty_presentation).
MAX_TASK_B = 1024
_HEX = re.compile(r"^[0-9a-f]{64}$")
_LABEL = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
PHASES = frozenset({"complete", "failed", "blocked", "cancelled"})
OUTCOMES = frozenset({"KNOWN", "UNKNOWN", "NOT_STARTED"})
GRADES = frozenset({"PASS", "OUTPUT_SCHEMA", "TASK_SKILL", "NOT_EVALUATED"})
# P2's failure classes and what each asks for next, said in words (delegation.NEXT, LAB #182).
FAILURE_NEXT = {
    "PERMISSION": "Authorize it yourself if you want it to run; a model can never authorize it.",
    "BUDGET": "Revise the budget before asking again.",
    "CANCELLED": "Check whether it had started before asking again.",
    "REPLAY": "Inspect the run: the same run id came back with a different task.",
    "TRANSPORT": "Repair the connection to the worker, then ask again.",
    "PROTOCOL": "Repair the adapter; the worker's reply did not follow the protocol.",
    "MODEL_IDENTITY": "Verify which model answered before trusting it.",
    "OUTPUT_SCHEMA": "Repair the contract; the output did not have the agreed shape.",
    "TASK_SKILL": "Collect an independent holdout; the output failed its check.",
    "EVIDENCE": "Collect the missing evidence; nothing is counted until then.",
    "UNKNOWN": "Diagnose it without retrying; it is never retried automatically.",
}
NEXT = {
    "DONE_CHECKED": "Review the receipt before relying on it.",
    "DONE_UNCHECKED": "Check the output yourself; nobody evaluated it.",
    "NEEDS_YOUR_AUTHORIZATION": FAILURE_NEXT["PERMISSION"],
    "CANCELLED": FAILURE_NEXT["CANCELLED"],
    "OUTCOME_UNKNOWN": FAILURE_NEXT["UNKNOWN"],
    "NO_RESULT_RECORDED": "Ask the host to resolve it; new work waits, and it is never retried automatically.",
    "NO_DATA": "Fix the record's source; nothing is counted from it.",
}
UNCERTAINTY_SCHEMA = "preceptoros.lab.uncertainty-ack/1"
_PROJECTION_KEYS = frozenset({"schema", "kind", "state", "cause", "acknowledgement", "observed_at", "journal_id",
                              "task_ref", "resolution_ref", "reservation", "ttl_seconds", "no_retry", "promotion",
                              "summary", "projection_ref"})
# The acknowledgement word the host reported -> what comes next, and its Acho class. None of them is shown as approval.
ACKNOWLEDGEMENT = {
    "HITL_REQUIRED": ("Your decision, on the host: review projection %s; only you can acknowledge it.", "needs_you"),
    "HUMAN_ACKNOWLEDGED": ("Host reports an acknowledgement (projection %s); re-read, never cached here.", "empty"),
    "AUTHORITY_NOT_VERIFIED": ("Treat projection %s as not approved; the host could not verify its witness.", "fence"),
}


UNCERTAINTY_TERMS = {"ttl_seconds": 0, "no_retry": True, "promotion": "NOT_AUTHORIZED"}


def _canonical_ref(record):
    """LAB's canonical encoding (bin/dfa06_evidence_bundle.encode) -> sha256: the same ref the host computed."""
    body = {k: v for k, v in record.items() if k != "projection_ref"}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


ACHO = {"DONE_CHECKED": "ok", "NEEDS_YOUR_AUTHORIZATION": "needs_you", "FAILED": "exec_fail"}


def _uncertainty(ref, raw):
    """The host's projection -> the facts the row shows, or the cause why it cannot be shown."""
    if type(raw) is not dict or set(raw) != _PROJECTION_KEYS or raw.get("schema") != UNCERTAINTY_SCHEMA \
            or raw.get("kind") != "projection":
        return None, "uncertainty_fields_unknown"
    try:
        if type(raw["projection_ref"]) is not str or raw["projection_ref"] != _canonical_ref(raw):
            return None, "uncertainty_ref_mismatch"
        if len(json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")) >= 1024:
            return None, "uncertainty_exceeds_1024_bytes"
    except (TypeError, ValueError):
        return None, "uncertainty_fields_unknown"
    if raw["task_ref"] != ref:
        return None, "uncertainty_for_another_task"
    if raw["state"] != "UNKNOWN":
        return None, "uncertainty_unavailable_on_host"
    res = raw["reservation"]
    reservation_ok = type(res) is dict and (
        (set(res) == {"state", "tokens"} and res["state"] == "RETAINED" and type(res["tokens"]) is int
         and 0 <= res["tokens"] <= 512)
        or (set(res) == {"state", "cause"} and res["state"] == "NO_DATA" and type(res["cause"]) is str))
    if (raw["acknowledgement"] not in ACKNOWLEDGEMENT or not reservation_ok or raw["no_retry"] is not True
            or raw["promotion"] != "NOT_AUTHORIZED" or raw["ttl_seconds"] != 0
            or type(raw["summary"]) is not str or not 0 < len(raw["summary"]) <= 200):
        return None, "uncertainty_terms_changed"
    return {"projection_ref": raw["projection_ref"], "task_ref": ref, "acknowledgement": raw["acknowledgement"],
            "reservation": dict(res), "observed_at": raw["observed_at"]}, raw["summary"]


def _uncertain(state, run_id, ref, cause, sentence, raw):
    if raw is None:
        return _task(state, run_id, cause, sentence, NEXT[state])
    u, said = _uncertainty(ref, raw)
    if u is None:
        return _no_data(run_id, said)
    words, clase = ACKNOWLEDGEMENT[u["acknowledgement"]]
    # The host's sentence is the sentence, for every modality; the row adds only what comes next.
    return _task(state, run_id, cause, said, words % u["projection_ref"][:12], uncertainty=u, acho_class=clase)


def _task(state, run_id, cause, sentence, next_step, replayed=False, uncertainty=None, acho_class=None):
    if replayed and state in ("DONE_CHECKED", "DONE_UNCHECKED", "FAILED"):
        sentence += " The result was recovered after a restart; it was not run again."
    clase = acho_class or ACHO.get(state, "empty")
    t = {"run_id": run_id, "state": state, "cause": cause, "sentence": sentence, "next": next_step,
         "reader": "Task %s. %s %s" % (run_id or "unnamed", sentence, next_step), "replayed": bool(replayed),
         # The class alone decides the cue (audio_feedback.cue_for_turn derives the motif); no task row is played.
         "acho": {"class": clase, "sound": "off_until_turned_on", "words": "reader"}}
    if uncertainty:
        t["uncertainty"] = uncertainty
    if len(json.dumps(t, ensure_ascii=False).encode("utf-8")) >= MAX_TASK_B:
        return _task("NO_DATA", run_id, "task_exceeds_its_byte_bound", "This task's record is too large to read.",
                     NEXT["NO_DATA"])
    return t


def _no_data(run_id, cause):
    return _task("NO_DATA", run_id, cause, "This task's record could not be read (%s)." % cause.replace("_", " "),
                 NEXT["NO_DATA"])


def task(record):
    """One journal record -> one told task. Anything malformed is NO_DATA with its cause, never a guess."""
    if type(record) is not dict:
        return _no_data(None, "record_not_an_object")
    run_id, ref, receipt = record.get("run_id"), record.get("task_sha256"), record.get("receipt")
    replayed = record.get("replayed", False)
    if set(record) - {"run_id", "task_sha256", "receipt", "replayed", "uncertainty"}:
        return _no_data(run_id if type(run_id) is str and _LABEL.match(run_id) else None, "record_fields_unknown")
    if type(run_id) is not str or not _LABEL.match(run_id):
        return _no_data(None, "run_id_invalid")
    if type(ref) is not str or not _HEX.match(ref):
        return _no_data(run_id, "task_digest_invalid")
    if type(replayed) is not bool:
        return _no_data(run_id, "replayed_not_boolean")
    raw_u = record.get("uncertainty")
    if receipt is None:
        return _uncertain("NO_RESULT_RECORDED", run_id, ref, "claim_without_receipt",
                          "This task was claimed and no result is recorded; it may have stopped.", raw_u)
    if type(receipt) is not dict or receipt.get("schema") != RECEIPT_SCHEMA:
        return _no_data(run_id, "receipt_schema_unknown")
    if receipt.get("run_id") != run_id or receipt.get("task_sha256") != ref:
        return _no_data(run_id, "receipt_for_another_task")
    phase, outcome, failure = receipt.get("phase"), receipt.get("outcome"), receipt.get("failure_class")
    gate, gate_ref, m = receipt.get("approval_state"), receipt.get("approval_ref"), receipt.get("measurement")
    if phase not in PHASES or outcome not in OUTCOMES or (failure != "NONE" and failure not in FAILURE_NEXT):
        return _no_data(run_id, "receipt_fields_unknown")
    if gate not in ("EXTERNAL_GATE", "NO_DATA") or (gate == "EXTERNAL_GATE") != (type(gate_ref) is str
                                                                                and bool(_HEX.match(gate_ref))):
        return _no_data(run_id, "approval_fields_inconsistent")
    if (failure == "NONE") != (phase == "complete"):
        return _no_data(run_id, "phase_and_failure_disagree")
    if raw_u is not None and not (outcome == "UNKNOWN" and phase != "cancelled"):
        return _no_data(run_id, "uncertainty_on_a_known_outcome")
    if phase == "complete":
        if outcome != "KNOWN" or gate != "EXTERNAL_GATE" or type(m) is not dict or m.get("grade") not in GRADES:
            return _no_data(run_id, "completion_without_its_evidence")
        if m["grade"] == "PASS":
            return _task("DONE_CHECKED", run_id, None, "This task finished and its output passed its check.",
                         NEXT["DONE_CHECKED"], replayed)
        if m["grade"] == "NOT_EVALUATED":
            return _task("DONE_UNCHECKED", run_id, "output_not_evaluated",
                         "This task finished, but nobody evaluated its output.", NEXT["DONE_UNCHECKED"], replayed)
        return _no_data(run_id, "completion_with_a_failed_grade")
    if outcome == "UNKNOWN" and phase != "cancelled":
        return _uncertain("OUTCOME_UNKNOWN", run_id, ref, failure.lower(),
                          "This task may have run, and its outcome is unknown.", raw_u)
    if phase == "cancelled":
        started = "; it may have started" if outcome == "UNKNOWN" else "; it had not started" if outcome == "NOT_STARTED" else ""
        return _task("CANCELLED", run_id, "cancelled", "This task was cancelled%s." % started, NEXT["CANCELLED"])
    if failure == "PERMISSION":
        if outcome != "NOT_STARTED":
            return _no_data(run_id, "permission_block_after_start")
        return _task("NEEDS_YOUR_AUTHORIZATION", run_id, "permission",
                     "This task needs your authorization; nothing has run.", NEXT["NEEDS_YOUR_AUTHORIZATION"])
    return _task("FAILED", run_id, failure.lower(),
                 "This task stopped: %s." % failure.lower().replace("_", " "), FAILURE_NEXT[failure], replayed)


def project(records, observed_at, source_cause=None):
    """The projection Notebook, Talk and the machine read. NO_DATA with cause while no mirror feeds it."""
    base = {"schema": SCHEMA, "observed_at": observed_at,
            "limits": "Reads journal records handed to it. It stores, claims, retries and authorises nothing.",
            # Every uncertainty a row shows was checked to carry these terms; they are said once, not per row.
            "uncertainty_terms": UNCERTAINTY_TERMS}
    if source_cause or not isinstance(records, list):
        return dict(base, state="NO_DATA", cause=str(source_cause or "records_unreadable")[:80], tasks=[], counts={},
                    needs_you=0, blocks_new_work=0, decisions_for_you=0)
    shown = records[:MAX_TASKS]
    # One run, one record. A run id handed twice is a contradictory source: none of its copies is believed.
    seen = {}
    for r in shown:
        rid = r.get("run_id") if type(r) is dict else None
        if type(rid) is str:
            seen[rid] = seen.get(rid, 0) + 1
    tasks = [_no_data(r["run_id"], "duplicate_record") if type(r) is dict and seen.get(r.get("run_id"), 0) > 1
             else task(r) for r in shown]
    counts = {}
    for t in tasks:
        counts[t["state"]] = counts.get(t["state"], 0) + 1
    # The journal lets a claim with no known result block every new claim until the host resolves it (LAB #182);
    # an interruption before authorisation can leave one. Said, never hidden and never cleared from here.
    blocks = counts.get("NO_RESULT_RECORDED", 0) + counts.get("OUTCOME_UNKNOWN", 0)
    return dict(base, state="MEASURED" if tasks else "NO_DATA", cause=None if tasks else "no_task_recorded",
                tasks=tasks, counts=dict(sorted(counts.items())), needs_you=counts.get("NEEDS_YOUR_AUTHORIZATION", 0),
                blocks_new_work=blocks, decisions_for_you=sum(1 for t in tasks if t.get("uncertainty", {}).get("acknowledgement") == "HITL_REQUIRED"))
