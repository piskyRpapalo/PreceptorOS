"""Uncertain task, told everywhere from one record (LAB #188, UNCERTAINTY-PROJECTION-01) · presentation only.

The host projects an uncertain claim as `preceptoros.lab.uncertainty-ack/1` with kind=projection. The fixture here is
built field for field like `meta_harness.uncertainty_views.project` and hashed with LAB's canonical encoding. The JSON
row, the Notebook card and status, Talk's line and the Acho cue must all carry its `summary` and `projection_ref`:
UNKNOWN, the acknowledgement word the host reported, the reservation (retained or NO_DATA with cause), no retry, no
memory promotion, TTL 0. None may present approval it cannot see, and no control may acknowledge or authorise.
The live route stays NO_DATA(p2_mirror_not_built): nothing here is connected to the journal.
"""
from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

import audio_feedback as AF
import tareas_hexelion as K
from test_p2_mirror_contract import told
from test_talk_turn_parity import node
from test_tareas_hexelion import PWA, rec, receipt

ROOT = Path(__file__).resolve().parent
TASK = hashlib.sha256(b"task").hexdigest()
TEXT = {"HITL_REQUIRED": "Outcome unknown; human review and a worker fence are required.",
        "HUMAN_ACKNOWLEDGED": "Outcome unknown; human acknowledgement and worker fence are witnessed.",
        "AUTHORITY_NOT_VERIFIED": "Outcome unknown; acknowledgement or worker fence cannot be verified."}


def lab_encode(data):          # LAB bin/dfa06_evidence_bundle.encode, byte for byte
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def projection(ack="HITL_REQUIRED", tokens=64, rehash=True, **over):
    reservation = {"state": "RETAINED", "tokens": tokens} if tokens is not None else \
        {"state": "NO_DATA", "cause": "durable_budget_not_configured"}
    summary = TEXT[ack] + (" Token reservation is retained." if tokens is not None else " Token reservation is unknown.")
    r = {"schema": "preceptoros.lab.uncertainty-ack/1", "kind": "projection", "state": "UNKNOWN",
         "cause": "execution_outcome_unknown", "acknowledgement": ack, "observed_at": "2026-11-13T12:00:00Z",
         "journal_id": "a" * 32, "task_ref": TASK,
         "resolution_ref": hashlib.sha256(b"res").hexdigest() if ack == "HUMAN_ACKNOWLEDGED" else None,
         "reservation": reservation, "ttl_seconds": 0, "no_retry": True, "promotion": "NOT_AUTHORIZED",
         "summary": summary}
    r.update(over)
    r["projection_ref"] = hashlib.sha256(lab_encode({k: v for k, v in r.items() if k != "projection_ref"})).hexdigest()
    if not rehash:
        r["projection_ref"] = "0" * 64
    return r


def event(prop=None, unknown_receipt=True, run_id="run-7"):
    r = rec(receipt("failed", "UNKNOWN", "UNKNOWN", "NO_DATA", None, run_id=run_id, task_sha256=TASK)
            if unknown_receipt else None)
    r.update(run_id=run_id, task_sha256=TASK)
    if prop is not None:
        r["uncertainty"] = prop
    return r


DOM = """
const els = {};
const mk = (tag) => ({ tag, className: '', textContent: '', hidden: false, dataset: {}, children: [],
  append(...c) { this.children.push(...c); }, replaceChildren() { this.children = []; } });
for (const id of ['notebook-tasks', 'notebook-tasks-status', 'talk-tasks']) els[id] = mk('div');
global.document = { createElement: mk, getElementById: (id) => els[id] || null };
global.fetch = async () => ({ ok: true, json: async () => RAW });
const text = (n) => [n.textContent, ...n.children.map(text)].join(' ');
const tags = (n) => [n.tag, ...n.children.flatMap(tags)];
"""


def surfaces(raw):
    script = ("const RAW=%s;const N=require('./interface/notebook.js');%s(async()=>{"
              "const p=await N.loadTasks('notebook-tasks','notebook-tasks-status');await N.talkTasks('talk-tasks');"
              "const c=els['notebook-tasks'].children[0];"
              "console.log(JSON.stringify({card:text(c),tags:tags(c),state:c.dataset.state,acho:c.dataset.acho,"
              "status:els['notebook-tasks-status'].textContent,talk:els['talk-tasks'].textContent,"
              "talkHidden:els['talk-tasks'].hidden,parsed:p.tasks[0].uncertainty}))})()") % (json.dumps(raw), DOM)
    return node(script)


