"""No zero is tranquillity unless a complete reading was attested (APP-P0-TRUTH, Mesa #3, 2026-11-13).

`tareas_hexelion.project` used to serialise `needs_you=0, blocks_new_work=0, decisions_for_you=0` whatever it read:
an absent source, an unreadable list, an empty reading nobody attested, a window that cut tasks off, rows it could not
read, uncertain rows whose projection it could not use, and an acknowledgement whose authority is unverified. Each of
those zeros says "nothing needs you" without evidence. Talk then kept quiet, which says the same thing to the ear.

Rule: a counter is a number only where it was observed. A positive count is what was seen (at least that many); a
zero is said only when `counters.state` is MEASURED, which needs the host's completeness witness for the reading and
every row read. Otherwise the zero is null and `counters` carries NO_DATA with its cause, the same in the JSON, the
MCP summary, the Notebook status (the reader text) and Talk. The live route stays NO_DATA(p2_mirror_not_built).

Every class failed on main 60064d7 before this change, except where its docstring says it pins an existing guard.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import tareas_hexelion as K
import turnos_hexelion as T
from test_host_truth import STAMP, packet, unknown_record
from test_talk_turn_parity import node
from test_tareas_hexelion import PWA, rec, receipt, runs

ROOT = Path(__file__).resolve().parent
WITNESS = "c" * 64          # synthetic: a completeness witness of the host's reading (no host provides one yet)
COUNTERS = ("needs_you", "blocks_new_work", "decisions_for_you")
# Words that tell a person nothing needs them. Said only over a MEASURED zero.
CLEAR = re.compile(r"\bnothing (else )?(needs|waits|requires)|\bno (task|decision)s? (needs|waits|for you)|all clear"
                   r"|\bno task recorded\b", re.I)


def unreadable_row():
    return {"run_id": "run-9", "task_sha256": "0" * 64, "receipt": "not a receipt"}


def fixtures():
    """name -> projection. Each is a reading in which "zero" was never observed."""
    return {
        "source_absent": K.project(None, STAMP, source_cause="p2_mirror_not_built"),
        "journal_file_missing": K.project(None, STAMP, source_cause="journal_file_missing"),
        "records_unreadable": K.project("not a list", STAMP),
        "empty_unattested": K.project([], STAMP),
        "known_done_unattested": K.project(runs(rec(receipt())), STAMP),
        "unknown_projection_stale": K.project([unknown_record(packet("unknown_hitl_required"))], "2026-11-13T12:00:00Z"),
        "authority_revoked": K.project([unknown_record(packet("synthetic_ack_not_verified"))], STAMP),
        "row_unreadable": K.project(runs(rec(receipt())) + [unreadable_row()], STAMP, complete_ref=WITNESS),
        "beyond_window": K.project(runs(*[rec(receipt())] * (K.MAX_TASKS + 1)), STAMP, complete_ref=WITNESS),
        "witness_not_a_ref": K.project(runs(rec(receipt())), STAMP, complete_ref="trust me"),
    }


class TheMachineNeverSerialisesAnUnobservedZero(unittest.TestCase):
    def test_no_fixture_carries_a_zero_without_a_measured_reading(self):
        for name, p in fixtures().items():
            self.assertEqual(p["counters"]["state"], "NO_DATA", name)
            self.assertRegex(p["counters"]["cause"], r"^[a-z][a-z0-9_]+$", name)
            for k in COUNTERS:
                self.assertNotEqual(p[k], 0, "%s: %s=0 is a false clear" % (name, k))

    def test_each_reading_names_why_it_cannot_count(self):
        f = fixtures()
        for name, cause in (("source_absent", "p2_mirror_not_built"), ("journal_file_missing", "journal_file_missing"),
                            ("records_unreadable", "records_unreadable"), ("empty_unattested", "completeness_not_attested"),
                            ("known_done_unattested", "completeness_not_attested"),
                            ("unknown_projection_stale", "uncertainty_unread"), ("row_unreadable", "rows_unreadable"),
                            ("beyond_window", "records_beyond_window"), ("witness_not_a_ref", "completeness_not_attested")):
            self.assertEqual(f[name]["counters"]["cause"], cause, name)

    def test_what_was_seen_is_still_said_as_at_least(self):
        f = fixtures()
        self.assertEqual(f["unknown_projection_stale"]["blocks_new_work"], 1)       # a known block is never cleared
        self.assertIsNone(f["unknown_projection_stale"]["decisions_for_you"])       # the decision is unknown, not 0
        self.assertEqual(f["unknown_projection_stale"]["counters"]["known_counts_are"], "at_least")

    def test_an_unverified_acknowledgement_is_a_decision_still_yours(self):
        p = fixtures()["authority_revoked"]
        self.assertEqual(p["tasks"][0]["uncertainty"]["acknowledgement"], "AUTHORITY_NOT_VERIFIED")
        self.assertEqual((p["decisions_for_you"], p["blocks_new_work"]), (1, 1))

    def test_the_live_route_says_its_cause_and_no_zero(self):
        h = PWA.PWA.__new__(PWA.PWA)
        h.path, h.client_address, out = "/api/hexelion/tareas", ("127.0.0.1", 1), {}
        h._json = lambda code, body: out.update(code=code, body=body)
        PWA.PWA._tareas_leer(h)
        b = out["body"]
        self.assertEqual((b["state"], b["cause"], b["counters"]["cause"]), ("NO_DATA", "p2_mirror_not_built", "p2_mirror_not_built"))
        self.assertEqual([b[k] for k in COUNTERS], [None, None, None])

    def test_the_mcp_line_carries_the_same_cause_and_no_zero(self):
        for name, p in fixtures().items():
            s = T.mcp_summary({"schema": T.SCHEMA, "state": "NO_DATA", "cause": "x", "turns": []}, p)["tasks"]
            self.assertEqual(s["counters"], p["counters"], name)
            self.assertNotEqual(s["needs_you"], 0, name)
            self.assertNotEqual(s["blocks_new_work"], 0, name)


class AMeasuredZeroIsStillSaid(unittest.TestCase):
    """The positive case: an attested, complete, fully read reading may say zero."""

    def test_a_witnessed_complete_reading_counts_zero(self):
        for records in ([], runs(rec(receipt()))):
            p = K.project(records, STAMP, complete_ref=WITNESS)
            self.assertEqual(p["counters"], {"state": "MEASURED", "cause": None, "complete_ref": WITNESS,
                                             "known_counts_are": "exact"})
            self.assertEqual([p[k] for k in COUNTERS], [0, 0, 0])
        self.assertEqual(K.project([], STAMP, complete_ref=WITNESS)["state"], "MEASURED")

    def test_a_witness_never_turns_a_no_data_source_into_a_measurement(self):
        p = K.project(None, STAMP, source_cause="journal_file_missing", complete_ref=WITNESS)
        self.assertEqual((p["counters"]["state"], p["needs_you"]), ("NO_DATA", None))


CLIENT = """
const els = {}; const mk = () => ({ textContent: '', hidden: false, dataset: {}, children: [], className: '',
  append(...c) { this.children.push(...c); }, replaceChildren() { this.children = []; } });
