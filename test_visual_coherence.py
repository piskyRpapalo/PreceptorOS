"""Visual coherence · one truth, nine panels, one announcement per event (measured audit, 2026-11-13).

The isolated browser walk (tests/autonomia_a11y.browser.cjs, steps 12-13) measures the live behaviour. These tests
pin the decisions at gate level, where no browser runs:
- each view has one home: requests and answers in the Notebook, measured runs in Lab; the other panel points there;
- an empty section is said once by its status line, never repeated by a NO_DATA card;
- Talk: a thread copy of a draft the window already announced arrives quietly; unchanged lines stay silent;
- the zone line does not repeat a focused tab;
- the server's own cause reaches the person: a home without its memory file is NO_DATA, never "cannot reach";
- English first paint, and channel causes as codes, not Spanish prose.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import canales
from test_turnos_hexelion import PWA

ROOT = Path(__file__).resolve().parent
HTML = (ROOT / "interface/app.html").read_text(encoding="utf-8")
APP = (ROOT / "interface/app.js").read_text(encoding="utf-8")
NOTEBOOK = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")
TALK = (ROOT / "interface/conversacion.js").read_text(encoding="utf-8")


class OneHomePerView(unittest.TestCase):
    def test_each_loader_paints_one_panel(self):
        targets = re.findall(r'load(?:Turns|Bench|Tasks)\("([a-z-]+)"', APP + NOTEBOOK)
        self.assertEqual(sorted(set(targets)), sorted(targets), "a view painted in two places")
        self.assertIn('loadBench("lab-bench"', APP)
        self.assertIn('loadTurns("notebook-turns"', NOTEBOOK)
        self.assertNotIn('loadBench("notebook-bench"', NOTEBOOK)
        self.assertNotIn('loadTurns("lab-turno"', APP)

    def test_the_other_panel_points_once(self):
        for pointer, words in (("notebook-bench-pointer", "they live in Lab"),
                               ("lab-turno-pointer", "kept in the Notebook")):
            line = re.search(r'<p [^>]*id="%s"[^>]*>([^<]*)</p>' % pointer, HTML)
            self.assertIsNotNone(line, pointer)
            self.assertIn(words, line.group(1))
            self.assertNotIn("aria-live", line.group(0))          # a signpost, not news

    def test_an_empty_section_is_said_once(self):
        for fn in ("async function loadBench", "async function loadTurns", "async function loadTasks"):
            body = NOTEBOOK[NOTEBOOK.index(fn):NOTEBOOK.index("\n  }\n", NOTEBOOK.index(fn))]
            self.assertNotRegex(body, r'card\("[^"]*", "NO_DATA", summary\)', fn)
            self.assertIn("spoken[statusId] !== summary", body, fn)


class OneAnnouncementPerEvent(unittest.TestCase):
    def test_thread_copies_of_drafts_arrive_quietly(self):
        self.assertIn('li.setAttribute("aria-live", "off")', TALK)
        self.assertIn("draftWords.findIndex((w) => w.includes(m.text))", TALK)
        self.assertIn("draftWords.splice(k, 1)", TALK)              # one draft silences one copy, no more

    def test_lines_are_written_only_when_their_words_change(self):
        self.assertIn("function say(el, text) { if (el && el.textContent !== text) el.textContent = text; }", TALK)
        self.assertNotRegex(TALK, r"out\.textContent = \"Answers here")
        self.assertNotRegex(TALK, r"status\.textContent = ")

    def test_a_focused_tab_is_not_announced_twice(self):
        guion = APP[APP.index("function actualizarGuionZona()"):APP.index("function mostrar(")]
        self.assertIn("enfocandoPestana || document.activeElement === boton", guion)
        self.assertIn("enfocandoPestana = !!opciones.enfocar;", APP)


class TheServersOwnWords(unittest.TestCase):
    def test_a_home_without_memory_is_no_data_not_unreachable(self):
        with tempfile.TemporaryDirectory() as d:
            h = PWA.PWA.__new__(PWA.PWA)
            h.server = SimpleNamespace(ruta_db=os.path.join(d, "missing", "memory.db"), modelo=None)
            out = {}
            h._json = lambda code, body: out.update(code=code, body=body)
            PWA.PWA._estado(h)
        self.assertEqual(out["code"], 200)
        self.assertEqual((out["body"]["estado"], out["body"]["turnos"]), ("NO_DATA", None))
        self.assertTrue(out["body"]["causa"].startswith("memory_db_unavailable_"))
        self.assertIn('"NO_DATA: " + String((d && d.causa)', APP)

    def test_channel_causes_are_codes(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "m.db")
            import memory
            with memory.abrir(db):
                pass
            r = canales.lee("orquesta", base=db)
        self.assertEqual((r["estado"], r["causa"]), ("NO_DATA", "channel_has_no_messages"))
        src = (ROOT / "canales.py").read_text(encoding="utf-8")
        self.assertNotIn("el canal aún no tiene mensajes", src)
        self.assertNotIn("el canal no se pudo leer", src)


class EnglishFirstPaint(unittest.TestCase):
    def test_the_first_words_on_screen_are_english(self):
        self.assertIn('data-i18n="comprobando">checking…</p>', HTML)
        self.assertIn('aria-atomic="true">Active zone: Talk.</p>', HTML)
        for spanish in ("comprobando…</p>", "Zona activa", "Publicar una creación", "Paquete de creación",
                        "Verificar e importar", "ninguna creación"):
            self.assertNotIn(spanish, HTML, spanish)
        publish = (ROOT / "interface/creation_publish.js").read_text(encoding="utf-8")
        self.assertNotRegex(publish, r"[áéíóúñ¿]")


if __name__ == "__main__":
    unittest.main()
