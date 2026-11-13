"""The Notebook mirrors Hexelion's actions (mission «App viva», 2026-11-12): MCP S-3 receipts say who acted and whether
the fence refused it; the projection is renewed when the Notebook opens; old receipts keep their fingerprints; the
refusal cause and the command text never leave the private log."""
import datetime as dt
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import notebook_read
import notebook_receipts as P

ROOT = Path(__file__).resolve().parent
NOW = dt.datetime(2026, 11, 12, 22, 0, 30, tzinfo=dt.timezone.utc)
OLD = {"ts": "2026-11-12T22:00:00Z", "tool": "exec", "cmd": "ss -tln", "cmd_sha": "15788a033b68dfe1",
       "rc": 0, "out_bytes": 10, "ms": 5}
ACTED = dict(OLD, voz="hexelion", tool="state", cmd="state")
REFUSED = {"ts": "2026-11-12T22:00:10Z", "tool": "exec", "voz": "hexelion", "cmd": "git merge secret-branch",
           "cmd_sha": "ec9eb388561b3750", "rc": -1, "out_bytes": 0, "ms": 0, "denied": True, "causa": "linea dura: git"}


def lines(*rows):
    return [json.dumps(r) for r in rows]


class Producer(unittest.TestCase):
    def test_who_acted_and_a_fence_refusal_are_kept_but_never_the_cause_or_the_command(self):
        out = P.project(lines(OLD, ACTED, REFUSED), NOW)
        old, acted, refused = out["receipts"]
        self.assertNotIn("voice", old)
        self.assertEqual((acted["voice"], acted["result"]), ("hexelion", "ok"))
        self.assertEqual((refused["voice"], refused["result"], refused["denied"]), ("hexelion", "refused", True))
        text = json.dumps(out)
        for leak in ("linea dura", "secret-branch", "git merge", "causa"):
            self.assertNotIn(leak, text)

    def test_an_old_receipt_keeps_its_fingerprint(self):
        record = {"measured_at": OLD["ts"], "tool": "exec", "cmd_sha": OLD["cmd_sha"], "rc": 0, "ms": 5,
                  "out_bytes": 10, "result": "ok"}
        self.assertEqual(P.project(lines(OLD), NOW)["receipts"][0]["receipt_sha256"], P._digest(record))

    def test_a_voice_outside_the_slug_or_none_is_dropped(self):
        for bad in ("None", "../x", "", "a" * 30, "none"):
            self.assertNotIn("voice", P.project(lines(dict(OLD, voz=bad)), NOW)["receipts"][0], bad)


class Reader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_reader_accepts_voice_and_refusal_and_rejects_a_changed_voice(self):
        P.write(self.root, P.project(lines(ACTED, REFUSED), NOW))
        rows = notebook_read.read(self.root, now=NOW)["receipts"]
        self.assertEqual([(r["voice"], r["result"]) for r in rows], [("hexelion", "ok"), ("hexelion", "refused")])
        path = self.root / "notebook" / "receipts.json"
        data = json.loads(path.read_text())
        data["receipts"][0]["voice"] = "claude"
        path.write_text(json.dumps(data))
        self.assertEqual(notebook_read.read(self.root, now=NOW)["receipts_cause"], "receipt_fingerprint_mismatch")

    def test_opening_the_notebook_renews_the_projection_from_the_servers_log(self):
        mcp = self.root / "mcp"
        mcp.mkdir()
        (mcp / "audit.jsonl").write_text("\n".join(lines(OLD)) + "\n")
        with mock.patch.dict(os.environ, {"PRECEPTOROS_MCP_HOME": str(mcp)}):
            P.refresh(self.root)
            self.assertEqual(len(notebook_read.read(self.root)["receipts"]), 1)
            with open(mcp / "audit.jsonl", "a") as f:
                f.write(json.dumps(dict(REFUSED, ts=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))) + "\n")
            self.assertEqual(P.refresh(self.root)[0], "DECLARED")
        rows = notebook_read.read(self.root)["receipts"]
        self.assertEqual((len(rows), rows[-1]["result"]), (2, "refused"))

    def test_a_missing_log_is_no_data_not_a_crash(self):
        with mock.patch.dict(os.environ, {"PRECEPTOROS_MCP_HOME": str(self.root / "absent")}):
            self.assertEqual(P.refresh(self.root)[0], "NO_DATA")


class Wiring(unittest.TestCase):
    def test_the_notebook_endpoint_refreshes_before_reading_and_the_rows_say_who_and_refused(self):
        src = (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        at = src.index('if ruta == "/api/notebook":')
        self.assertLess(src.index("_notebook_receipts.refresh(_casa.raiz())", at), src.index("_notebook_read.read(", at))
        js = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")
        self.assertIn('"refused by the fence"', js)
        self.assertIn("voice: clean(r.voice, 24)", js)
        sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
        self.assertIn('"/notebook.js?v=19"', sw)
        self.assertIn("preceptoros-armazon-v193", sw)


if __name__ == "__main__":
    unittest.main()
