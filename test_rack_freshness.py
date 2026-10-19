"""Rack freshness (P08): TTL_DAYS is an exact integer; LIVE turns STALE at the TTL; the CLI works without --now."""
import datetime as dt
import json
import subprocess
import sys
import unittest

import rack_freshness as r

UTC = dt.timezone.utc


class RackFreshness(unittest.TestCase):
    def test_ttl_is_an_exact_integer(self):
        self.assertIs(type(r.TTL_DAYS), int)
        self.assertEqual(r.TTL_SECONDS, r.TTL_DAYS * 86400)

    def test_live_turns_stale_exactly_at_the_ttl(self):
        seen = dt.datetime(2026, 10, 10, tzinfo=UTC)
        just_before = seen + dt.timedelta(seconds=r.TTL_SECONDS - 1)
        at_ttl = seen + dt.timedelta(seconds=r.TTL_SECONDS)
        self.assertEqual(r.freshness("LIVE", seen, just_before), "LIVE")
        self.assertEqual(r.freshness("LIVE", seen, at_ttl), "STALE")

    def test_other_stamps_pass_through_and_missing_observation_is_no_data(self):
        for s in ("STALE", "STATIC", "SIMULATED", "NO_DATA", "ERROR"):
            self.assertEqual(r.freshness(s, None), s)
        self.assertEqual(r.freshness("LIVE", None), "NO_DATA")
        with self.assertRaises(ValueError):
            r.freshness("MEDIDO", None)

    def test_cli_with_now(self):
        out = subprocess.run([sys.executable, "rack_freshness.py", "--observed-at", "2026-10-10T00:00:00Z",
                              "--now", "2026-10-19T00:00:00Z"], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(out.stdout)["state"], "STALE")

    def test_cli_without_now_uses_the_current_utc_clock(self):
        out = subprocess.run([sys.executable, "rack_freshness.py", "--observed-at", "2000-01-01T00:00:00Z"],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr[-300:])
        self.assertEqual(json.loads(out.stdout)["state"], "STALE")


if __name__ == "__main__":
    unittest.main()
