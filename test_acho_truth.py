"""Acho is the flag of verifiable truth, not the judge (APP-P1-ACHO, Mesa #3, 2026-11-13).

Before this change a task whose receipt was SIMULATED (basis `synthetic`) and passed its check was class `ok`: Acho drew
the `verified` expression (double line, moving, ok tone) and the cue took the MEASURED motif, while the words said
"Simulated run". Another voice's reply (turn REPLIED), checked by nobody here, sounded and looked like a success too.

Invariant: SIMULATED != VERIFIED. The success class needs MEASURED evidence. A proposal or simulation is `proposed`
(a question's form on a dashed line, quiet, still, the proposal motif); a claim whose evidence cannot be named is
silence. Six facts, six marks that differ in form and line (never colour alone), in words, and in motif. Sound stays
off until the person turns it on; reduced motion and a failed Web Audio never change the fact (pinned elsewhere:
test_acho_expression, test_acho_sonido, test_a11y_proof).
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import audio_feedback as AF
import tareas_hexelion as K
import turnos_hexelion as T
from test_talk_turn_parity import node
from test_tareas_hexelion import rec, receipt

ROOT = Path(__file__).resolve().parent
LOAD = "require('./interface/acho_motion.js');const A=globalThis.AchoMotion;"


def drawn(rows):
    """[(class, state)] -> the expression acho_motion draws for each, plus the expression table."""
    return node(LOAD + "console.log(JSON.stringify({got:%s.map(([c,s])=>A.expressionOf(c,s)),table:A.expressions}))"
                % json.dumps(rows))


SIX = {
    "verified": rec(receipt()),                                                   # protocol_roundtrip: MEASURED
    "proposed_or_simulated": rec(receipt(confidence_basis="synthetic")),
    "missing_evidence": rec(receipt(receipt_ref="not-a-ref")),
    "unknown": rec(receipt("failed", "UNKNOWN", "UNKNOWN", "NO_DATA", None)),
    "human_required": rec(receipt("blocked", "NOT_STARTED", "PERMISSION", "NO_DATA", None)),
    "rejected": rec(receipt("failed", "NOT_STARTED", "TRANSPORT", "NO_DATA", None)),
}


class SixFactsSixMarks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {k: K.task(r) for k, r in SIX.items()}
        out = drawn([[t["acho"]["class"], t["state"]] for t in cls.rows.values()])
        cls.expr = dict(zip(cls.rows, out["got"]))
        cls.table = out["table"]

    def test_each_fact_has_its_own_expression(self):
        self.assertEqual(self.expr, {"verified": "verified", "proposed_or_simulated": "proposed",
                                     "missing_evidence": "silent", "unknown": "uncertain",
                                     "human_required": "needs_you", "rejected": "refused"})

    def test_told_apart_by_form_and_line_words_and_motif_not_colour(self):
        marks = {(self.table[e]["form"], self.table[e]["line"]) for e in self.expr.values()}
        self.assertEqual(len(marks), 6)
        self.assertEqual(len({t["sentence"] for t in self.rows.values()}), 6)
        motifs = {json.dumps(AF.motif_for_class(t["acho"]["class"]), sort_keys=True) for t in self.rows.values()}
        self.assertEqual(len(motifs), 6)

    def test_the_words_carry_the_fact_and_the_cue_reads_them(self):
        sim = self.rows["proposed_or_simulated"]
        self.assertTrue(sim["sentence"].startswith("Simulated run: "))
        cue = AF.cue_for_turn(sim)
        self.assertEqual((cue["clase"], cue["texto"], cue["sonido"]), ("proposed", sim["reader"], "INACTIVO"))


class SimulatedIsNeverVerified(unittest.TestCase):
    """For every receipt shape, a simulated or evidence-less row never reaches the success mark, tone, motion or motif."""

    SHAPES = [receipt(), receipt(grade="NOT_EVALUATED"), receipt("blocked", "NOT_STARTED", "PERMISSION", "NO_DATA", None),
              receipt("failed", "UNKNOWN", "UNKNOWN", "NO_DATA", None)]

    def test_no_simulated_or_unnamed_evidence_reads_as_success(self):
        rows = []
        for shape in self.SHAPES:
            for over in ({"confidence_basis": "synthetic"}, {"receipt_ref": "not-a-ref"}, {"confidence_basis": "trust_me"}):
                t = K.task(rec(dict(shape, **over)))
                rows.append(t)
                self.assertNotEqual(t["acho"]["class"], "ok", (shape["phase"], over))
        out = drawn([[t["acho"]["class"], t["state"]] for t in rows])
        success = AF.motif_for_class("ok")
        for t, e in zip(rows, out["got"]):
            mark = out["table"][e]
            self.assertNotEqual(e, "verified")
            self.assertNotEqual(mark["tone"], "ok")
            self.assertNotEqual(AF.motif_for_class(t["acho"]["class"]), success)

    def test_a_right_looking_answer_is_still_only_a_proposal(self):
        # The words of a passed check with a simulated basis: the sentence never upgrades the class.
        t = K.task(rec(receipt(confidence_basis="synthetic")))
        self.assertIn("passed its check", t["sentence"])
        self.assertEqual((t["state"], t["evidence"]["origin"], t["acho"]["class"]), ("DONE_CHECKED", "SIMULATED", "proposed"))
        self.assertFalse(drawn([["proposed", "DONE_CHECKED"]])["table"]["proposed"]["moves"])

    def test_only_measured_evidence_reaches_the_success_mark(self):
        for basis in ("public_deterministic_reference", "protocol_roundtrip"):
            t = K.task(rec(receipt(confidence_basis=basis)))
            self.assertEqual((t["evidence"]["origin"], t["acho"]["class"]), ("MEASURED", "ok"), basis)


class AnotherVoiceIsAProposal(unittest.TestCase):
    def test_a_reply_nobody_checked_is_proposed(self):
        self.assertEqual(T.acho_class({"state": "REPLIED"}), "proposed")
        self.assertEqual(drawn([["proposed", "REPLIED"]])["got"], ["proposed"])
        for state in ("ANSWERED", "ACTED", "LOCAL_SENSOR"):       # unchanged: they carry their own check
            self.assertEqual(T.acho_class({"state": state}), "ok", state)


class ActedIsTheContractNotTheOutput(unittest.TestCase):
    """ACTED proves the action ran under its documented execution contract; it never says the output is right."""

    def test_acted_words_claim_execution_and_ask_for_the_result_check(self):
        self.assertIn("Check the result", T.NEXT["ACTED"])
        src = (ROOT / "turnos_hexelion.py").read_text(encoding="utf-8")
        said = src[src.index('turn.update(state="ACTED"'):src.index('elif state == "ACTION_REFUSED"')]
        self.assertIn("ran the action", said)
        self.assertNotRegex(said.lower(), r"\b(correct|right answer|verified output|succeeded)\b")


class EveryReaderKnowsTheNewClass(unittest.TestCase):
    def test_server_tables_and_both_clients_list_proposed(self):
        self.assertIn("proposed", AF.ACHO_CLASSES)
        got = node("const N=require('./interface/notebook.js');const S=require('./interface/acho_sonido.js');"
                   "console.log(JSON.stringify([N.achoClasses.includes('proposed'),"
                   "S.classes.includes('proposed')]))")
        self.assertEqual(got, [True, True])


if __name__ == "__main__":
    unittest.main()
