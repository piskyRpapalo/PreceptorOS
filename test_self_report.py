"""«What are you doing, what have you achieved, how do you know, what do you need from me?» (APP-P3, Mesa #3 r7).

One projection (`turnos_hexelion.self_report`) over what the Notebook and the routes already read: the shared thread's
turns, the tasks reading the route serves (`tareas_hexelion.live`) and the signature list. The person asks in Talk
with a phrase or `/informe`; the door answers as a local read (no model, no MCP), and the answer lands in the thread
as one turn, so Talk, the Notebook, the reader line and the JSON all carry it with the same refs.

Rules pinned here: an answer it cannot read is NO_DATA with its source's cause; it never says a process is running;
"nothing needs you" only over measured zeros; simulated or unchecked results are not achievements; its own report
turns are not counted as work; the four answers always fit the chat envelope uncut.
Every class failed on main 18bf0d4 (no phrase, no reader, no projection) before this change.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import unittest
from unittest import mock

import canales
import hexelion_acciones as A
import tareas_hexelion as K
import turnos_hexelion as T
import test_hexelion_acciones as HA
from test_tareas_hexelion import rec, receipt, runs

NOW = dt.datetime(2026, 11, 13, 22, 0, tzinfo=dt.timezone.utc)
STAMP = "2026-11-13T22:00:00Z"
RUNNING = re.compile(r"\b(is|are) (running|working on)\b", re.I)
CLEAR = re.compile(r"nothing (now|needs|waits)|no task (needs|waits)|all clear", re.I)


def turn(n, state, sentence="s", question="q"):
    return {"n": n, "state": state, "sentence": sentence, "question": question}


def turns(*rows, state="MEASURED", cause=None):
    return {"schema": T.SCHEMA, "state": state, "cause": cause, "turns": list(rows)}


def report(tp, kp=None, sig=(True, None, 0), **kw):
    return T.self_report(tp, kp if kp is not None else K.live(STAMP), sig, **kw)


class TheQuestionIsALocalRead(unittest.TestCase):
    def test_phrases_and_command_name_the_report_and_never_the_model(self):
        for said in ("¿Qué estás haciendo?", "What are you doing?", "What have you achieved?", "How do you know?",
                     "¿Qué necesitas de mí?", "What do you need from me?", "o que precisas de mim"):
            self.assertEqual(A.frase(said), "/informe", said)
        self.assertEqual(A.interpreta("/informe"), ("report", {}))
        self.assertEqual(A.interpreta("/report"), ("report", {}))
        self.assertIn("report", T.LOCAL_READS)


class NothingUnknownIsSaidAsKnown(unittest.TestCase):
    def test_a_fresh_home_answers_no_data_four_times_with_causes(self):
        r = report(turns(state="NO_DATA", cause="channel_has_no_messages"), sig=(False, "scraper_not_run", None))
        self.assertEqual({k: v["state"] for k, v in r["answers"].items()},
                         {"doing": "NO_DATA", "achieved": "NO_DATA", "how": "NO_DATA", "needs": "NO_DATA"})
        self.assertEqual(r["answers"]["doing"]["cause"], "p2_mirror_not_built")
        for words in ("p2 mirror not built", "channel has no messages", "scraper not run"):
            self.assertIn(words, r["text"])
        self.assertIsNone(CLEAR.search(r["text"]))

    def test_it_never_says_a_process_is_running(self):
        for kp in (K.live(STAMP), K.project(runs(rec(None)), STAMP)):
            text = report(turns(turn(5, "NO_REPLY_RECORDED")), kp)["text"]
            self.assertIsNone(RUNNING.search(text.replace("never say a process is running", "")), text)

    def test_a_clear_only_over_measured_zeros(self):
        measured = K.project(runs(rec(receipt())), STAMP, complete_ref="c" * 64)
        self.assertIn("Needs from you: nothing now (measured).", report(turns(turn(3, "ACTED")), measured)["text"])
        for kp, sig in ((K.live(STAMP), (True, None, 0)), (measured, (False, "signatures_stale", None)),
                        (measured, (True, None, None))):
            text = report(turns(turn(3, "ACTED")), kp, sig)["text"]
            self.assertIsNone(CLEAR.search(text), text)

    def test_known_decisions_are_said_as_at_least(self):
        from test_host_truth import STAMP as HS, packet, unknown_record
        kp = K.project([unknown_record(packet("unknown_hitl_required"))], HS)
        self.assertIn("at least 1 task decision(s) yours; others unknown (completeness not attested)",
                      report(turns(turn(3, "ACTED")), kp)["text"])


class AWindowIsNotACensus(unittest.TestCase):
    """Mesa #3 round 8 (Cell A review): what is visible is never told as the whole queue."""

    def test_twelve_visible_done_and_a_thirteenth_unresolved(self):
        kp = K.project(runs(*[rec(receipt())] * 12 + [rec(None)]), STAMP, complete_ref="c" * 64)
        self.assertEqual((kp["state"], kp["counters"]["cause"]), ("MEASURED", "records_beyond_window"))
        r = report(turns(turn(3, "ACTED")), kp)
        for k in ("doing", "how"):
            self.assertEqual((r["answers"][k]["state"], r["answers"][k]["cause"]), ("NO_DATA", "records_beyond_window"), k)
        self.assertIn("Doing: at least 12 task(s) visible; completeness NO_DATA (records beyond window)", r["text"])
        self.assertIn("at least 12 task(s) checked", r["text"])
        self.assertNotRegex(r["text"], r"(?<!at least )\b12 task\(s\) (recorded|checked)")
        self.assertEqual(r["answers"]["needs"]["state"], "NO_DATA")

    def test_a_measured_projection_without_counters_is_no_accredited_zero(self):
        legacy = {"schema": "preceptoros.hexelion-tasks/1", "state": "MEASURED", "cause": None, "tasks": [],
                  "needs_you": 0, "blocks_new_work": 0, "decisions_for_you": 0}
        r = report(turns(turn(3, "ACTED")), legacy)
        self.assertEqual((r["answers"]["doing"]["state"], r["answers"]["doing"]["cause"]), ("NO_DATA", "counters_not_stated"))
        self.assertNotIn("0 task(s)", r["text"])
        self.assertIn("completeness NO_DATA (counters not stated)", r["text"])
        self.assertIsNone(CLEAR.search(r["text"]))
        self.assertEqual(r["answers"]["how"]["state"], "NO_DATA")

    def test_only_an_attested_complete_reading_counts_the_queue(self):
        kp = K.project(runs(rec(receipt()), rec(receipt())), STAMP, complete_ref="c" * 64)
        r = report(turns(turn(3, "ACTED")), kp)
        self.assertEqual(r["answers"]["doing"]["state"], "MEASURED")
        self.assertIn("Doing: 2 task(s) recorded (complete reading).", r["text"])


