import json
import unittest
import argparse

import canal_event
import rack_freshness


class ChannelContractTests(unittest.TestCase):
    def make_event(self, stamp="LIVE"):
        return json.dumps({
            "version": 1,
            "ancla": "a" * 64,
            "utc": "2026-10-19T10:30:00Z",
            "sello": stamp,
            "payload": {},
        }, separators=(",", ":")).encode()

    def test_accepts_all_six_canonical_stamps(self):
        for stamp in sorted(canal_event.STAMPS):
            with self.subTest(stamp=stamp):
                self.assertEqual(canal_event.validate_event(self.make_event(stamp))["sello"], stamp)

    def test_rejects_oversized_event_before_parsing(self):
        raw = self.make_event() + b" " * canal_event.MAX_EVENT_BYTES
        with self.assertRaisesRegex(canal_event.EventRejected, "rejected whole"):
            canal_event.validate_event(raw)

    def test_rejects_invalid_stamp_and_non_rfc3339_utc(self):
        event = json.loads(self.make_event())
        event["sello"] = []
        with self.assertRaises(canal_event.EventRejected):
            canal_event.validate_event(json.dumps(event).encode())
        event["sello"] = "LIVE"
        event["utc"] = "2026-10-19T10:30Z"
        with self.assertRaises(canal_event.EventRejected):
            canal_event.validate_event(json.dumps(event).encode())

    def test_rejects_duplicate_keys_and_invalid_utf8(self):
        raw = self.make_event().replace(b'"version":1', b'"version":1,"version":1')
        with self.assertRaises(canal_event.EventRejected):
            canal_event.validate_event(raw)
        with self.assertRaisesRegex(canal_event.EventRejected, "invalid UTF-8"):
            canal_event.validate_event(b"\xff")


class RackFreshnessTests(unittest.TestCase):
    def test_live_becomes_stale_at_exact_ttl(self):
        observed = rack_freshness.parse_utc("2026-10-12T10:00:00Z")
        before = rack_freshness.parse_utc("2026-10-19T09:59:59Z")
        boundary = rack_freshness.parse_utc("2026-10-19T10:00:00Z")
        self.assertEqual(rack_freshness.freshness("LIVE", observed, before), "LIVE")
        self.assertEqual(rack_freshness.freshness("LIVE", observed, boundary), "STALE")

    def test_non_live_stamps_keep_their_state(self):
        now = rack_freshness.parse_utc("2026-10-19T10:00:00Z")
        for stamp in sorted(rack_freshness.STAMPS - {"LIVE"}):
            with self.subTest(stamp=stamp):
                self.assertEqual(rack_freshness.freshness(stamp, None, now), stamp)

    def test_timezone_is_required(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            rack_freshness.parse_utc("2026-10-19T10:00:00")


if __name__ == "__main__":
    unittest.main()
