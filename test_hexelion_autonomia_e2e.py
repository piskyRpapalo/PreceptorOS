"""Autonomy parity S6 · the smallest end-to-end walk, deterministic, with fake tools.

EVIDENCE LEVEL: SIMULATED. The native MCP is the fake S-3 of test_hexelion_acciones; the P2 journal is a test double
that follows LAB #182's claim rules (claim before dispatch, replay a finished receipt, an unresolved claim blocks).
Not measured here: a running app service, the real journal, a device screen reader or speaker — each NO_DATA.

Walk: a request is asked and acted on; a task is created, blocked on permission, authorised by the person, started,
interrupted, recovered after a restart without running twice, and finished. At every step the six surfaces say the
same thing: Talk's reply turn, Talk's aria-live line, the Notebook card, the screen reader line, the Acho cue and the
machine JSON.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

import audio_feedback as AF
import canales
import tareas_hexelion as K
import test_hexelion_acciones as H
import turnos_hexelion as T
from test_talk_turn_parity import node

NOW = "2026-11-13T12:00:00Z"
EVIDENCE_LEVEL = "SIMULATED"


class JournalDouble:
    """SIMULATED stand-in for LAB #182 ExecutionJournal, persisted in a JSON file so a 'restart' re-reads it.
    It is a test double only: the APP ships no store; the real one is Codex CLI's."""

    def __init__(self, path):
        self.path = Path(path)
        self.claims = json.loads(self.path.read_text()) if self.path.exists() else {}

    def _save(self):
        self.path.write_text(json.dumps(self.claims, sort_keys=True))

    def claim(self, run_id, ref):
        row = self.claims.get(run_id)
        if row:
            if row["ref"] != ref or row["receipt"] is None:
                raise RuntimeError("REPLAY")
            return row["receipt"]
        if any(r["receipt"] is None or r["receipt"]["outcome"] == "UNKNOWN" for r in self.claims.values()):
            raise RuntimeError("EVIDENCE")                 # unknown/in-flight work blocks new claims
        self.claims[run_id] = {"ref": ref, "receipt": None}
        self._save()
        return None

    def finish(self, run_id, ref, receipt):
        row = self.claims.get(run_id)
        if not row or row["ref"] != ref or row["receipt"] is not None:
            raise RuntimeError("EVIDENCE")
        row["receipt"] = receipt
        self._save()

    def records(self, replayed=()):
        return [{"run_id": k, "task_sha256": v["ref"], "receipt": v["receipt"], "replayed": k in replayed}
                for k, v in sorted(self.claims.items())]


def meta(run_id, ref, phase, outcome, failure, gate_ref=None, grade=None):
    return {"schema": "preceptoros.meta-receipt/1", "task_id": "t1", "run_id": run_id, "specialist": "coder",
            "model_version": "f" * 64, "source": "rack", "phase": phase, "observed_at": NOW,
            "measurement": {"tokens": 8, "output_sha256": "e" * 64, "grade": grade} if grade else None,
            "failure_class": failure, "confidence_basis": "synthetic" if grade else "NO_DATA",
            "next_action": "review_receipt", "approval_state": "EXTERNAL_GATE" if gate_ref else "NO_DATA",
            "task_sha256": ref, "approval_ref": gate_ref, "outcome": outcome, "receipt_ref": "a" * 64}


