"""Weekly and monthly review files from benchmark receipts: a list with a fingerprint, never a copied figure."""
import datetime as dt
import io
import json
import re
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import notebook_reports as nr

NOW = dt.datetime(2026, 11, 11, 12, 0, 0, tzinfo=dt.timezone.utc)


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.rec = self.dir / "receipts"
        self.rec.mkdir()

    def put(self, name, text="{}"):
        (self.rec / name).write_text(text, encoding="utf-8")


class Receipts(Base):
    def test_only_dated_receipt_names_count_oldest_first(self):
        for name in ("20261111-b-run.json", "20261103-a-run.md", "README.md", "notes.txt", "2026111-bad.json",
                     "20261340-bad-date.json"):
            self.put(name)
        (self.rec / "remote-ci-runs").mkdir()
        found, cause = nr.receipts(self.rec)
        self.assertEqual([n for _, n, _ in found], ["20261103-a-run.md", "20261111-b-run.json"])
        self.assertEqual(cause, "skipped_1")

    def test_a_symlinked_receipt_is_not_followed(self):
        self.put("20261111-real.json")
        (self.rec / "20261110-link.json").symlink_to(self.rec / "20261111-real.json")
        self.assertEqual([n for _, n, _ in nr.receipts(self.rec)[0]], ["20261111-real.json"])

    def test_a_missing_folder_says_so(self):
        self.assertEqual(nr.receipts(self.dir / "absent"), ([], "folder_unreadable"))


class Review(Base):
    def test_periods_follow_the_calendar(self):
        self.assertEqual(nr.week_of(dt.date(2026, 11, 11)), "2026-W46")
        self.assertEqual(nr.week_of(dt.date(2027, 1, 1)), "2026-W53")
        self.assertEqual(nr.month_of(dt.date(2026, 11, 11)), "2026-11")

    def test_a_review_fits_the_readers_contract(self):
        self.put("20261109-first.json", '{"tokens_per_second": 33}')
        self.put("20261111-second.md", "secret-figure 9999")
        found, _ = nr.receipts(self.rec)
        for kind, period in (("wbr", "2026-W46"), ("mbr", "2026-11")):
            doc = nr.review(kind, period, found, NOW)
            self.assertEqual(sorted(doc), ["measured_at", "period", "receipt_sha256", "schema", "summary"])
            self.assertEqual(doc["schema"], "preceptoros.%s/1" % kind)
            self.assertLessEqual(len(doc["period"]), 16)
            self.assertLessEqual(len(doc["summary"]), 420)
            self.assertRegex(doc["receipt_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(doc["measured_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            self.assertTrue(doc["summary"].startswith("2 receipt files for 2 benchmarks dated in " + period + ": first, second."))
            self.assertNotIn("9999", json.dumps(doc))
            self.assertNotIn("33", doc["summary"])

    def test_the_fingerprint_changes_when_a_receipt_changes(self):
        self.put("20261111-run.json", "a")
        one = nr.review("wbr", "2026-W46", nr.receipts(self.rec)[0], NOW)
        self.assertEqual(one, nr.review("wbr", "2026-W46", nr.receipts(self.rec)[0], NOW))
        self.put("20261111-run.json", "b")
        self.assertNotEqual(one["receipt_sha256"], nr.review("wbr", "2026-W46", nr.receipts(self.rec)[0], NOW)["receipt_sha256"])

    def test_a_benchmark_with_two_files_is_named_once(self):
        self.put("20261111-run.json")
        self.put("20261111-run.md")
        doc = nr.review("wbr", "2026-W46", nr.receipts(self.rec)[0], NOW)
        self.assertTrue(doc["summary"].startswith("2 receipt files for 1 benchmark dated in 2026-W46: run."))

    def test_a_period_without_receipts_gives_nothing(self):
        self.put("20261001-old.json")
        found, _ = nr.receipts(self.rec)
        self.assertIsNone(nr.review("wbr", "2026-W46", found, NOW))
        self.assertIsNone(nr.review("mbr", "2026-11", found, NOW))
        self.assertIsNotNone(nr.review("mbr", "2026-10", found, NOW))

    def test_many_receipts_still_fit(self):
        for i in range(60):
            self.put("20261111-a-rather-long-benchmark-receipt-name-%02d.json" % i)
        doc = nr.review("mbr", "2026-11", nr.receipts(self.rec)[0], NOW)
        self.assertLessEqual(len(doc["summary"]), 420)
        self.assertIn("60 receipt files for 60 benchmarks", doc["summary"])
        self.assertIn("…", doc["summary"])
        self.assertIn("Newest: 20261111-a-rather-long-benchmark-receipt-name-59.json", doc["summary"])


class Files(Base):
    def test_write_is_private_small_and_atomic(self):
        self.put("20261111-run.json")
        doc = nr.review("wbr", "2026-W46", nr.receipts(self.rec)[0], NOW)
        target = nr.write(self.dir, "wbr", doc)
        self.assertEqual(target, self.dir / "notebook" / "wbr.json")
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        self.assertLessEqual(target.stat().st_size, 4096)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), doc)
        self.assertEqual([p.name for p in target.parent.iterdir()], ["wbr.json"])

    def test_write_refuses_symlinks_and_oversized(self):
        (self.dir / "elsewhere").mkdir()
        (self.dir / "notebook").symlink_to(self.dir / "elsewhere", target_is_directory=True)
        with self.assertRaises(OSError):
            nr.write(self.dir, "wbr", {"a": 1})
        with self.assertRaises(ValueError):
            nr.write(self.dir / "other", "wbr", {"summary": "x" * 5000})

    def test_the_command_writes_only_periods_that_have_receipts(self):
        today = dt.datetime.now(dt.timezone.utc).date()
        self.put(today.strftime("%Y%m%d") + "-today.json")
        out = io.StringIO()
        with redirect_stdout(out):
            nr.main(["--receipts", str(self.rec), "--root", str(self.dir), "--dry-run"])
        said = json.loads(out.getvalue())
        self.assertEqual((said["receipts"], said["written"], said["wbr"]["status"]), (1, [], "DECLARED"))
        self.assertFalse((self.dir / "notebook").exists())
        with redirect_stdout(io.StringIO()):
            nr.main(["--receipts", str(self.rec), "--root", str(self.dir)])
        self.assertEqual(sorted(p.name for p in (self.dir / "notebook").iterdir()), ["mbr.json", "wbr.json"])
        empty = self.dir / "empty"
        empty.mkdir()
        out = io.StringIO()
        with redirect_stdout(out):
            nr.main(["--receipts", str(empty), "--root", str(self.dir / "fresh")])
        said = json.loads(out.getvalue())
        self.assertEqual((said["wbr"]["status"], said["wbr"]["cause"], said["written"]), ("NO_DATA", "no_receipt_in_period", []))
        self.assertFalse((self.dir / "fresh").exists())

    def test_no_network_subprocess_or_scheduler(self):
        text = Path(nr.__file__).read_text(encoding="utf-8")
        for banned in ("import subprocess", "import socket", "urllib", "http.client", "os.system"):
            self.assertNotIn(banned, text)


if __name__ == "__main__":
    unittest.main()
