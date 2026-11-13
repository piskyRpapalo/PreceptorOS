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

A model's words never change a state: states come from typed receipt fields only, and permission is only ever
reported as missing, never granted. Pure: no network, no clock, no writes.
"""
from __future__ import annotations

import json
import re

import audio_feedback as AF

SCHEMA = "preceptoros.hexelion-tasks/1"
RECEIPT_SCHEMA = "preceptoros.meta-receipt/1"
MAX_TASKS = 12
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
ACHO = {"DONE_CHECKED": "ok", "NEEDS_YOUR_AUTHORIZATION": "needs_you", "FAILED": "exec_fail"}


def _task(state, run_id, cause, sentence, next_step, replayed=False):
    if replayed and state in ("DONE_CHECKED", "DONE_UNCHECKED", "FAILED"):
        sentence += " The result was recovered after a restart; it was not run again."
    clase = ACHO.get(state, "empty")
    t = {"run_id": run_id, "state": state, "cause": cause, "sentence": sentence, "next": next_step,
         "reader": "Task %s. %s %s" % (run_id or "unnamed", sentence, next_step), "replayed": bool(replayed),
         "acho": {"class": clase, "motif": AF.motif_for_class(clase), "sound": "off_until_turned_on", "words": "reader"}}
    if len(json.dumps(t, ensure_ascii=False).encode("utf-8")) >= MAX_TASK_B:
        return _task("NO_DATA", None, "task_exceeds_1024_bytes", "This task's record is too large to read.",
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
    if type(run_id) is not str or not _LABEL.match(run_id):
        return _no_data(None, "run_id_invalid")
    if type(ref) is not str or not _HEX.match(ref):
        return _no_data(run_id, "task_digest_invalid")
    if type(replayed) is not bool:
        return _no_data(run_id, "replayed_not_boolean")
    if receipt is None:
        return _task("NO_RESULT_RECORDED", run_id, "claim_without_receipt",
                     "This task was claimed and no result is recorded; it may have stopped.",
                     NEXT["NO_RESULT_RECORDED"])
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
        return _task("OUTCOME_UNKNOWN", run_id, failure.lower(),
                     "This task may have run, and its outcome is unknown.", NEXT["OUTCOME_UNKNOWN"])
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
            "limits": "Reads journal records handed to it. It stores, claims, retries and authorises nothing."}
    if source_cause or not isinstance(records, list):
        return dict(base, state="NO_DATA", cause=str(source_cause or "records_unreadable")[:80], tasks=[], counts={},
                    needs_you=0)
    tasks = [task(r) for r in records[:MAX_TASKS]]
    counts = {}
    for t in tasks:
        counts[t["state"]] = counts.get(t["state"], 0) + 1
    return dict(base, state="MEASURED" if tasks else "NO_DATA", cause=None if tasks else "no_task_recorded",
                tasks=tasks, counts=dict(sorted(counts.items())), needs_you=counts.get("NEEDS_YOUR_AUTHORIZATION", 0))
