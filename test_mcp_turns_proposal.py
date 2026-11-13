"""S5 proposal · synthetic tests only. What a read-only MCP `turns` tool would answer, if the Sovereign decides to add
it to the native server. Nothing here adds a tool, changes the server or its permissions."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import mcp_transport
import tareas_hexelion as K
import turnos_hexelion as T
from test_turnos_hexelion import msg

ROOT = Path(__file__).resolve().parent


def projection(*messages):
    return T.project({"estado": "MEDIDO", "mensajes": list(messages)}, "2026-11-13T12:00:00Z")


def line(summary):
    return mcp_transport._reply({"jsonrpc": "2.0", "id": 3, "result": {"content": [
        {"type": "text", "text": json.dumps(summary, ensure_ascii=False, separators=(",", ":"), sort_keys=True)}]}})


class Proposal(unittest.TestCase):
    def test_the_machine_reads_the_same_last_turn_as_talk_and_the_notebook(self):
        p = projection(msg(1, "soberano", "q"), msg(2, "hexelion-door", "x", pregunta_n=1, causa="station_unavailable"))
        s = T.mcp_summary(p, K.project(None, "t", source_cause="p2_mirror_not_built"))
        self.assertEqual(s["last"], {k: p["turns"][0].get(k) for k in ("n", "state", "cause", "sentence")})
        self.assertEqual(s["tasks"]["cause"], "p2_mirror_not_built")
        self.assertIn(b"preceptoros.hexelion-status/1", line(s))

    def test_the_worst_case_still_fits_one_mcp_line(self):
        long_cause = "ñ" * 80
        p = projection(msg(1, "soberano", "é" * 600), msg(2, "hexelion-door", "x", pregunta_n=1, causa=long_cause))
        p["counts"] = {s: 12 for s in T.NEXT}
        s = T.mcp_summary(p, K.project([], "t"))
        encoded = line(s)
        self.assertLess(len(encoded), mcp_transport.LIMIT)
        self.assertIn(b"preceptoros.hexelion-status/1", encoded)       # never replaced by the ceiling error

    def test_it_gives_way_rather_than_grow(self):
        p = projection(msg(1, "soberano", "q"), msg(2, "hexelion-door", "x", pregunta_n=1, causa="station_unavailable"))
        p["turns"][0]["sentence"] = "€" * 300
        s = T.mcp_summary(p)
        self.assertEqual((s["last"].get("sentence_cut"), "sentence" in s["last"]), ("mcp_line", False))
        p["counts"] = {"X" * 60 + str(i): i for i in range(30)}
        self.assertEqual(T.mcp_summary(p)["cause"], "summary_exceeds_mcp_line")

    def test_malformed_inputs_are_no_data(self):
        for bad in (None, {}, {"schema": "other"}, "turns"):
            self.assertEqual(T.mcp_summary(bad), {"schema": T.STATUS_SCHEMA, "state": "NO_DATA",
                                                  "cause": "turns_projection_invalid"})
        self.assertEqual(T.mcp_summary(projection())["last"], None)
        self.assertEqual(T.mcp_summary(projection(msg(1, "soberano")))["tasks"]["cause"], "tasks_projection_missing")

    def test_it_is_a_reading_and_nothing_is_wired(self):
        s = json.dumps(T.mcp_summary(projection(msg(1, "soberano")))).lower()
        for word in ("command", "write", "exec", "grant", "allowlist"):
            self.assertNotIn(word, s)
        pwa = (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        self.assertNotIn("mcp_summary", pwa)                             # not served, not called


if __name__ == "__main__":
    unittest.main()
