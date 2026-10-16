"""Pruebas de integración del proyector visual con el controlador de pestañas."""
from pathlib import Path
import unittest

ROOT = Path(__file__).parent


class IntegracionTransicion(unittest.TestCase):
    def test_solo_muestra_llama_al_proyector_despues_de_cambiar_estado(self):
        js = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        self.assertLess(js.index('actualizarGuionZona();', js.index('function mostrar(')),
                        js.index('PreceptorTransicion.pintar', js.index('function mostrar(')))
        self.assertIn('espejo: indiceAnterior > panelActual', js)
        self.assertIn('onTau: (tau) => { transicionVista.tau = tau; }', js)
        self.assertIn('mostrar(n)', js)
        self.assertNotIn('location.assign(', js)
        self.assertNotIn('window.location.href', js)

    def test_canvas_es_puro_de_presentacion_y_pwa_lo_sirve_offline(self):
        js = (ROOT / "interface/transicion.js").read_text(encoding="utf-8")
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        css = (ROOT / "interface/app.css").read_text(encoding="utf-8")
        pwa = (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
        self.assertIn('setAttribute("aria-hidden", "true")', js)
        self.assertIn('matchMedia("(prefers-reduced-motion: reduce)")', js)
        self.assertIn('pointer-events: none', css)
        self.assertIn('<script src="/transicion.js?v=1"></script>', html)
        self.assertIn('"/transicion.js": ("transicion.js",', pwa)
        self.assertIn('"/transicion.js?v=1"', sw)


if __name__ == "__main__":
    unittest.main()
