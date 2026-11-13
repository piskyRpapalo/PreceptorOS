"""Evidence chip (visual-coherence commission P3): the thread's evidence state is a shape, one English word and a colour.

Source and wiring checks; the node cases in tests/evidence_chip_cases.cjs hold the table. Not a model call,
not a state decision: the chip only shows what the record says."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def leer(ruta):
    return (ROOT / ruta).read_text(encoding="utf-8")


class Cableado(unittest.TestCase):
    def test_la_pagina_carga_el_componente_antes_del_hilo(self):
        html = leer("interface/app.html")
        self.assertIn('<script src="/evidence_chip.js?v=1"></script>', html)
        self.assertLess(html.index("/evidence_chip.js?v=1"), html.index("/conversacion.js?v=3"))

    def test_el_servidor_sirve_el_componente(self):
        self.assertIn('"/evidence_chip.js": ("evidence_chip.js"', leer("bin/preceptoros-pwa"))

    def test_el_service_worker_lo_instala_y_sube_la_cache(self):
        sw = leer("interface/sw.js")
        self.assertIn('"/evidence_chip.js?v=1"', sw)
        self.assertIn("preceptoros-armazon-v180", sw)
        self.assertIn("2026-11-13 (evidence chip, visual-coherence commission)", sw)

    def test_el_pie_del_hilo_usa_el_componente_y_no_el_texto_crudo(self):
        conv = leer("interface/conversacion.js")
        self.assertIn("PreceptorEvidence.make(doc, m.seal)", conv)
        self.assertNotIn('foot.join(" · ")', conv)

    def test_el_css_tiene_forma_palabra_y_forced_colors(self):
        css = leer("interface/app.css")
        for tono in ("ok", "warn", "quiet", "stop"):
            self.assertIn(".evidence-chip.evidence-%s" % tono, css)
        self.assertIn("@media (forced-colors: active)", css)
        self.assertIn("border: 1.5px solid currentColor", css)


class Tabla(unittest.TestCase):
    def test_las_palabras_visibles_estan_en_ingles(self):
        js = leer("interface/evidence_chip.js")
        for palabra in re.findall(r'word: "([^"]+)"', js):
            with self.subTest(palabra=palabra):
                self.assertNotRegex(palabra, r"MEDIDO|DECLARADO|DENEGADO|SIN DATOS")

    def test_el_caso_de_nodo_casos_en_node(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("NO_DATA · sin node no se ejecutan los casos del componente. Remedio: instalar Node")
        r = subprocess.run([node, str(ROOT / "tests" / "evidence_chip_cases.cjs")], cwd=ROOT,
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('"ok":true', r.stdout)


if __name__ == "__main__":
    unittest.main()
