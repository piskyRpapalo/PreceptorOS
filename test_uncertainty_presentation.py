"""Uncertain task, told everywhere the same way (HUMAN-UNCERTAINTY-01, LAB #186) · presentation only, synthetic.

One fixture event: a run whose outcome is UNKNOWN, with the journal's read-only proposal
(`preceptoros.lab.uncertainty-ack/1`, the shape prepare_unknown_ack returns). The JSON row, the Notebook card and
status line, Talk's line and the Acho cue must carry the same facts: UNKNOWN, the exact task ref, the evidence and
proposal refs, budget still reserved, no retry, and that the next decision is the Sovereign's. None may say the
proposal was signed, the budget was returned or the old worker was stopped, and no control may acknowledge or
authorise. The live route stays NO_DATA(p2_mirror_not_built): nothing here is connected to the journal.
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
TASK, PRIOR, EVIDENCE, AUTHORITY, PROPOSAL = (hashlib.sha256(w.encode()).hexdigest()
                                              for w in ("task", "prior", "evidence", "authority", "proposal"))


def proposal(**over):
    p = {"schema": K.UNCERTAINTY_SCHEMA, "journal_id": "a" * 32, "run_id": "run-7", "task_ref": TASK,
         "prior_ref": PRIOR, "evidence_ref": EVIDENCE, "authority_ref": AUTHORITY,
         "observed_at": "2026-11-13T12:00:00Z", "decision": K.DECISION, "no_retry": True,
         "reservation_release": False, "resolution_ref": PROPOSAL}
    p.update(over)
    return p


def event(prop=None, unknown_receipt=True):
    r = rec(receipt("failed", "UNKNOWN", "UNKNOWN", "NO_DATA", None, run_id="run-7", task_sha256=TASK)
            if unknown_receipt else None)
    r.update(run_id="run-7", task_sha256=TASK)
    if prop is not None:
        r["uncertainty"] = prop
    return r


# Node fake DOM: enough for notebook.js to paint cards and status lines, and a fetch that serves `raw`.
DOM = """
const els = {};
const mk = (tag) => ({ tag, className: '', textContent: '', hidden: false, dataset: {}, children: [],
  append(...c) { this.children.push(...c); }, replaceChildren() { this.children = []; } });
