"""Notebook receipts producer: sanitized, deterministic, honest about what a receipt proves.

Every fixture is synthetic. The command texts below are invented markers used
only to prove they never reach the projection.
"""
import datetime as dt
import io
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import notebook_receipts as nr

NOW = dt.datetime(2026, 11, 11, 12, 0, 0, tzinfo=dt.timezone.utc)
MARK = "synthetic-marker-command --flag example-value"


def raw(ts="2026-11-11T11:59:00Z", **extra):
    row = {"ts": ts, "tool": "exec", "cmd": MARK, "cmd_sha": "0123456789abcdef",
           "rc": 0, "out_bytes": 4, "ms": 15}
    row.update(extra)
    return json.dumps(row)


class Clean(unittest.TestCase):
    def test_a_valid_receipt_keeps_only_the_allowlisted_fields(self):
        record, cause = nr.clean(raw())
        self.assertIsNone(cause)
        self.assertEqual(sorted(record), ["cmd_sha", "measured_at", "ms", "out_bytes", "rc",
                                          "receipt_sha256", "result", "tool"])
        self.assertEqual(record["result"], "ok")
        self.assertRegex(record["receipt_sha256"], r"^[0-9a-f]{64}$")

    def test_the_command_text_and_unknown_keys_never_reach_the_record(self):
        record, _ = nr.clean(raw(note="another-synthetic-marker", args=["x"]))
        text = json.dumps(record)
        self.assertNotIn("synthetic-marker", text)
        self.assertNotIn("cmd\"", text.replace("cmd_sha", ""))
        self.assertNotIn("note", text)
        self.assertNotIn("args", text)

    def test_a_failed_command_is_a_declared_failure_not_a_missing_one(self):
        record, cause = nr.clean(raw(rc=2))
        self.assertIsNone(cause)
        self.assertEqual((record["rc"], record["result"]), (2, "failed"))

    def test_bad_lines_are_rejected_with_their_cause(self):
        cases = {
            "not json": "invalid_json",
            "[1, 2]": "invalid_object",
            '{"ts": "2026-11-11T11:59:00Z", "ts": "2026-11-11T11:59:00Z"}': "invalid_json",
            raw(ts="2026-11-11 11:59"): "invalid_timestamp",
            raw(ts="2026-13-41T11:59:00Z"): "invalid_timestamp",
            raw(tool="Exec; rm"): "invalid_tool",
            raw(tool=7): "invalid_tool",
            raw(cmd_sha="XYZ"): "invalid_cmd_sha",
            raw(cmd_sha="0123456789abcdef0"): "invalid_cmd_sha",
            raw(rc=True): "invalid_rc",
            raw(rc="0"): "invalid_rc",
            raw(rc=9999): "invalid_rc",
            raw(ms=-1): "invalid_ms",
            raw(ms=1.5): "invalid_ms",
            raw(out_bytes=-4): "invalid_out_bytes",
        }
        for line, expected in cases.items():
            with self.subTest(expected=expected, line=line[:40]):
                self.assertEqual(nr.clean(line), (None, expected))


class Project(unittest.TestCase):
    def test_states_follow_the_evidence(self):
        fresh, old, future = raw(), raw(ts="2026-11-11T11:00:00Z", ms=16), raw(ts="2026-11-11T12:00:01Z", ms=17)
        out = nr.project([old, future, fresh], NOW)
        states = [(r["status"], r["cause"]) for r in out["receipts"]]
        self.assertEqual(states, [("STALE", "receipt_older_than_600s"),
                                  ("NO_DATA", "future_timestamp"),
                                  ("DECLARED", "execution_receipt_only_result_not_checked")])
        self.assertEqual((out["status"], out["cause"]), states[-1])

    def test_the_freshness_edge_is_600_seconds_inclusive(self):
        edge = nr.project([raw(ts="2026-11-11T11:50:00Z")], NOW)["receipts"][0]
        past = nr.project([raw(ts="2026-11-11T11:49:59Z")], NOW)["receipts"][0]
        self.assertEqual((edge["status"], past["status"]), ("DECLARED", "STALE"))

    def test_verified_only_when_the_exact_receipt_was_checked(self):
        plain = nr.project([raw()], NOW)["receipts"][0]
        self.assertEqual(plain["status"], "DECLARED")
        checked = nr.project([raw()], NOW, verified={plain["receipt_sha256"]})["receipts"][0]
        self.assertEqual((checked["status"], checked["cause"]), ("VERIFIED", "independent_check_recorded"))
        other = nr.project([raw(ms=99)], NOW, verified={plain["receipt_sha256"]})["receipts"][0]
        self.assertEqual(other["status"], "DECLARED")
        # A command fingerprint alone verifies nothing.
        by_cmd = nr.project([raw()], NOW, verified={"0123456789abcdef"})["receipts"][0]
        self.assertEqual(by_cmd["status"], "DECLARED")

    def test_no_data_always_carries_a_cause(self):
        self.assertEqual(nr.project([], NOW)["cause"], "source_empty")
        self.assertEqual(nr.project(["", "  "], NOW)["cause"], "source_empty")
        self.assertEqual(nr.project(["nope"], NOW)["cause"], "no_valid_receipt")
        self.assertEqual(nr.project([], NOW, source_cause="file_missing")["cause"], "file_missing")
        for out in (nr.project([], NOW), nr.project(["nope"], NOW)):
            self.assertEqual(out["status"], "NO_DATA")
            self.assertEqual(out["receipts"], [])

    def test_rejected_lines_are_counted_never_copied(self):
        out = nr.project([raw(), "another-synthetic-marker", raw(rc="x"), raw(rc="y")], NOW)
        self.assertEqual(out["counts"], {"read": 4, "kept": 1, "rejected": {"invalid_json": 1, "invalid_rc": 2}})
        self.assertNotIn("synthetic-marker", json.dumps(out))

    def test_two_identical_runs_give_the_same_bytes(self):
        lines = [raw(ms=n) for n in range(5)] + ["broken"]
        a, b = nr.project(lines, NOW), nr.project(lines, NOW)
        self.assertEqual(nr._encode(a), nr._encode(b))
        self.assertEqual(a["projection_sha256"], b["projection_sha256"])
        self.assertNotEqual(a["projection_sha256"], nr.project(lines[:4], NOW)["projection_sha256"])

    def test_only_the_latest_receipts_are_kept_and_the_file_stays_small(self):
        out = nr.project([raw(ms=n) for n in range(300)], NOW)
        self.assertEqual(out["counts"]["read"], 300)
        self.assertEqual(len(out["receipts"]), nr.MAX_RECEIPTS)
        self.assertEqual(out["receipts"][-1]["ms"], 299)
        self.assertLessEqual(len(nr._encode(out)), nr.MAX_OUT + 128)


