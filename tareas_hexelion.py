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

Uncertainty (LAB #186, HUMAN-UNCERTAINTY-01): an OUTCOME_UNKNOWN or NO_RESULT_RECORDED record may carry the
journal's read-only proposal (`preceptoros.lab.uncertainty-ack/1`, from prepare_unknown_ack). It is told, never
acted on: exact task, evidence and proposal refs, budget still reserved, no retry, and the one decision that is the
Sovereign's. The APP cannot see a signature, the budget ledger or the old worker, so it never says the proposal was
signed, the budget returned or the worker stopped; those stay NO_DATA with their cause. The state stays uncertain
and still blocks new work. The proposal's own hash is checked by the journal, not here.

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
# One told task is a row of an HTTP projection, not an MCP line or a thread message (those keep 1,024 B). An uncertain
# task carries three exact 64-hex refs plus its words, measured at 1,198 B worst case (32-char run id), so 1,536 B.
MAX_TASK_B = 1536
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
DECISION = "ACK_UNKNOWN_RETAIN_RESERVATION"
_PROPOSAL_KEYS = frozenset({"schema", "journal_id", "run_id", "task_ref", "prior_ref", "evidence_ref", "authority_ref",
                            "observed_at", "decision", "no_retry", "reservation_release", "resolution_ref"})
# What the APP cannot see is listed as not visible here (NO_DATA), never filled in: a signature, a budget return and
# the old worker's stop each live with the host.
NOT_VISIBLE = ("signature", "budget_return", "worker_stop")
ACHO = {"DONE_CHECKED": "ok", "NEEDS_YOUR_AUTHORIZATION": "needs_you", "FAILED": "exec_fail"}


def _uncertainty(run_id, ref, raw):
    """The journal's proposal -> what the person needs to decide, or a cause why it cannot be shown."""
    if type(raw) is not dict or set(raw) != _PROPOSAL_KEYS or raw.get("schema") != UNCERTAINTY_SCHEMA:
        return None, "uncertainty_fields_unknown"
    if raw["run_id"] != run_id or raw["task_ref"] != ref:
        return None, "uncertainty_for_another_task"
    if (raw["decision"] != DECISION or raw["no_retry"] is not True or raw["reservation_release"] is not False
            or any(type(raw[k]) is not str or not _HEX.match(raw[k])
                   for k in ("prior_ref", "evidence_ref", "authority_ref", "resolution_ref"))):
        return None, "uncertainty_terms_changed"
    return {"task_ref": ref, "evidence_ref": raw["evidence_ref"], "proposal_ref": raw["resolution_ref"],
            "budget": "reserved", "retry": "none", "decides": "sovereign", "not_visible": list(NOT_VISIBLE)}, None


def _uncertain(state, run_id, ref, cause, sentence, raw):
    if raw is None:
        return _task(state, run_id, cause, sentence, NEXT[state])
    u, bad = _uncertainty(run_id, ref, raw)
    if bad:
        return _no_data(run_id, bad)
    sentence += " Budget stays reserved; no retry."
    nxt = ("Your decision: proposal %s, evidence %s. Only you can acknowledge it, outside this app."
           % (u["proposal_ref"][:12], u["evidence_ref"][:12]))
    return _task(state, run_id, cause, sentence, nxt, uncertainty=u)


def _task(state, run_id, cause, sentence, next_step, replayed=False, uncertainty=None):
    if replayed and state in ("DONE_CHECKED", "DONE_UNCHECKED", "FAILED"):
        sentence += " The result was recovered after a restart; it was not run again."
    # A proposal waiting for the Sovereign's own decision is a needs-you cue; the words say which decision.
    clase = "needs_you" if uncertainty else ACHO.get(state, "empty")
    t = {"run_id": run_id, "state": state, "cause": cause, "sentence": sentence, "next": next_step,
         "reader": "Task %s. %s %s" % (run_id or "unnamed", sentence, next_step), "replayed": bool(replayed),
         "acho": {"class": clase, "motif": AF.motif_for_class(clase), "sound": "off_until_turned_on", "words": "reader"}}
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
            "limits": "Reads journal records handed to it. It stores, claims, retries and authorises nothing."}
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
                blocks_new_work=blocks, decisions_for_you=sum(1 for t in tasks if "uncertainty" in t))