for (const id of ['notebook-tasks', 'notebook-tasks-status', 'talk-tasks']) els[id] = mk();
global.document = { createElement: mk, getElementById: (id) => els[id] || null };
const N = require('./interface/notebook.js');
(async () => { const out = {};
  for (const [name, raw] of Object.entries(RAWS)) {
    global.fetch = async () => ({ ok: true, json: async () => raw });
    await N.loadTasks('notebook-tasks', 'notebook-tasks-status'); await N.talkTasks('talk-tasks');
    out[name] = { status: els['notebook-tasks-status'].textContent, talk: els['talk-tasks'].textContent,
                  talkHidden: els['talk-tasks'].hidden };
  }
  global.fetch = async () => { throw new Error('connection reset'); };
  await N.loadTasks('notebook-tasks', 'notebook-tasks-status'); await N.talkTasks('talk-tasks');
  out.lost = { status: els['notebook-tasks-status'].textContent, talk: els['talk-tasks'].textContent,
               talkHidden: els['talk-tasks'].hidden };
  console.log(JSON.stringify(out)); })();
"""


def told(raws):
    return node("const RAWS=%s;%s" % (json.dumps(raws), CLIENT))


class TheEyeAndTheEarHearTheSameCause(unittest.TestCase):
    """Notebook status (the reader text) and Talk say the cause; silence is kept for a measured zero only."""

    @classmethod
    def setUpClass(cls):
        cls.raws = fixtures()
        old = dict(cls.raws["known_done_unattested"])
        old.pop("counters")                                       # a server from before this contract
        for k in COUNTERS:
            old[k] = 0
        cls.raws["old_server_zeros"] = old
        cls.raws["measured_zero"] = K.project(runs(rec(receipt())), STAMP, complete_ref=WITNESS)
        cls.out = told(cls.raws)

    def test_zero_false_clears_across_every_fixture(self):
        false_clear = []
        for name, o in self.out.items():
            if name == "measured_zero":
                continue
            if o["talkHidden"] or not o["talk"]:
                false_clear.append((name, "talk silent"))
            for where in ("status", "talk"):
                if CLEAR.search(o[where]):
                    false_clear.append((name, where, o[where]))
        self.assertEqual(false_clear, [])

    def test_the_cause_is_one_string_on_every_surface(self):
        for name, p in self.raws.items():
            if name in ("measured_zero", "old_server_zeros"):
                continue
            words = p["counters"]["cause"].replace("_", " ")
            self.assertIn(words, self.out[name]["status"], name)
            self.assertIn(words, self.out[name]["talk"], name)
        self.assertIn("counters not stated", self.out["old_server_zeros"]["talk"])

    def test_a_lost_reading_is_told_in_talk_too(self):
        o = self.out["lost"]
        self.assertFalse(o["talkHidden"])
        self.assertTrue(o["talk"].startswith("NO_DATA") and "did not answer" in o["talk"], o)

    def test_only_a_measured_zero_lets_talk_be_quiet(self):
        o = self.out["measured_zero"]
        self.assertTrue(o["talkHidden"])
        self.assertIn("Measured: no task needs you", o["status"])


class AnOlderReadingNeverRepaintsANewerOne(unittest.TestCase):
    """Found by the walk: a reading started before a newer one, answering after it, repainted Talk with old words."""

    SCRIPT = """
