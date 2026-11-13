"""Acho expression · what just happened, as form, line and tone (ACHO-EXPRESSION, 2026-11-13).

The class and state come from the turn or task row; acho_motion.express only draws them, next to words that are
already on screen. Pinned here without a browser (the engine is pure in Node); the walk measures it rendered.
"""
from __future__ import annotations

import json
import unittest

import audio_feedback as AF
import tareas_hexelion as K
import turnos_hexelion as T
from test_talk_turn_parity import node

LOAD = "require('./interface/acho_motion.js');const A=globalThis.AchoMotion;"


class Expression(unittest.TestCase):
    def setUp(self):
        self.table = node(LOAD + "console.log(JSON.stringify(A.expressions))")

    def test_each_expression_looks_different_without_colour(self):
        pairs = [(e["form"], e["line"]) for e in self.table.values()]
        self.assertEqual(len(set(pairs)), len(pairs), "two expressions share form and line")
        for e in self.table.values():
            self.assertIn(e["line"], ("solid", "double", "dashed", "dotted"))

    def test_nothing_moves_without_evidence(self):
        still = {k for k, e in self.table.items() if not e["moves"]}
        self.assertEqual(still, {"waiting", "uncertain", "silent", "proposed"})

    def test_the_five_moments_are_told_apart(self):
        got = node(LOAD + "console.log(JSON.stringify([A.expressionOf(null,'waiting'),A.expressionOf('ok','ANSWERED'),"
                   "A.expressionOf('ok','ACTED'),A.expressionOf('fence','ACTION_REFUSED'),"
                   "A.expressionOf('exec_fail','ACTION_REFUSED'),A.expressionOf('uncertain','OUTCOME_UNKNOWN'),"
                   "A.expressionOf('needs_you','NEEDS_YOUR_AUTHORIZATION'),A.expressionOf('bridge_down','NO_ANSWER'),"
                   "A.expressionOf('nonsense','X'),A.expressionOf(null,'')]))")
        self.assertEqual(got, ["waiting", "answer", "verified", "refused", "refused", "uncertain", "needs_you",
                               "silent", "silent", "silent"])

    def test_every_class_the_server_can_send_has_an_expression(self):
        for cls in AF.ACHO_CLASSES:
            self.assertIn(node(LOAD + "console.log(JSON.stringify(A.expressionOf(%s,'')))" % json.dumps(cls)),
                          self.table)


class UncertaintyHasItsOwnCue(unittest.TestCase):
    def test_uncertain_is_a_distinct_sound_and_class(self):
        motifs = {c: json.dumps(AF.motif_for_class(c), sort_keys=True) for c in AF.ACHO_CLASSES}
        self.assertEqual(len(set(motifs.values())), len(motifs))
        self.assertTrue(AF.motif_for_class("uncertain")["vibrato"])

    def test_unproven_or_unknown_outcomes_are_uncertain_never_silent_or_ok(self):
        self.assertEqual(T.ACHO["ACTION_UNVERIFIED"], "uncertain")
        self.assertEqual((K.ACHO["OUTCOME_UNKNOWN"], K.ACHO["NO_RESULT_RECORDED"]), ("uncertain", "uncertain"))
        self.assertEqual(T.acho_class({"state": "ANSWERED_UNVERIFIED"}), "empty")    # words, not a possible action


if __name__ == "__main__":
    unittest.main()