class Walk(unittest.TestCase):
    setUp, tearDown, server, person = H.Door.setUp, H.Door.tearDown, H.Door.server, H.Door.person

    # --- the six surfaces of one request turn -------------------------------------------------------------------
    def surfaces_of_turn(self, reply):
        talk = reply["body"]["turno"]
        machine = next(t for t in T.project(canales.lee("orquesta", 0, base=self.base), NOW)["turns"]
                       if t["n"] == talk["n"])
        screen = node("const N=require('./interface/notebook.js');const m=%s;const c=N.projectTurns({schema:"
                      "'preceptoros.hexelion-turns/1',state:'MEASURED',turns:[m]}).turns[0];const l=N.turnLine(%s);"
                      "console.log(JSON.stringify({card:[c.state,c.sentence,c.acho],live:[l.state,l.line,l.acho]}))"
                      % (json.dumps(machine), json.dumps(talk)))
        cue = AF.cue_for_turn(machine)
        return talk, machine, screen, cue

    def assertOneTurnEverywhere(self, reply, state):
        talk, machine, screen, cue = self.surfaces_of_turn(reply)
        self.assertEqual(talk["state"], state)
        self.assertEqual(screen["card"], [state, machine["sentence"], machine["acho"]["class"]])       # Notebook card
        self.assertEqual(screen["live"], [state, machine["sentence"] + " " + machine["next"],          # Talk aria-live
                                          machine["acho"]["class"]])
        self.assertEqual((talk["sentence"], talk.get("cause")), (machine["sentence"], machine.get("cause")))
        self.assertTrue(machine["reader"].endswith(machine["sentence"] + " " + machine["next"]))       # screen reader
        self.assertEqual((cue["texto"], cue["clase"]), (machine["reader"], machine["acho"]["class"]))  # Acho
        return machine

    # --- the six surfaces of one task --------------------------------------------------------------------------
    def assertOneTaskEverywhere(self, journal, run_id, state, replayed=()):
        machine = K.project(journal.records(replayed), NOW)
        task = next(t for t in machine["tasks"] if t["run_id"] == run_id)
        screen = node("const N=require('./interface/notebook.js');const p=N.projectTasks(%s);"
                      "const t=p.tasks.find(x=>x.run===%s);console.log(JSON.stringify([t.state,t.sentence,t.acho,"
                      "N.taskSummary(p)]))" % (json.dumps(machine), json.dumps(run_id)))
        self.assertEqual(screen[:3], [state, task["sentence"], task["acho"]["class"]])
        self.assertEqual(AF.cue_for_turn(task)["texto"], task["reader"])
        self.assertIn(task["sentence"], task["reader"])
        self.assertEqual(task["state"], state)
        return task, machine, screen[3]

    def test_create_authorize_act_verify_interrupt_resume_once(self):
        self.assertEqual(EVIDENCE_LEVEL, "SIMULATED")
        # 1 · A request is asked and acted on through the fake native MCP: ACTED, said the same six ways.
        self.assertOneTurnEverywhere(self.person("/estado"), "ACTED")
        # 1b · Negative control: a write the fake MCP cannot prove is not counted as done anywhere.
        self.assertOneTurnEverywhere(self.person("/escribe @hexelion-demo a.txt :: b"), "ACTION_UNVERIFIED")

        journal = JournalDouble(Path(self.base) / "journal-double.json")
        ref = hashlib.sha256(b"git status in @hexelion-demo").hexdigest()
        executions = []

        # 2 · Created and blocked on permission: nothing ran; the person hears that it needs them.
        self.assertIsNone(journal.claim("run-1", ref))
        journal.finish("run-1", ref, meta("run-1", ref, "blocked", "NOT_STARTED", "PERMISSION"))
        task, machine, summary = self.assertOneTaskEverywhere(journal, "run-1", "NEEDS_YOUR_AUTHORIZATION")
        self.assertEqual(machine["needs_you"], 1)
        self.assertTrue(summary.startswith("1 task needs your authorization."))
        self.assertEqual(executions, [])

        # 3 · Authorised by the person: the gate reference is the hash of the person's own message in the thread.
        #     A model or agent voice is never a gate (negative control).
        grant = canales.di_soberano("orquesta", "Authorize run-2: git status in @hexelion-demo", base=self.base)
        gate_ref = hashlib.sha256(json.dumps(grant, sort_keys=True).encode()).hexdigest()
        agent = canales.di("cli", "claude", "I authorize run-2", rol="rack CLI agent", base=self.base)
        self.assertNotEqual(agent.get("voz"), "soberano")

        # 4 · Started, then interrupted before any receipt: told as no result recorded, never as running.
        self.assertIsNone(journal.claim("run-2", ref))
        executions.append("run-2")
        self.assertOneTaskEverywhere(journal, "run-2", "NO_RESULT_RECORDED")
        with self.assertRaises(RuntimeError):                       # the unresolved claim blocks new work
            journal.claim("run-3", ref)

        # 5 · Restart: the double is re-read from its file; claiming the same run again is refused, not re-run.
        journal = JournalDouble(Path(self.base) / "journal-double.json")
        with self.assertRaises(RuntimeError):
            journal.claim("run-2", ref)
        self.assertEqual(executions, ["run-2"])

        # 6 · The host resolves it with the checked receipt; the result is verified.
        journal.finish("run-2", ref, meta("run-2", ref, "complete", "KNOWN", "NONE", gate_ref, "PASS"))
        self.assertOneTaskEverywhere(journal, "run-2", "DONE_CHECKED")

        # 7 · Asked again after another restart: the known result is replayed, said so, and never run twice.
        journal = JournalDouble(Path(self.base) / "journal-double.json")
        replay = journal.claim("run-2", ref)
        self.assertEqual(replay["outcome"], "KNOWN")
        task, _, _ = self.assertOneTaskEverywhere(journal, "run-2", "DONE_CHECKED", replayed={"run-2"})
        self.assertIn("it was not run again", task["sentence"])
        self.assertEqual(executions, ["run-2"])                     # exactly once

    def test_what_this_walk_does_not_prove(self):
        """The levels stay separate: a simulation is not a running service, and neither is a screen-reader test."""
        not_measured = {"running_app_service": "NO_DATA(not_exercised_in_ci)",
                        "real_p2_journal": "NO_DATA(p2_mirror_not_built)",
                        "screen_reader_on_device": "NO_DATA(not_exercised)",
                        "physical_audio": "NO_DATA(sound_opt_in_not_built)"}
        self.assertTrue(all(v.startswith("NO_DATA(") for v in not_measured.values()))
        route = K.project(None, NOW, source_cause="p2_mirror_not_built")
        self.assertEqual((route["state"], route["cause"]), ("NO_DATA", "p2_mirror_not_built"))


if __name__ == "__main__":
    unittest.main()
