"""Bounded channel event (P02): one ceiling for the whole house, < 1,024 UTF-8 bytes (RC-07), rejected whole."""
import json
import unittest

import canal_event as c


def raw_of_size(n, stamp="LIVE"):
    base = {"version": 1, "ancla": "a" * 64, "utc": "2026-10-19T00:00:00Z", "sello": stamp, "payload": {"t": ""}}
    pad = n - len(json.dumps(base, separators=(",", ":")).encode())
    base["payload"]["t"] = "x" * pad
    raw = json.dumps(base, separators=(",", ":")).encode()
    assert len(raw) == n
    return raw


class CanalEvent(unittest.TestCase):
    def test_1023_bytes_pass(self):
        self.assertEqual(c.validate_event(raw_of_size(1023))["sello"], "LIVE")

    def test_1024_bytes_rejected_whole_rc07(self):
        with self.assertRaises(c.EventRejected):
            c.validate_event(raw_of_size(1024))

    def test_schema_declares_the_same_ceiling(self):
        with open("data/canal_event.schema.json", encoding="utf-8") as f:
            self.assertEqual(json.load(f)["x-max-serialized-utf8-bytes"], 1023)

    def test_six_canonical_stamps_and_nothing_else(self):
        for s in ("LIVE", "STALE", "STATIC", "SIMULATED", "NO_DATA", "ERROR"):
            self.assertEqual(c.validate_event(raw_of_size(200, s))["sello"], s)
        with self.assertRaises(c.EventRejected):
            c.validate_event(raw_of_size(200, "MEDIDO"))

    def test_shape_duplicates_and_text_are_rejected(self):
        for bad in (b'{"version":1}', b'not json', '{"a":1}'.encode()[:-1],
                    b'{"version":1,"version":1,"ancla":"","utc":"","sello":"LIVE","payload":{}}'):
            with self.assertRaises(c.EventRejected):
                c.validate_event(bad)
        with self.assertRaises(c.EventRejected):
            c.validate_event("text, not bytes")


if __name__ == "__main__":
    unittest.main()
