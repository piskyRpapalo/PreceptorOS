"""Host truth · the P2 mirror's own packets, told without promotion (HOST-TRUTH-TO-APP, 2026-11-13).

Golden packets come from LAB's real producer (`meta_harness.readonly_mirror.ReadOnlyMirror.read`, LAB 51782ea) run on
temporary synthetic journals with a synthetic local-source witness (tests/fixtures/gen_p2_mirror_packets.py). APP has
no transport to the host mirror yet: the live route stays NO_DATA(p2_mirror_not_built) and nothing here connects it.

Each class is one adversarial case of the commission (numbered as there). Each failed on main b7937ce before this
change, except where the docstring says the guard already existed (then it pins that guard).
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import tareas_hexelion as K
from test_talk_turn_parity import node
from test_tareas_hexelion import PWA, rec, receipt

ROOT = Path(__file__).resolve().parent
GOLDEN = json.loads((ROOT / "tests/fixtures/p2_mirror_packets.json").read_text(encoding="utf-8"))
TASK = GOLDEN["task"]
STAMP = GOLDEN["provenance"]["stamp"]


def packet(name):
    return copy.deepcopy(GOLDEN["packets"][name])


def unknown_record(uncertainty, task_sha256=None):
    ref = task_sha256 or TASK["task_sha256"]
    r = rec(receipt("failed", "UNKNOWN", "UNKNOWN", "NO_DATA", None, run_id=TASK["run_id"], task_sha256=ref))
    r.update(run_id=TASK["run_id"], task_sha256=ref, uncertainty=uncertainty)
    return r


def told(uncertainty, read_at=STAMP, **kw):
    p = K.project([unknown_record(uncertainty, **kw)], read_at)
    return p, p["tasks"][0]


class Provenance(unittest.TestCase):
    def test_the_golden_packets_are_labs_own_and_synthetic(self):
        prov = GOLDEN["provenance"]
        self.assertEqual(prov["lab_commit"], "51782ea8490d5d76f47a0c02eb00b4f46d7b3d15")
        self.assertEqual(prov["producer"], "meta_harness.readonly_mirror.ReadOnlyMirror.read")
        self.assertEqual(prov["witness"], "SYNTHETIC (tests fixture)")
        self.assertNotRegex(json.dumps(GOLDEN), r"/(tmp|home)/")      # LAB returns no source paths

    def test_the_live_route_is_still_not_connected(self):
        h = PWA.PWA.__new__(PWA.PWA)
        h.path, h.client_address, out = "/api/hexelion/tareas", ("127.0.0.1", 1), {}
        h._json = lambda code, body: out.update(code=code, body=body)
        PWA.PWA._tareas_leer(h)
        self.assertEqual((out["body"]["state"], out["body"]["cause"], out["body"]["tasks"]),
                         ("NO_DATA", "p2_mirror_not_built", []))


class HostCausesAreTheCause(unittest.TestCase):
    """1 journal absent · 2 journal corrupt · 3 valid self-hash, source not attested. Before: 'another task'."""

    def test_each_host_cause_reaches_the_row_and_the_claim_still_blocks(self):
        for name, cause in (("journal_absent", "source_unavailable_or_unsafe"),
                            ("journal_corrupt", "source_unavailable_or_unsafe"),
                            ("local_source_not_attested", "local_source_not_attested"),
                            ("source_not_allowlisted", "source_not_allowlisted"),
                            ("source_busy_wal", "source_busy_or_wal_not_supported"),
                            ("host_clock_invalid", "host_clock_invalid")):
            p, t = told(packet(name))
            self.assertEqual((t["state"], t["cause"]), ("OUTCOME_UNKNOWN", cause), name)
            self.assertNotIn("uncertainty", t, name)
            self.assertIn("Do not retry", t["next"], name)
            self.assertEqual((p["blocks_new_work"], t["acho"]["class"]), (1, "uncertain"), name)


class UnknownStaysUnknown(unittest.TestCase):
    """5 UNKNOWN · 13 authority only from a synthetic callback · 6 finished without evaluation."""

    def test_the_real_unknown_packet_is_told_in_the_hosts_words(self):
        pk = packet("unknown_hitl_required")
        p, t = told(pk)
        self.assertEqual((t["state"], t["sentence"]), ("OUTCOME_UNKNOWN", pk["text"]["summary"]))
        self.assertEqual(t["uncertainty"]["projection_ref"], pk["machine"]["state_ref"])
        self.assertEqual((p["decisions_for_you"], p["blocks_new_work"], t["acho"]["class"]), (1, 1, "uncertain"))

    def test_a_synthetic_acknowledgement_is_never_approval(self):
        p, t = told(packet("synthetic_ack_not_verified"))
        self.assertEqual(t["uncertainty"]["acknowledgement"], "AUTHORITY_NOT_VERIFIED")
        self.assertIn("not approved", t["next"])
        self.assertNotEqual(t["acho"]["class"], "ok")
        self.assertEqual(p["blocks_new_work"], 1)

    def test_finished_without_evaluation_is_not_done(self):
        t = K.task(rec(receipt(grade="NOT_EVALUATED")))
        self.assertEqual((t["state"], t["cause"], t["acho"]["class"]), ("DONE_UNCHECKED", "output_not_evaluated", "empty"))


class OneRefThreeViews(unittest.TestCase):
    """7 refs crossed between tasks · 10 the eye and the ear told different words · 15 over the contract."""

    def test_a_packet_for_another_task_is_set_aside(self):
        _, t = told(packet("unknown_hitl_required"), task_sha256="f" * 64)
        self.assertEqual((t["state"], t["cause"]), ("OUTCOME_UNKNOWN", "uncertainty_for_another_task"))

    def test_views_that_disagree_are_refused(self):
        pk = packet("unknown_hitl_required")
        pk["speech"]["summary"] = "Outcome known; all done."
        self.assertEqual(told(pk)[1]["cause"], "views_say_different_words")
        pk = packet("unknown_hitl_required")
        pk["text"]["state_ref"] = "0" * 64
        self.assertEqual(told(pk)[1]["cause"], "views_bind_different_refs")
        pk = packet("unknown_hitl_required")
        pk["machine"]["extra"] = True
        self.assertEqual(told(pk)[1]["cause"], "views_fields_unknown")

    def test_an_oversize_record_is_refused_and_rows_stay_bounded(self):
        pk = packet("unknown_hitl_required")
        pk["machine"]["record"]["summary"] = "x" * 1100
        pk["text"]["summary"] = pk["speech"]["summary"] = pk["machine"]["record"]["summary"]
        self.assertEqual(told(pk)[1]["cause"], "uncertainty_ref_mismatch")      # resealing is the producer's job
        for name in GOLDEN["packets"]:
            t = told(packet(name))[1]
            self.assertLess(len(json.dumps(t, ensure_ascii=False).encode("utf-8")), K.MAX_TASK_B, name)


class NothingOldReadsAsCurrent(unittest.TestCase):
    """4 projection expired · 12 a cached observation shown as current."""

    def test_ttl_zero_means_read_now(self):
        self.assertIn("uncertainty", told(packet("unknown_hitl_required"), read_at=STAMP)[1])
        _, t = told(packet("unknown_hitl_required"), read_at="2026-11-13T12:00:00Z")
        self.assertEqual((t["state"], t["cause"]), ("OUTCOME_UNKNOWN", "uncertainty_projection_stale"))
        self.assertNotIn("uncertainty", t)

    def test_nothing_between_the_server_and_the_person_keeps_an_api_answer(self):
        sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
        self.assertIn('if (url.pathname.startsWith("/api/")) return;   // nunca de la caché', sw)
        nb = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")
        self.assertIn('fetch(path, { cache: "no-store", credentials: "same-origin" })', nb)


class EvidenceTravels(unittest.TestCase):
    """States without a verifiable ref; a simulation told as a real run."""

    def test_every_receipt_row_carries_its_origin_and_ref(self):
        t = K.task(rec(receipt()))
        self.assertEqual(t["evidence"], {"origin": "MEASURED", "ref": "a" * 64})
        self.assertIn("evidence", K.task(rec(None)))

    def test_a_simulated_run_says_so_in_every_view(self):
        t = K.task(rec(receipt(confidence_basis="synthetic")))
        self.assertEqual((t["state"], t["evidence"]["origin"]), ("DONE_CHECKED", "SIMULATED"))
        self.assertTrue(t["sentence"].startswith("Simulated run: "))
        self.assertIn("Simulated run: ", t["reader"])

    def test_a_receipt_whose_evidence_cannot_be_named_is_no_data(self):
        for over in ({"confidence_basis": "trust_me"}, {"receipt_ref": "not-a-ref"},
                     {"confidence_basis": "NO_DATA"}):                       # a measurement with no basis
            t = K.task(rec(receipt(**over)))
            self.assertEqual((t["state"], t["cause"]), ("NO_DATA", "receipt_evidence_unknown"), over)


class TheClientNeverPretends(unittest.TestCase):
    """8 connection lost while reading · 9 HTTP 500 from a reachable server · 11 one event, two announcements."""

    SCRIPT = """