for (const id of ['notebook-tasks', 'notebook-tasks-status', 'talk-tasks']) els[id] = mk('div');
global.document = { createElement: mk, getElementById: (id) => els[id] || null };
global.fetch = async () => ({ ok: true, json: async () => RAW });
const text = (n) => [n.textContent, ...n.children.map(text)].join(' ');
"""


def surfaces(raw):
    script = ("const RAW=%s;const N=require('./interface/notebook.js');%s(async()=>{"
              "const p=await N.loadTasks('notebook-tasks','notebook-tasks-status');await N.talkTasks('talk-tasks');"
              "const c=els['notebook-tasks'].children[0];"
              "console.log(JSON.stringify({card:text(c),state:c.dataset.state,acho:c.dataset.acho,"
              "status:els['notebook-tasks-status'].textContent,talk:els['talk-tasks'].textContent,"
              "talkHidden:els['talk-tasks'].hidden,parsed:p.tasks[0].uncertainty}))})()") % (json.dumps(raw), DOM)
    return node(script)


class OneUncertainEvent(unittest.TestCase):
    def setUp(self):
        self.raw = told(event(proposal()))
        self.t = self.raw["tasks"][0]

    def test_json_carries_every_fact_and_claims_nothing_unseen(self):
        t = self.t
        self.assertEqual((t["state"], t["cause"]), ("OUTCOME_UNKNOWN", "unknown"))
        self.assertEqual(t["uncertainty"], {"task_ref": TASK, "evidence_ref": EVIDENCE, "proposal_ref": PROPOSAL,
                                            "budget": "reserved", "retry": "none", "decides": "sovereign",
                                            "not_visible": ["signature", "budget_return", "worker_stop"]})
        self.assertNotIn(AUTHORITY, json.dumps(t))       # a host identifier for a decision, not a signature to show
        self.assertEqual((self.raw["blocks_new_work"], self.raw["decisions_for_you"], self.raw["needs_you"]), (1, 1, 0))
        self.assertLess(len(json.dumps(t, ensure_ascii=False).encode("utf-8")), K.MAX_TASK_B)

    def test_notebook_talk_acho_and_json_say_the_same(self):
        t, got = self.t, surfaces(self.raw)
        words = t["sentence"] + " " + t["next"]
        self.assertEqual(got["parsed"], {"task": TASK, "evidence": EVIDENCE, "proposal": PROPOSAL})
        self.assertEqual((got["state"], got["acho"]), ("OUTCOME_UNKNOWN", "needs_you"))
        for ref in (TASK, EVIDENCE, PROPOSAL):
            self.assertIn(ref, got["card"])
        for fact in ("Still reserved.", "None: it will not run again.", "You, outside this app.", t["sentence"],
                     t["next"], "OUTCOME_UNKNOWN"):
            self.assertIn(fact, got["card"])
        self.assertIn(words, got["status"])
        self.assertEqual(got["talk"], got["status"])     # Talk's line is the Notebook's status, word for word
        self.assertFalse(got["talkHidden"])
        cue = AF.cue_for_turn(t)
        self.assertEqual((cue["clase"], cue["texto"], cue["sonido"]), ("needs_you", t["reader"], "INACTIVO"))
        self.assertIn(words, cue["texto"])
        for short in (PROPOSAL[:12], EVIDENCE[:12]):        # the ear gets the refs the eye can match
            self.assertIn(short, t["reader"])
        self.assertNotEqual(PROPOSAL[:12], EVIDENCE[:12])

    def test_no_surface_pretends_a_signature_a_refund_or_a_stopped_worker(self):
        got = surfaces(self.raw)
        claims = re.compile(r"\b(signed|approved|authori[sz]ed|refunded|released|returned|was stopped|is stopped|"
                            r"has stopped|fenced|acknowledged)\b", re.I)
        for name, text in (("json", json.dumps(self.t)), ("card", got["card"]), ("status", got["status"]),
                           ("talk", got["talk"]), ("reader", self.t["reader"])):
            self.assertIsNone(claims.search(text.replace("not_visible", "")), name)
        self.assertIn("NO_DATA until the host shows them", got["card"])

    def test_no_control_acknowledges_or_authorises(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        js = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")
        for button in re.findall(r"<button[^>]*>[^<]*</button>", html):
            self.assertIsNone(re.search(r"acknowledg|authori[sz]|\bACK\b|retain", button, re.I), button)
        self.assertNotIn('elem("button"', js)
        self.assertNotIn("method: \"POST\"", js)
        self.assertNotIn("acknowledge", (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8").lower())

    def test_the_live_app_is_still_not_connected(self):
        h = PWA.PWA.__new__(PWA.PWA)
        h.path, h.client_address, out = "/api/hexelion/tareas", ("127.0.0.1", 1), {}
        h._json = lambda code, body: out.update(code=code, body=body)
        PWA.PWA._tareas_leer(h)
        self.assertEqual((out["body"]["cause"], out["body"]["decisions_for_you"]), ("p2_mirror_not_built", 0))


class ProposalNegatives(unittest.TestCase):
    def cause(self, record):
        t = told(record)["tasks"][0]
        self.assertNotIn("uncertainty", t)
        return t["state"], t["cause"]

    def test_changed_terms_are_not_shown_as_a_proposal(self):
        for over, cause in (({"reservation_release": True}, "uncertainty_terms_changed"),
                            ({"no_retry": False}, "uncertainty_terms_changed"),
                            ({"decision": "ACK_UNKNOWN_RELEASE"}, "uncertainty_terms_changed"),
                            ({"evidence_ref": "e" * 63}, "uncertainty_terms_changed"),
                            ({"resolution_ref": None}, "uncertainty_terms_changed"),
                            ({"task_ref": "f" * 64}, "uncertainty_for_another_task"),
                            ({"run_id": "run-8"}, "uncertainty_for_another_task"),
                            ({"schema": "preceptoros.lab.uncertainty-ack/2"}, "uncertainty_fields_unknown")):
            self.assertEqual(self.cause(event(proposal(**over))), ("NO_DATA", cause), over)

    def test_a_forged_signature_or_extra_field_is_refused(self):
        for extra in ({"signed": True}, {"approved_by": "sovereign"}, {"budget_returned": True},
                      {"worker_stopped": True}):
            self.assertEqual(self.cause(event(dict(proposal(), **extra))), ("NO_DATA", "uncertainty_fields_unknown"))
        self.assertEqual(self.cause(dict(event(proposal()), acknowledged=True)), ("NO_DATA", "record_fields_unknown"))

    def test_a_proposal_never_rides_a_known_outcome(self):
        known = rec(receipt(run_id="run-7", task_sha256=TASK))
        known.update(run_id="run-7", task_sha256=TASK, uncertainty=proposal())
        self.assertEqual(self.cause(known), ("NO_DATA", "uncertainty_on_a_known_outcome"))

    def test_without_a_proposal_it_stays_uncertain_and_the_host_must_prepare_one(self):
        p = told(event())
        t = p["tasks"][0]
        self.assertEqual((t["state"], t["acho"]["class"], p["decisions_for_you"], p["blocks_new_work"]),
                         ("OUTCOME_UNKNOWN", "empty", 0, 1))
        self.assertEqual(t["next"], K.NEXT["OUTCOME_UNKNOWN"])

    def test_a_claim_with_no_receipt_can_carry_the_proposal(self):
        t = told(event(proposal(), unknown_receipt=False))["tasks"][0]
        self.assertEqual((t["state"], t["uncertainty"]["proposal_ref"]), ("NO_RESULT_RECORDED", PROPOSAL))

    def test_the_notebook_hides_a_tampered_block_but_keeps_the_words(self):
        raw = told(event(proposal()))
        raw["tasks"][0]["uncertainty"]["budget"] = "returned"
        got = surfaces(raw)
        self.assertIsNone(got["parsed"])
        self.assertNotIn("Still reserved.", got["card"])
        self.assertIn("outcome is unknown", got["card"])


if __name__ == "__main__":
    unittest.main()