const els = {}; const mk = () => ({ textContent: '', hidden: false, dataset: {}, children: [], className: '',
  append(...c) { this.children.push(...c); }, replaceChildren() { this.children = []; } });
for (const id of ['notebook-tasks', 'notebook-tasks-status', 'talk-tasks']) els[id] = mk();
global.document = { createElement: mk, getElementById: (id) => els[id] || null };
const N = require('./interface/notebook.js');
let release; const slow = new Promise((r) => { release = r; });
(async () => {
  global.fetch = async () => { await slow; return { ok: true, json: async () => OLD }; };
  const first = [N.talkTasks('talk-tasks'), N.loadTasks('notebook-tasks', 'notebook-tasks-status')];
  global.fetch = async () => ({ ok: true, json: async () => NEW });
  await N.talkTasks('talk-tasks'); await N.loadTasks('notebook-tasks', 'notebook-tasks-status');
  release(); await Promise.all(first);
  console.log(JSON.stringify({ talk: els['talk-tasks'].textContent, status: els['notebook-tasks-status'].textContent,
                               rows: els['notebook-tasks'].children.length }));
})();
"""

    def test_the_newer_reading_stays(self):
        old = K.project(None, STAMP, source_cause="p2_mirror_not_built")
        new = K.project([unknown_record(packet("unknown_hitl_required"))], STAMP)
        out = node("const OLD=%s,NEW=%s;%s" % (json.dumps(old), json.dumps(new), self.SCRIPT))
        self.assertTrue(out["talk"].startswith("New tasks wait"), out)
        self.assertEqual((out["status"], out["rows"]), (out["talk"], 1))


class SignaturesNeverClearFromAnOldList(unittest.TestCase):
    """The same rule for «what awaits my signature?»: a stale or partly unreadable list never says nothing waits."""

    def setUp(self):
        import tempfile
        import hexelion_acciones as A
        self.A, self.tmp = A, tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def line(self, medido, filas, age):
        from unittest import mock
        d = Path(self.tmp.name) / "firmas"
        d.mkdir(exist_ok=True)
        (d / "pendientes.json").write_text(json.dumps({"esquema": "preceptoros.firmas-pendientes/1",
                                                       "medido": medido, "filas": filas}))
        with mock.patch.object(self.A, "_edad", lambda s, now: age):
            return self.A._firmas(self.tmp.name, None)

    def test_a_stale_empty_list_does_not_say_nothing_waits(self):
        ok, cause, text = self.line("2026-11-12T09:00:00Z", [], 86400.0)
        self.assertEqual((ok, cause), (False, "signatures_stale"))
        self.assertTrue(text.startswith("STALE: "))
        self.assertNotRegex(text, CLEAR)

    def test_an_unreadable_row_means_the_list_cannot_clear(self):
        ok, cause, text = self.line("2026-11-13T09:25:00Z", ["not a row"], 300.0)
        self.assertEqual((ok, cause), (False, "signatures_rows_unreadable"))
        self.assertNotRegex(text, CLEAR)

    def test_a_fresh_complete_empty_list_still_says_so(self):
        ok, cause, text = self.line("2026-11-13T09:25:00Z", [], 300.0)
        self.assertEqual((ok, cause), (True, None))
        self.assertIn("Nothing waits for your signature now.", text)        # pins the measured clear


if __name__ == "__main__":
    unittest.main()
