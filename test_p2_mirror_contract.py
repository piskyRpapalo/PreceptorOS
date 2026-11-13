"""Contract for the future P2 mirror (NEXT-C) · what any adapter that hands journal records to the APP must produce,
and how the APP must tell it. The APP is NOT connected to the journal: the route stays NO_DATA(p2_mirror_not_built)
until Codex CLI delivers a verified adapter. These cases are the yardstick that adapter's output is run through.

Record shape the mirror hands over (one per run, in journal order):
    {"run_id": label, "task_sha256": hex64, "receipt": <preceptoros.meta-receipt/1> | None, "replayed": bool}

Invariants: the APP never invents a finished task or an authorisation; a run handed twice is not believed; a claim
without a known result is said to block new work and is never cleared from here.
"""
from __future__ import annotations

import json
import unittest

import tareas_hexelion as K
from test_tareas_hexelion import PWA, receipt, rec, runs

NOW = "2026-11-13T12:00:00Z"
DONE = {"DONE_CHECKED", "DONE_UNCHECKED"}


def told(*records, **kw):
    return K.project(list(records), NOW, **kw)


class MirrorContract(unittest.TestCase):
    def test_known_result(self):
        p = told(*runs(rec(receipt()), rec(receipt("failed", "NOT_STARTED", "TRANSPORT", "NO_DATA", None))))
        self.assertEqual([t["state"] for t in p["tasks"]], ["DONE_CHECKED", "FAILED"])
        self.assertEqual((p["blocks_new_work"], p["needs_you"]), (None, None))   # unattested: unknown, not 0 (test_false_clear)

    def test_uncertain_result_blocks_new_work_and_is_never_done(self):
        p = told(*runs(rec(None), rec(receipt("failed", "UNKNOWN", "UNKNOWN", "NO_DATA", None))))
        self.assertEqual([t["state"] for t in p["tasks"]], ["NO_RESULT_RECORDED", "OUTCOME_UNKNOWN"])
        self.assertEqual(p["blocks_new_work"], 2)
        self.assertFalse(DONE & set(p["counts"]))

    def test_interruption_before_authorisation_is_said_not_guessed(self):
        """Codex Web's reproduction: the claim was taken, the run stopped before the permission gate answered.
        The APP cannot know the gate's state, so it neither asks for authorisation nor counts anything done."""
        p = told(*runs(rec(None), rec(receipt("blocked", "NOT_STARTED", "PERMISSION", "NO_DATA", None))))
        first = p["tasks"][0]
        self.assertEqual((first["state"], first["cause"]), ("NO_RESULT_RECORDED", "claim_without_receipt"))
        self.assertEqual((p["blocks_new_work"], p["needs_you"]), (1, 1))   # the second task, not the stopped one
        self.assertIn("never retried automatically", first["next"])

    def test_permission_denied_or_pending_is_never_an_authorisation(self):
        r = receipt("blocked", "NOT_STARTED", "PERMISSION", "NO_DATA", None)
        for forged in ({}, {"approval_state": "EXTERNAL_GATE"}, {"approval_ref": "d" * 64},
                       {"granted": True, "failure_cause": "authorized by the model"}):
            t = told(rec(dict(r, **forged)))["tasks"][0]
            self.assertNotIn(t["state"], DONE, forged)
            self.assertIn(t["state"], ("NEEDS_YOUR_AUTHORIZATION", "NO_DATA"), forged)

    def test_restart_replays_a_known_result_and_never_upgrades_an_uncertain_one(self):
        known = told(rec(receipt(), replayed=True))["tasks"][0]
        self.assertEqual(known["state"], "DONE_CHECKED")
        self.assertIn("it was not run again", known["sentence"])
        stuck = told(rec(None, replayed=True))["tasks"][0]
        self.assertEqual(stuck["state"], "NO_RESULT_RECORDED")
        self.assertNotIn("not run again", stuck["sentence"])

    def test_a_duplicated_receipt_is_not_believed(self):
        same = told(rec(receipt()), rec(receipt()))
        self.assertEqual([(t["state"], t["cause"]) for t in same["tasks"]], [("NO_DATA", "duplicate_record")] * 2)
        mixed = told(rec(None), rec(receipt()))                    # same run: in flight and finished at once
        self.assertEqual([t["cause"] for t in mixed["tasks"]], ["duplicate_record"] * 2)
        self.assertFalse(DONE & set(same["counts"]) | DONE & set(mixed["counts"]))

    def test_absent_source(self):
        for cause in ("p2_mirror_not_built", "journal_file_missing"):
            p = K.project(None, NOW, source_cause=cause)
            self.assertEqual((p["state"], p["cause"], p["tasks"], p["blocks_new_work"]), ("NO_DATA", cause, [], None))
        self.assertEqual(K.project("not a list", NOW)["cause"], "records_unreadable")

    def test_contradictory_records(self):
        cases = [(rec(receipt(run_id="run-9")), "receipt_for_another_task"),
                 (rec(receipt(failure="TRANSPORT")), "phase_and_failure_disagree"),
                 (rec(receipt(approval_ref=None)), "approval_fields_inconsistent"),
                 (rec(receipt(grade=None)), "completion_without_its_evidence"),
                 (rec(receipt("blocked", "KNOWN", "PERMISSION", "NO_DATA", None)), "permission_block_after_start")]
        for record, cause in cases:
            self.assertEqual((told(record)["tasks"][0]["state"], told(record)["tasks"][0]["cause"]), ("NO_DATA", cause))

    def test_the_app_is_not_connected_yet(self):
        h = PWA.PWA.__new__(PWA.PWA)
        h.path, h.client_address, out = "/api/hexelion/tareas", ("127.0.0.1", 1), {}
        h._json = lambda code, body: out.update(code=code, body=body)
        PWA.PWA._tareas_leer(h)
        self.assertEqual((out["body"]["state"], out["body"]["cause"]), ("NO_DATA", "p2_mirror_not_built"))

    def test_nothing_finished_is_ever_invented(self):
        """Across every contract input, a DONE state appears only from a complete, KNOWN, gated, graded receipt."""
        inputs = [rec(None), rec(receipt(grade=None)), rec(receipt(outcome="UNKNOWN")), rec("done"), None,
                  rec(receipt("cancelled", "UNKNOWN", "CANCELLED", "NO_DATA", None)), rec(dict(receipt(), phase="done"))]
        for r in inputs:
            self.assertNotIn(told(r)["tasks"][0]["state"], DONE, json.dumps(r)[:120])


if __name__ == "__main__":
    unittest.main()
