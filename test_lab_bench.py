"""Lab benchmark reader (LAB #173 bench-repro-01-v1): re-derived fingerprints, separate timings, NO_DATA kept."""
from __future__ import annotations

import copy
import datetime as dt
import json
import pathlib
import subprocess
import tempfile
import unittest

import lab_bench as B
import notebook_read as N

ROOT = pathlib.Path(__file__).resolve().parent
NOW = dt.datetime(2026, 11, 12, 14, 0, tzinfo=dt.timezone.utc)


def receipt(date="2026-11-12T12:20:21+00:00", rate=54.8):
    r = {"schema": "bench-repro-01-v1", "experiment_id": "public-throughput-v1", "date_utc": date, "state": "MEASURED",
         "cause": None, "model_name": "tiny:1b", "model_digest": "a" * 64, "model_stable": True, "ollama_version": "0.40.3",
         "fixture_sha256": "b" * 64, "input_sha256": "c" * 64, "attempted": 2, "succeeded": 2, "failed": 0,
         "byte_identical": True, "settings": {"seed": 42, "temperature": 0},
         "source": {"commit": "d" * 40, "runner_sha256": "e" * 64},
         "samples": [{"attempt": i, "state": "MEASURED", "generation_tokens_per_s": rate + i / 10, "wall_ns": 3_000_000_000 - i,
                      "load_ns": 900_000_000 * i, "response_sha256": "f" * 64} for i in (1, 2)]}
    for name in B.NO_DATA_FIELDS:
        r[name] = {"state": "NO_DATA", "cause": name + "_not_measured"}
    r["comparison_key"] = B.comparison_key(r)
    return r


def bench_file(*receipts_, machine=True):
    doc = {"executions": [{"receipt": r, "receipt_sha256": B.receipt_fingerprint(r)} for r in receipts_]}
    if machine:
        doc["machine_class"] = {"state": "DECLARED", "value": "Small-box"}
    return json.dumps(doc).encode()


