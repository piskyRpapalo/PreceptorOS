import json
import subprocess
import sys
import unittest

import lexical_projector as P
from lexicon_state import LexiconState, compact_json, measured, unavailable


FRAME = {
    "id": "radio-building",
    "t": "Radio Building",
    "sound": "four soft notes",
    "motion": "steady",
    "atoms": [{"k": "channel", "i": [{"o": "channel", "tx": "local"}]}],
}


class LexiconStateTests(unittest.TestCase):
    def test_projection_is_stable_and_does_not_mutate_source(self):
        before = json.loads(json.dumps(FRAME))
        one, two = P.project(FRAME), P.project(FRAME)
        self.assertEqual(one.to_json(), two.to_json())
        self.assertEqual(FRAME, before)
        self.assertEqual(one.status, "LIVE")
        self.assertEqual(one.as_dict()["v"], "preceptoros.lexical-projection/1")
        self.assertLess(one.measured_bytes, 1024)

    def test_missing_measurements_keep_cause(self):
        result = P.project({"id": "radio-building"})
        self.assertEqual(result.status, "NO_DATA")
        self.assertIn("missing frame fields", result.cause)
        self.assertNotIn("p", result.as_dict())

    def test_unknown_and_untyped_items_fail_closed(self):
        unknown = dict(FRAME, atoms=[{"k": "x", "i": [{"o": "x", "private": "x"}]}])
        untyped = dict(FRAME, atoms=[{"k": "x", "i": [{}]}])
        self.assertEqual(P.project(unknown).status, "NO_DATA")
        self.assertEqual(P.project(untyped).status, "NO_DATA")

    def test_no_data_state_keeps_declared_cause(self):
        result = P.project(FRAME, status="NO_DATA", cause="source was not captured")
        self.assertEqual(result.status, "NO_DATA")
        self.assertEqual(result.cause, "source was not captured")

    def test_unicode_counts_utf8_bytes(self):
        value = measured({"label": "é"})
        self.assertEqual(value.measured_bytes, len(compact_json({"label": "é"})))
        text = json.dumps({"label": "é"}, ensure_ascii=False, separators=(",", ":"))
        self.assertGreater(value.measured_bytes, len(text))

    def test_overflow_rejects_whole_payload(self):
        value = measured({"label": "x" * 1024})
        self.assertEqual(value.status, "NO_DATA")
        self.assertGreaterEqual(value.measured_bytes, 1024)
        self.assertNotIn("p", value.as_dict())

    def test_status_cause_contract_is_strict(self):
        with self.assertRaises(ValueError):
            LexiconState("NO_DATA")
        with self.assertRaises(ValueError):
            unavailable(" ")


if __name__ == "__main__":
    unittest.main()