const els = {}; const mk = () => ({ textContent: '', hidden: false, dataset: {}, children: [], className: '',
  append(...c) { this.children.push(...c); }, replaceChildren() { this.children = []; } });
for (const id of ['notebook-tasks', 'notebook-tasks-status']) els[id] = mk();
global.document = { createElement: mk, getElementById: (id) => els[id] || null };
let writes = 0; Object.defineProperty(els['notebook-tasks-status'], 'textContent',
  { get() { return this._t || ''; }, set(v) { this._t = v; writes++; } });
const N = require('./interface/notebook.js');
(async () => { const out = {};
  global.fetch = async () => { throw new Error('connection reset'); };
  await N.loadTasks('notebook-tasks', 'notebook-tasks-status'); out.lost = els['notebook-tasks-status'].textContent;
  global.fetch = async () => ({ ok: false, status: 500, json: async () => ({}) });
  await N.loadTasks('notebook-tasks', 'notebook-tasks-status'); out.http500 = els['notebook-tasks-status'].textContent;
  out.rows = els['notebook-tasks'].children.length;
  global.fetch = async () => ({ ok: true, json: async () => RAW });
  writes = 0; await N.loadTasks('notebook-tasks', 'notebook-tasks-status');
  await N.loadTasks('notebook-tasks', 'notebook-tasks-status'); out.writes = writes;
  console.log(JSON.stringify(out)); })();
