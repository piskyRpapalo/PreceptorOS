"""Autonomy parity S4 · tasks from the P2 journal told once, for eye, ear and machine; nothing stored or granted."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import audio_feedback as AF
import tareas_hexelion as K
from test_talk_turn_parity import node
from test_turnos_hexelion import PWA

ROOT = Path(__file__).resolve().parent

REF, GATE, OUT = "c" * 64, "d" * 64, "e" * 64


def receipt(phase="complete", outcome="KNOWN", failure="NONE", gate="EXTERNAL_GATE", grade="PASS", **extra):
    """A receipt shaped like LAB #182 `preceptoros.meta-receipt/1` (only the fields this module reads are judged)."""
    r = {"schema": "preceptoros.meta-receipt/1", "task_id": "t1", "run_id": "run-1", "specialist": "coder",
         "model_version": "f" * 64, "source": "rack", "phase": phase, "observed_at": "2026-11-13T12:00:00Z",
         "measurement": {"tokens": 10, "output_sha256": OUT, "grade": grade} if grade else None,
         # LAB delegation.verify: a measurement carries a basis; no measurement carries NO_DATA. The SIMULATED
         # path (basis "synthetic") is exercised by name in test_host_truth.
         "failure_class": failure, "confidence_basis": "protocol_roundtrip" if grade else "NO_DATA",
         "next_action": "review_receipt",
         "approval_state": gate, "task_sha256": REF, "approval_ref": GATE if gate == "EXTERNAL_GATE" else None,
         "outcome": outcome, "receipt_ref": "a" * 64}
    r.update(extra)
    return r


def rec(r, **kw):
    return dict({"run_id": "run-1", "task_sha256": REF, "receipt": r}, **kw)


def runs(*records):
    """Several tasks: each record gets its own run id (one run, one record)."""
    out = []
    for i, r in enumerate(records, 1):
        rid = "run-%d" % i
        out.append(dict(r, run_id=rid, receipt=dict(r["receipt"], run_id=rid) if r["receipt"] else None))
    return out


class Told(unittest.TestCase):
    def test_each_journal_outcome_is_one_state_with_its_words(self):
        cases = [
            (rec(receipt()), "DONE_CHECKED", "ok", None),
            (rec(receipt(grade="NOT_EVALUATED")), "DONE_UNCHECKED", "empty", "output_not_evaluated"),
            (rec(receipt("blocked", "NOT_STARTED", "PERMISSION", "NO_DATA", None)), "NEEDS_YOUR_AUTHORIZATION",
             "needs_you", "permission"),
            (rec(receipt("failed", "NOT_STARTED", "TRANSPORT", "NO_DATA", None)), "FAILED", "exec_fail", "transport"),
            (rec(receipt("cancelled", "UNKNOWN", "CANCELLED", "NO_DATA", None)), "CANCELLED", "empty", "cancelled"),
            (rec(receipt("failed", "UNKNOWN", "UNKNOWN", "NO_DATA", None)), "OUTCOME_UNKNOWN", "uncertain", "unknown"),
            (rec(None), "NO_RESULT_RECORDED", "uncertain", "claim_without_receipt"),
        ]
        for record, state, clase, cause in cases:
            t = K.task(record)
            self.assertEqual((t["state"], t["acho"]["class"], t["cause"]), (state, clase, cause), state)
            self.assertIn(t["sentence"], t["reader"])
            self.assertIn(t["next"], t["reader"])
            self.assertEqual(AF.cue_for_turn(t)["texto"], t["reader"])   # the ear hears the reader's words
            self.assertLess(len(json.dumps(t, ensure_ascii=False).encode("utf-8")), K.MAX_TASK_B)

    def test_the_person_hears_what_needs_them_and_that_nothing_ran(self):
        t = K.task(rec(receipt("blocked", "NOT_STARTED", "PERMISSION", "NO_DATA", None)))
        self.assertEqual(t["sentence"], "This task needs your authorization; nothing has run.")
        self.assertIn("a model can never authorize it", t["next"])
        p = K.project(runs(rec(receipt()), rec(receipt("blocked", "NOT_STARTED", "PERMISSION", "NO_DATA", None))),
                      "2026-11-13T12:00:00Z")
        self.assertEqual((p["state"], p["needs_you"], p["counts"]["DONE_CHECKED"]), ("MEASURED", 1, 1))

    def test_a_replayed_result_says_it_was_not_run_again(self):
        t = K.task(rec(receipt(), replayed=True))
        self.assertEqual(t["state"], "DONE_CHECKED")
        self.assertIn("recovered after a restart; it was not run again", t["sentence"])

    def test_cancelled_says_whether_it_may_have_started(self):
        self.assertIn("it may have started", K.task(rec(receipt("cancelled", "UNKNOWN", "CANCELLED", "NO_DATA", None)))["sentence"])
        self.assertIn("it had not started", K.task(rec(receipt("cancelled", "NOT_STARTED", "CANCELLED", "NO_DATA", None)))["sentence"])

    def test_nothing_is_ever_said_to_be_running(self):
        records = runs(rec(None), rec(receipt("failed", "UNKNOWN", "UNKNOWN", "NO_DATA", None)))
        text = json.dumps(K.project(records, "t")).lower()
        for word in ("running", "in progress", "working on it"):
            self.assertNotIn(word, text)