class Producer(unittest.TestCase):
    def test_a_valid_run_is_rechecked_and_told_plainly(self):
        p = B.project([("20261112-run.json", bench_file(receipt()))], NOW)
        self.assertEqual((p["state"], p["counts"]["runs"]), ("DECLARED", 1))
        run = p["runs"][0]
        self.assertEqual((run["fingerprint"], run["comparison_key"]), ("RECHECKED", "RECHECKED"))
        self.assertEqual([(s["tokens_per_s"], s["wall_ms"], s["load_ms"]) for s in run["samples"]],
                         [(54.9, 3000, 900), (55.0, 3000, 1800)])      # wall and load kept apart, per sample
        self.assertEqual({m["field"] for m in run["not_measured"]}, set(B.NO_DATA_FIELDS))
        self.assertIn("54.9–55.0 tokens/s over 2 samples", run["sentence"])
        self.assertIn("declared Small-box (DECLARED)", run["sentence"])
        self.assertIn("were not measured", run["sentence"])
        self.assertEqual(p["projection_sha256"], B.projection_fingerprint(p["runs"]))

    def test_tampered_or_foreign_receipts_are_refused_with_their_cause(self):
        good = receipt()
        bent = json.loads(bench_file(good))
        bent["executions"][0]["receipt"]["samples"][0]["generation_tokens_per_s"] = 99.0
        other = copy.deepcopy(good)
        other["schema"] = "preceptoros.lab.harness-receipt/1"
        files = [("20261112-bent.json", json.dumps(bent).encode()), ("20261112-other.json", bench_file(other)),
                 ("20261112-dup.json", b'{"executions": [], "executions": []}'), ("20261112-x.json", b"[1]")]
        p = B.project(files, NOW)
        self.assertEqual(p["runs"], [])
        self.assertEqual(p["counts"]["rejected"], {"invalid_json": 1, "not_a_bench_file": 1,
                                                   "receipt_fingerprint_mismatch": 1, "schema_not_bench_repro_01_v1": 1})
        self.assertEqual((p["state"], p["cause"]), ("NO_DATA", "no_valid_bench_receipt"))
        self.assertEqual(B.project([], NOW)["cause"], "source_empty")

    def test_a_comparison_key_that_does_not_match_its_controls_is_shown_as_mismatch(self):
        r = receipt()
        r["comparison_key"] = "0" * 64
        run = B.project([("20261112-k.json", bench_file(r))], NOW)["runs"][0]
        self.assertEqual((run["fingerprint"], run["comparison_key"]), ("RECHECKED", "MISMATCH"))

    def test_undeclared_machine_and_failed_run(self):
        r = receipt()
        r.update(state="FAILED", cause="model_not_installed", samples=[])
        r["comparison_key"] = B.comparison_key(r)
        run = B.project([("20261112-f.json", bench_file(r, machine=False))], NOW)["runs"][0]
        self.assertEqual(run["machine"], "NO_DATA")
        self.assertEqual(run["sentence"], "tiny:1b: no throughput was measured (model_not_installed).")

    def test_ceiling_keeps_the_newest_runs_and_same_input_same_output(self):
        files = [("20261112-r%02d.json" % i, bench_file(receipt(date="2026-11-12T12:%02d:00+00:00" % i))) for i in range(12)]
        p = B.project(files, NOW)
        self.assertLessEqual(len(B.encode(p)), B.MAX_OUT)
        self.assertEqual(p["runs"][-1]["date"], "2026-11-12T12:11:00+00:00")
        self.assertEqual(B.encode(p), B.encode(B.project(list(reversed(files)), NOW)))

    def test_git_source_reads_a_ref_without_touching_the_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = lambda *a: subprocess.run(["git", "-C", tmp, *a], check=True, capture_output=True)
            run("init", "-q")
            folder = pathlib.Path(tmp, "benchmarks/receipts")
            folder.mkdir(parents=True)
            (folder / "20261112-run.json").write_bytes(bench_file(receipt()))
            run("add", ".")
            run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "r")
            (folder / "20261112-run.json").write_text("local edit, not committed")
            files = B.from_git(tmp, "HEAD")
            self.assertEqual(B.project(files, NOW)["counts"]["runs"], 1)
            self.assertEqual((folder / "20261112-run.json").read_text(), "local edit, not committed")
            self.assertEqual(B.from_git(tmp, "no-such-ref"), [])


class Reader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        B.write(self.root, B.project([("20261112-run.json", bench_file(receipt()))], NOW))

    def tearDown(self):
        self.tmp.cleanup()

    def test_reader_recomputes_the_projection_fingerprint(self):
        state = N.read(self.root, NOW)
        self.assertIsNone(state["bench_cause"])
        self.assertEqual(len(state["bench"]), 1)
        path = self.root / "notebook" / "bench.json"
        doc = json.loads(path.read_text())
        doc["runs"][0]["sentence"] = "tiny:1b generated 900 tokens/s."
        path.write_text(json.dumps(doc))
        state = N.read(self.root, NOW)
        self.assertEqual((state["bench"], state["bench_cause"]), ([], "projection_fingerprint_mismatch"))
        path.unlink()
        self.assertEqual(N.read(self.root, NOW)["bench_cause"], "file_missing")

    def test_views_show_the_same_runs_in_lab_and_notebook(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        js = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")
        app = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        for ident in ("lab-bench", "lab-bench-status", "notebook-bench", "notebook-bench-status"):
            self.assertIn('id="%s"' % ident, html)
        self.assertIn('loadBench("lab-bench", "lab-bench-status")', app)
        self.assertIn('loadBench("notebook-bench", "notebook-bench-status"', js)
        block = js[js.index("function benchCard"):js.index("async function loadTurns")]
        self.assertIn('"Not measured"', block)
        self.assertIn("spoken[statusId] !== summary", block)
        self.assertNotRegex(block, r"\.focus\(|speechSynthesis|innerHTML|setInterval")


if __name__ == "__main__":
    unittest.main()