class Files(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_the_source_is_read_and_a_missing_one_says_so(self):
        log = self.dir / "audit.jsonl"
        self.assertEqual(nr.read_source(log), ([], "file_missing"))
        log.write_text(raw() + "\n" + raw(ms=16) + "\n", encoding="utf-8")
        lines, cause = nr.read_source(log)
        self.assertIsNone(cause)
        self.assertEqual(len(lines), 2)

    def test_a_symlinked_source_is_refused(self):
        real = self.dir / "real.jsonl"
        real.write_text(raw() + "\n", encoding="utf-8")
        link = self.dir / "audit.jsonl"
        link.symlink_to(real)
        self.assertEqual(nr.read_source(link), ([], "symlink_forbidden"))

    def test_only_the_tail_of_a_long_log_is_read_and_the_cut_line_is_dropped(self):
        log = self.dir / "audit.jsonl"
        line = raw() + "\n"
        log.write_text(line * (nr.MAX_SOURCE // len(line) + 50), encoding="utf-8")
        lines, cause = nr.read_source(log)
        self.assertIsNone(cause)
        self.assertLessEqual(sum(len(x) + 1 for x in lines), nr.MAX_SOURCE)
        self.assertEqual({nr.clean(x)[1] for x in lines}, {None})

    def test_write_is_private_atomic_and_leaves_no_temp_file(self):
        target = nr.write(self.dir, nr.project([raw()], NOW))
        self.assertEqual(target, self.dir / "notebook" / "receipts.json")
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        self.assertEqual(sorted(p.name for p in target.parent.iterdir()), ["receipts.json"])
        saved = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(saved["schema"], "preceptoros.notebook-receipts/0")
        self.assertNotIn("synthetic-marker", target.read_text(encoding="utf-8"))
        nr.write(self.dir, nr.project([raw(), raw(ms=16)], NOW))
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["counts"]["kept"], 2)

    def test_write_refuses_a_symlinked_folder_or_file(self):
        elsewhere = self.dir / "elsewhere"
        elsewhere.mkdir()
        (self.dir / "notebook").symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(OSError):
            nr.write(self.dir, nr.project([raw()], NOW))
        self.assertEqual(list(elsewhere.iterdir()), [])
        other = self.dir / "other"
        (other / "notebook").mkdir(parents=True)
        victim = other / "victim.txt"
        victim.write_text("keep", encoding="utf-8")
        (other / "notebook" / "receipts.json").symlink_to(victim)
        with self.assertRaises(OSError):
            nr.write(other, nr.project([raw()], NOW))
        self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

    def test_the_command_line_prints_counts_only_and_dry_run_writes_nothing(self):
        log = self.dir / "audit.jsonl"
        log.write_text(raw() + "\nbroken\n", encoding="utf-8")
        home = self.dir / "home"
        home.mkdir()
        out = io.StringIO()
        with redirect_stdout(out):
            code = nr.main(["--source", str(log), "--root", str(home), "--dry-run"])
        self.assertEqual(code, 0)
        said = json.loads(out.getvalue())
        self.assertEqual(said["counts"], {"read": 2, "kept": 1, "rejected": {"invalid_json": 1}})
        self.assertFalse(said["written"])
        self.assertNotIn("receipts", said)
        self.assertNotIn("synthetic-marker", out.getvalue())
        self.assertEqual(list(home.iterdir()), [])
        with redirect_stdout(io.StringIO()):
            nr.main(["--source", str(log), "--root", str(home)])
        self.assertTrue((home / "notebook" / "receipts.json").is_file())

    def test_a_missing_log_is_written_as_no_data_with_its_cause(self):
        with redirect_stdout(io.StringIO()):
            nr.main(["--source", str(self.dir / "absent.jsonl"), "--root", str(self.dir)])
        saved = json.loads((self.dir / "notebook" / "receipts.json").read_text(encoding="utf-8"))
        self.assertEqual((saved["status"], saved["cause"], saved["receipts"]), ("NO_DATA", "file_missing", []))


class Source(unittest.TestCase):
    def test_the_producer_has_no_network_subprocess_or_scheduler(self):
        text = Path(nr.__file__).read_text(encoding="utf-8")
        for banned in ("import subprocess", "import socket", "urllib", "http.client", "os.system", "import sched"):
            self.assertNotIn(banned, text)


if __name__ == "__main__":
    unittest.main()