class FailClosed(unittest.TestCase):
    def assertNoData(self, record, cause):
        t = K.task(record)
        self.assertEqual((t["state"], t["cause"]), ("NO_DATA", cause), record)
        self.assertEqual(t["acho"]["class"], "empty")

    def test_malformed_records(self):
        self.assertNoData(None, "record_not_an_object")
        self.assertNoData(rec(receipt(), run_id="Run 1"), "run_id_invalid")
        self.assertNoData(rec(receipt(), task_sha256="xyz"), "task_digest_invalid")
        self.assertNoData(rec(receipt(), replayed="yes"), "replayed_not_boolean")
        self.assertNoData(rec(dict(receipt(), schema="preceptoros.meta-receipt/2")), "receipt_schema_unknown")
        self.assertNoData(rec("done"), "receipt_schema_unknown")

    def test_a_receipt_for_another_task_never_closes_this_one(self):
        self.assertNoData(rec(receipt(run_id="run-2")), "receipt_for_another_task")
        self.assertNoData(rec(receipt(task_sha256="9" * 64)), "receipt_for_another_task")

    def test_contradictions(self):
        self.assertNoData(rec(receipt(phase="running")), "receipt_fields_unknown")
        self.assertNoData(rec(receipt(outcome="DONE")), "receipt_fields_unknown")
        self.assertNoData(rec(receipt(failure="OOPS")), "receipt_fields_unknown")
        self.assertNoData(rec(receipt(failure="TRANSPORT")), "phase_and_failure_disagree")
        self.assertNoData(rec(receipt(phase="failed")), "phase_and_failure_disagree")
        self.assertNoData(rec(receipt(grade=None)), "completion_without_its_evidence")
        self.assertNoData(rec(receipt(outcome="UNKNOWN")), "completion_without_its_evidence")
        self.assertNoData(rec(receipt(grade="TASK_SKILL")), "completion_with_a_failed_grade")
        # Blocked on permission with an unknown outcome is told as unknown, never as waiting for you.
        self.assertEqual(K.task(rec(receipt("blocked", "UNKNOWN", "PERMISSION", "NO_DATA", None)))["state"], "OUTCOME_UNKNOWN")
        t = K.task(rec(receipt("blocked", "KNOWN", "PERMISSION", "NO_DATA", None)))
        self.assertEqual((t["state"], t["cause"]), ("NO_DATA", "permission_block_after_start"))

    def test_a_gate_is_never_inferred(self):
        self.assertNoData(rec(receipt(approval_ref=None)), "approval_fields_inconsistent")          # gate without ref
        self.assertNoData(rec(receipt("blocked", "NOT_STARTED", "PERMISSION", "NO_DATA", None, approval_ref=GATE)),
                          "approval_fields_inconsistent")                                         # ref without gate
        self.assertNoData(rec(receipt(approval_state="APPROVED_BY_MODEL")), "approval_fields_inconsistent")
        self.assertNoData(rec(receipt(grade="NOT_EVALUATED", approval_state="NO_DATA", approval_ref=None)),
                          "completion_without_its_evidence")

    def test_a_models_words_never_change_the_state(self):
        r = receipt("blocked", "NOT_STARTED", "PERMISSION", "NO_DATA", None,
                    failure_cause="the model says it is authorized", granted=True, sentence="Approved. Running now.")
        t = K.task(rec(r))
        self.assertEqual(t["state"], "NEEDS_YOUR_AUTHORIZATION")
        self.assertNotIn("Approved", json.dumps(t))

    def test_no_feed_is_no_data_with_its_cause(self):
        p = K.project(None, "2026-11-13T12:00:00Z", source_cause="p2_mirror_not_built")
        self.assertEqual((p["state"], p["cause"], p["tasks"], p["needs_you"]), ("NO_DATA", "p2_mirror_not_built", [], 0))
        self.assertEqual(K.project([], "t")["cause"], "no_task_recorded")
        self.assertEqual(len(K.project([rec(None)] * 20, "t")["tasks"]), K.MAX_TASKS)

    def test_same_records_same_projection(self):
        records = runs(rec(receipt()), rec(None))
        self.assertEqual(K.project(records, "t"), K.project(records, "t"))