"""

    def test_failures_say_no_data_and_one_event_is_said_once(self):
        raw = K.project([unknown_record(packet("unknown_hitl_required"))], STAMP)
        out = node("const RAW=%s;%s" % (json.dumps(raw), self.SCRIPT))
        self.assertTrue(out["lost"].startswith("NO_DATA"), out)
        self.assertTrue(out["http500"].startswith("NO_DATA"), out)
        self.assertIn("did not answer", out["lost"])
        self.assertIn("answered http 500", out["http500"])                 # reachable server, failed answer
        self.assertEqual(out["rows"], 0)                                   # nothing old painted as current
        self.assertEqual(out["writes"], 1)                                 # the same reading twice: said once


class NoRetryAndNoGrant(unittest.TestCase):
    """14 an uncertain operation retried by accident · no test grants anything."""

    def test_the_task_route_is_read_only_and_the_terms_forbid_retry(self):
        pwa = (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        post = pwa[pwa.index("def _despachar_post"):]
        post = post[:post.index("\n    def ", 10)]
        self.assertNotIn("/api/hexelion/tareas", post)
        self.assertEqual(K.project([], STAMP)["uncertainty_terms"]["no_retry"], True)
        nb = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")
        self.assertNotRegex(nb, r"method:\s*\"POST\"[^\n]*tareas|tareas[^\n]*method:\s*\"POST\"")


if __name__ == "__main__":
    unittest.main()
