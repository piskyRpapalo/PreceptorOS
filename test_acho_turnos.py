"""Autonomy parity S3 · Acho: how a turn sounds is decided with its sentence; the ear hears the screen reader's words."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import audio_feedback as AF
import turnos_hexelion as T
from test_talk_turn_parity import node
from test_turnos_hexelion import msg

ROOT = Path(__file__).resolve().parent
SHA = "b" * 64


def turn(*replies, asked=None):
    return T.turns([asked or msg(1, "soberano", "q")] + [dict(r, n=2) for r in replies])[0]


def act(**m):
    return turn(msg(2, "hexelion", "r", pregunta_n=1, via="mcp_nativo", herramienta="exec", **m))


CASES = {
    "ok": [act(ok=True, rc=0),
           turn(msg(2, "hexelion", "a", pregunta_n=1, modelo="hexelion:latest", ms=10, fuentes=[{"id": 1}])),
           turn(msg(2, "orquestador", "Energy: 3 W", pregunta_n=1))],
    "fence": [act(ok=False, causa="linea dura: git")],
    "exec_fail": [act(ok=False, rc=2)],
    "bridge_down": [turn(msg(2, "hexelion-door", "x", pregunta_n=1, causa="mcp_nativo_missing")),
                    turn(msg(2, "hexelion-door", "x", pregunta_n=1, causa="station_unavailable"))],
    "empty": [act(ok=True, rc=None), act(ok="true", rc=0),
              turn(msg(2, "hexelion-door", "x", pregunta_n=1, causa="no_exact_quote_in_sources")),
              turn(msg(2, "hexelion", "words"))],
    "unanswered": [T.turns([msg(1, "soberano", "q")])[0]],
}


class AchoClass(unittest.TestCase):
    def test_each_outcome_has_its_class(self):
        for clase, turns in CASES.items():
            for t in turns:
                self.assertEqual(t["acho"]["class"], clase, t["state"])

    def test_only_a_proven_success_sounds_like_success(self):
        for clase, turns in CASES.items():
            for t in turns:
                self.assertEqual(t["acho"]["class"] == "ok", t["state"] in ("ACTED", "ANSWERED", "LOCAL_SENSOR", "REPLIED"))
        self.assertEqual(T.acho_class({"state": "SOMETHING_NEW"}), "empty")
        self.assertEqual(T.acho_class({}), "empty")

    def test_the_turn_says_sound_is_off_and_whose_words_it_would_use(self):
        t = CASES["ok"][0]
        self.assertEqual((t["acho"]["sound"], t["acho"]["words"]), ("off_until_turned_on", "reader"))
        self.assertEqual(t["acho"]["motif"], AF.motif_for_class("ok"))


class Cue(unittest.TestCase):
    def test_the_ear_hears_exactly_the_screen_readers_words(self):
        for turns in CASES.values():
            for t in turns:
                cue = AF.cue_for_turn(t)
                self.assertEqual(cue["texto"], t["reader"])
                self.assertEqual((cue["clase"], cue["estado"], cue["sonido"]), (t["acho"]["class"], t["state"], "INACTIVO"))

    def test_every_class_has_its_own_deterministic_motif(self):
        motifs = {c: json.dumps(AF.motif_for_class(c), sort_keys=True) for c in AF.ACHO_CLASSES}
        self.assertEqual(len(set(motifs.values())), len(AF.ACHO_CLASSES))
        self.assertEqual(motifs, {c: json.dumps(AF.motif_for_class(c), sort_keys=True) for c in AF.ACHO_CLASSES})

    def test_malformed_turns_have_no_cue(self):
        good = CASES["ok"][0]
        for bad in (None, [], {}, dict(good, acho=None), dict(good, acho={"class": "success"}),
                    dict(good, acho={"class": ["ok"]}), dict(good, reader=""), dict(good, reader=None)):
            self.assertIsNone(AF.cue_for_turn(bad), bad)
        self.assertIsNone(AF.motif_for_class("waiting"))

    def test_the_public_orchestrator_cue_is_unchanged(self):
        self.assertEqual(AF.project({"intent": "QUERY_STATE", "estado": "MEASURED", "causa": None})["motivo"],
                         {"portadora": 277.18, "moduladora": 554.36, "indice": 20, "dur": 0.28, "vibrato": False})

    def test_a_turn_with_its_acho_stays_under_1024_bytes(self):
        t = turn(msg(2, "hexelion-door", "x", pregunta_n=1, causa="z" * 200), asked=msg(1, "soberano", "ñ" * 600))
        self.assertLess(len(json.dumps(t, ensure_ascii=False).encode("utf-8")), 1024)
        self.assertIn("acho", t)


class ScreenHooks(unittest.TestCase):
    def test_notebook_and_talk_carry_the_class_and_unknown_is_empty(self):
        raw = T.project({"estado": "MEDIDO", "mensajes": [msg(1, "soberano", "q"),
                                                           msg(2, "hexelion-door", "x", pregunta_n=1, causa="station_unavailable")]},
                        "2026-11-13T12:00:00Z")
        raw["turns"].append(dict(raw["turns"][0], n=9, acho={"class": "success"}))
        raw["turns"].append(dict(raw["turns"][0], n=10, state="RUNNING"))
        got = node("const N=require('./interface/notebook.js');const raw=%s;const p=N.projectTurns(raw);"
                   "console.log(JSON.stringify([p.turns.map(t=>t.acho),raw.turns.map(t=>N.turnLine(t).acho),N.achoClasses]))"
                   % json.dumps(raw))
        self.assertEqual(got[0], ["bridge_down", "empty", "empty"])
        self.assertEqual(got[1], ["bridge_down", "empty", "empty"])
        self.assertEqual(sorted(got[2]), sorted(AF.ACHO_CLASSES))
        js = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        nb = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")
        self.assertIn('$("estado").dataset.acho = turno ? turno.acho : ""', js)
        self.assertIn("c.dataset.acho = x.acho", nb)


if __name__ == "__main__":
    unittest.main()