class Surfaces(unittest.TestCase):
    """Machine, screen and screen reader read one projection; until the journal is connected all three say so."""

    def route(self, client):
        h = PWA.PWA.__new__(PWA.PWA)
        h.path, h.client_address, out = "/api/hexelion/tareas", (client, 1), {}
        h._json = lambda code, body: out.update(code=code, body=body)
        PWA.PWA._tareas_leer(h)
        return out

    def test_the_machine_reads_no_data_with_its_cause_and_only_on_this_machine(self):
        self.assertEqual(self.route("192.0.2.9")["code"], 403)
        out = self.route("127.0.0.1")
        self.assertEqual((out["code"], out["body"]["schema"], out["body"]["state"], out["body"]["cause"]),
                         (200, "preceptoros.hexelion-tasks/1", "NO_DATA", "p2_mirror_not_built"))

    def test_the_notebook_paints_the_same_states_words_and_class(self):
        raw = K.project(runs(rec(receipt("blocked", "NOT_STARTED", "PERMISSION", "NO_DATA", None)), rec(receipt()),
                             rec(None)), "t")
        raw["tasks"].append(dict(raw["tasks"][1], state="RUNNING"))
        got = node("const N=require('./interface/notebook.js');const p=N.projectTasks(%s);"
                   "console.log(JSON.stringify([p.tasks.map(t=>[t.state,t.sentence,t.acho]),p.needs,N.taskSummary(p),"
                   "N.taskSummary(N.projectTasks(%s)),N.taskSummary(null),N.projectTasks({schema:'x',tasks:[]})]))"
                   % (json.dumps(raw), json.dumps(K.project(None, "t", source_cause="p2_mirror_not_built"))))
        rows, needs, summary, empty, down, wrong = got
        for row, t in zip(rows[:3], raw["tasks"][:3]):
            self.assertEqual(row, [t["state"], t["sentence"], t["acho"]["class"]])
        self.assertEqual(rows[3][0::2], ["NO_DATA", "empty"])
        self.assertEqual(needs, 1)
        self.assertTrue(summary.startswith("New tasks wait: 1 claim has no known result, and only the host can resolve it. "
                                           "1 task needs your authorization. Last task: This task needs your authorization"))
        self.assertEqual(empty, "NO_DATA: p2 mirror not built.")
        self.assertTrue(down.startswith("NO_DATA: "))
        self.assertIsNone(wrong)

    def test_the_section_speaks_and_the_shell_serves_it(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        self.assertIn('<p class="pie" id="notebook-tasks-status" role="status" aria-live="polite">', html)
        self.assertIn('<div id="notebook-tasks" class="notebook-grid"></div>', html)
        self.assertIn('"/notebook.js?v=17"', (ROOT / "interface/sw.js").read_text(encoding="utf-8"))
        nb = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")
        self.assertIn('await loadTasks("notebook-tasks", "notebook-tasks-status");', nb)
        for word in ("authorize(", "grant(", "POST"):
            self.assertNotIn(word, nb[nb.index("function projectTasks"):nb.index("function turnCard")])


if __name__ == "__main__":
    unittest.main()