class AchievementsCarryEvidence(unittest.TestCase):
    def test_only_closed_with_evidence_counts_and_unchecked_asks_you(self):
        tp = turns(turn(9, "ANSWERED_UNVERIFIED"), turn(8, "REPLIED"), turn(7, "ACTED"), turn(6, "ANSWERED"),
                   turn(5, "ACTION_UNVERIFIED"), turn(4, "LOCAL_SENSOR"))
        r = report(tp)
        self.assertIn("Achieved: 3 of the last 6 requests closed with evidence (messages 7, 6, 4)", r["text"])
        self.assertIn("check message(s) 9, 5 yourself", r["text"])
        self.assertEqual(r["refs"]["turns"], [9, 8, 7, 6, 5, 4])

    def test_its_own_report_turns_are_not_work(self):
        tp = turns(turn(9, "ACTED", question="What are you doing?"), turn(7, "ACTED", "Hexelion ran «exec».", "/estado"))
        r = report(tp, is_report=lambda q: A.frase(q) == "/informe")
        self.assertIn("Your last request (message 7)", r["text"])
        self.assertEqual(r["refs"]["turns"], [7])


class OneRefForEveryReader(unittest.TestCase):
    def test_the_ref_is_the_hash_of_what_was_said(self):
        r = report(turns(turn(3, "ACTED")))
        body = {k: v for k, v in r.items() if k != "report_ref"}
        self.assertEqual(r["report_ref"], hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True,
                                                                    separators=(",", ":")).encode()).hexdigest())

    def test_the_four_answers_always_fit_uncut(self):
        long = "x" * 230
        tp = turns(*[turn(100 - i, s, long) for i, s in enumerate(["NO_REPLY_RECORDED"] + ["ACTION_UNVERIFIED"] * 6
                                                                   + ["ACTED"] * 5)])
        partial = K.project(runs(*[rec(receipt())] * 11 + [rec(None)] * 2), STAMP, complete_ref="c" * 64)
        for kp in (K.live(STAMP), partial):                      # the longest wording: a partial window
            text = report(tp, kp, sig=(False, "signatures_rows_unreadable", None))["text"]
            self.assertLessEqual(len(text.encode("utf-8")), A.TOPE_LOCAL_B)
            self.assertEqual(A.cabe(text), text)
            self.assertIn("Needs from you:", text)


class ThroughTheDoor(unittest.TestCase):
    """The person asks in Talk; the thread, the turns projection and the reply carry one report."""

    person, thread, tearDown = HA.Door.person, HA.Door.thread, HA.Door.tearDown

    def setUp(self):
        import os
        import tempfile
        from pathlib import Path
        self.tmp = tempfile.TemporaryDirectory()
        self.base = self.tmp.name
        # A local read: any MCP call is a bug, so the server path points at nothing.
        self.env = mock.patch.dict(os.environ, {"PRECEPTOROS_MCP_NATIVO": str(Path(self.base) / "must_not_run.py")})

    def test_asked_once_told_the_same_everywhere(self):
        with mock.patch.object(A, "_edad", wraps=lambda s, now: 300.0):
            out = self.person("What are you doing?")
        self.assertEqual((out["code"], out["body"]["causa"]), (200, "lectura_local;model_not_invoked"))
        acc = out["body"]["respuesta"]["accion"]
        msgs = self.thread()
        self.assertEqual(msgs[-1]["texto"], acc["texto"])                       # Talk's words are the thread's
        ev = msgs[-1]["maquina"]["evidencia"]
        self.assertRegex(ev["report_ref"], r"^[0-9a-f]{64}$")
        self.assertEqual(ev["informe"]["doing"], "NO_DATA")
        row = T.project(canales.lee("orquesta", 0, base=self.base), STAMP)["turns"][0]
        self.assertEqual((row["state"], row["cause"], row["answers"]), ("ACTED", "report_has_no_data", ev["informe"]))
        self.assertEqual(row["acho"]["class"], "empty")                         # missing evidence, never the success mark
        self.assertIn("NO_DATA: doing", row["sentence"])
        self.assertIn(row["sentence"], row["reader"])
        self.assertIsNone(CLEAR.search(acc["texto"]))


if __name__ == "__main__":
    unittest.main()