class OneRecordEverywhere(unittest.TestCase):
    def setUp(self):
        self.p = projection()
        self.raw = told(event(self.p))
        self.t = self.raw["tasks"][0]

    def test_the_row_carries_the_hosts_record_by_its_ref(self):
        t = self.t
        self.assertEqual((t["state"], t["sentence"]), ("OUTCOME_UNKNOWN", self.p["summary"]))
        self.assertEqual(t["uncertainty"], {"projection_ref": self.p["projection_ref"], "task_ref": TASK,
                                            "acknowledgement": "HITL_REQUIRED",
                                            "reservation": {"state": "RETAINED", "tokens": 64},
                                            "observed_at": "2026-11-13T12:00:00Z"})
        self.assertEqual(self.raw["uncertainty_terms"], {"ttl_seconds": 0, "no_retry": True,
                                                         "promotion": "NOT_AUTHORIZED"})
        self.assertIn(self.p["projection_ref"][:12], t["next"])
        self.assertEqual((self.raw["blocks_new_work"], self.raw["decisions_for_you"]), (1, 1))

    def test_every_row_keeps_the_1024_byte_row_budget(self):
        """Budgets kept apart: the host record < 1,024 B (LAB), the row < 1,024 B (here), MCP line < 1,024 B
        (mcp_transport), chat envelope 1,023 B (estado_compacto). Worst case: 32-char run id, longest wording."""
        worst = 0
        for ack in TEXT:
            for tokens in (512, None):
                for receipt_present in (True, False):
                    row = told(event(projection(ack, tokens), receipt_present, run_id="r" + "x" * 31))["tasks"][0]
                    self.assertIn("uncertainty", row)
                    worst = max(worst, len(json.dumps(row, ensure_ascii=False).encode("utf-8")))
        self.assertLess(worst, 1024)
        self.assertEqual(K.MAX_TASK_B, 1024)

    def test_notebook_talk_acho_and_json_say_the_same(self):
        t, got = self.t, surfaces(self.raw)
        words = t["sentence"] + " " + t["next"]
        self.assertEqual(got["parsed"]["projection"], self.p["projection_ref"])
        self.assertEqual((got["state"], got["acho"]), ("OUTCOME_UNKNOWN", "needs_you"))
        self.assertIn("details", got["tags"])                      # full refs one disclosure away
        for fact in (self.p["projection_ref"], TASK, "HITL_REQUIRED", "Retained: 64 tokens.", "Not authorized.",
                     "valid for this reading only", self.p["summary"]):
            self.assertIn(fact, got["card"])
        self.assertIn(words, got["status"])
        self.assertEqual(got["talk"], got["status"])
        self.assertTrue(got["talk"].startswith("New tasks wait"))
        cue = AF.cue_for_turn(t)
        self.assertEqual((cue["clase"], cue["texto"], cue["sonido"]), ("needs_you", t["reader"], "INACTIVO"))
        self.assertIn(self.p["summary"], cue["texto"])

    def test_each_acknowledgement_is_said_as_the_host_said_it(self):
        for ack, acho in (("HUMAN_ACKNOWLEDGED", "empty"), ("AUTHORITY_NOT_VERIFIED", "fence")):
            raw = told(event(projection(ack)))
            t = raw["tasks"][0]
            self.assertEqual((t["sentence"], t["acho"]["class"], raw["decisions_for_you"], raw["blocks_new_work"]),
                             (TEXT[ack] + " Token reservation is retained.", acho, 0, 1))
            got = surfaces(raw)
            self.assertIn("Uncertain task", got["talk"])
            self.assertNotIn("Decision for you", got["talk"])
        self.assertIn("never cached", told(event(projection("HUMAN_ACKNOWLEDGED")))["tasks"][0]["next"])
        self.assertIn("not approved", told(event(projection("AUTHORITY_NOT_VERIFIED")))["tasks"][0]["next"])

    def test_no_surface_presents_an_approval_or_a_refund(self):
        claims = re.compile(r"\b(approved|authori[sz]ed by|refunded|released|returned|signed|succeeded)\b", re.I)
        for ack in TEXT:
            raw = told(event(projection(ack)))
            got, t = surfaces(raw), raw["tasks"][0]
            for name, text in (("card", got["card"]), ("talk", got["talk"]), ("reader", t["reader"])):
                self.assertIsNone(claims.search(text.replace("not approved", "")), (ack, name))

    def test_no_control_acknowledges_or_authorises(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        js = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")
        for button in re.findall(r"<button[^>]*>[^<]*</button>", html):
            self.assertIsNone(re.search(r"acknowledg|authori[sz]|\bACK\b|retain", button, re.I), button)
        self.assertNotIn('elem("button"', js)
        self.assertNotIn('method: "POST"', js)
        self.assertNotIn("acknowledge", (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8").lower())

    def test_the_live_app_is_still_not_connected(self):
        h = PWA.PWA.__new__(PWA.PWA)
        h.path, h.client_address, out = "/api/hexelion/tareas", ("127.0.0.1", 1), {}
        h._json = lambda code, body: out.update(code=code, body=body)
        PWA.PWA._tareas_leer(h)
        self.assertEqual((out["body"]["cause"], out["body"]["decisions_for_you"]), ("p2_mirror_not_built", 0))


class ProjectionNegatives(unittest.TestCase):
    def cause(self, record):
        t = told(record)["tasks"][0]
        self.assertNotIn("uncertainty", t)
        return t["state"], t["cause"]

    def test_a_record_that_does_not_match_its_ref_is_not_shown(self):
        self.assertEqual(self.cause(event(projection(rehash=False))), ("NO_DATA", "uncertainty_ref_mismatch"))
        tampered = projection()
        tampered["acknowledgement"] = "HUMAN_ACKNOWLEDGED"              # promoted without re-hashing
        self.assertEqual(self.cause(event(tampered)), ("NO_DATA", "uncertainty_ref_mismatch"))

    def test_changed_terms_are_refused_even_when_rehashed(self):
        for over in ({"no_retry": False}, {"promotion": "AUTHORIZED"}, {"ttl_seconds": 60},
                     {"acknowledgement": "APPROVED"}, {"reservation": {"state": "RELEASED", "tokens": 0}},
                     {"reservation": {"state": "RETAINED", "tokens": 9999}}, {"summary": ""}):
            self.assertEqual(self.cause(event(projection(**over))), ("NO_DATA", "uncertainty_terms_changed"), over)

    def test_other_shapes_are_refused(self):
        self.assertEqual(self.cause(event(projection(task_ref="f" * 64))), ("NO_DATA", "uncertainty_for_another_task"))
        self.assertEqual(self.cause(event(projection(state="NO_DATA"))), ("NO_DATA", "uncertainty_unavailable_on_host"))
        self.assertEqual(self.cause(event(projection(kind="ack"))), ("NO_DATA", "uncertainty_fields_unknown"))
        self.assertEqual(self.cause(event(dict(projection(), signed=True))), ("NO_DATA", "uncertainty_fields_unknown"))
        self.assertEqual(self.cause(event(projection(summary="é" * 200, cause="x" * 700))),
                         ("NO_DATA", "uncertainty_exceeds_1024_bytes"))
        self.assertEqual(self.cause(dict(event(projection()), acknowledged=True)), ("NO_DATA", "record_fields_unknown"))

    def test_a_projection_never_rides_a_known_outcome(self):
        known = rec(receipt(run_id="run-7", task_sha256=TASK))
        known.update(run_id="run-7", task_sha256=TASK, uncertainty=projection())
        self.assertEqual(self.cause(known), ("NO_DATA", "uncertainty_on_a_known_outcome"))

    def test_without_a_projection_it_stays_uncertain(self):
        p = told(event())
        t = p["tasks"][0]
        self.assertEqual((t["state"], t["acho"]["class"], p["decisions_for_you"], p["blocks_new_work"]),
                         ("OUTCOME_UNKNOWN", "empty", 0, 1))

    def test_a_claim_with_no_receipt_can_carry_it(self):
        t = told(event(projection(), unknown_receipt=False))["tasks"][0]
        self.assertEqual(t["state"], "NO_RESULT_RECORDED")
        self.assertIn("uncertainty", t)

    def test_the_notebook_hides_tampered_details_but_keeps_the_words(self):
        raw = told(event(projection()))
        raw["uncertainty_terms"]["promotion"] = "AUTHORIZED"
        got = surfaces(raw)
        self.assertIsNone(got["parsed"])
        self.assertNotIn("details", got["tags"])
        self.assertIn("Outcome unknown", got["card"])


if __name__ == "__main__":
    unittest.main()
