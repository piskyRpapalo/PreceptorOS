"""Contrato de la carcasa reorganizable de la app."""
from html.parser import HTMLParser
from pathlib import Path
import unittest


RAIZ = Path(__file__).parent


class _HTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tabs = []
        self.panels = []
        self.elements = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("role") == "tab":
            self.tabs.append(a)
        if tag == "section" and a.get("class") == "panel":
            self.panels.append(a)
        if "id" in a:
            self.elements[a["id"]] = (tag, a)


def _app():
    parser = _HTML()
    parser.feed((RAIZ / "interface/app.html").read_text(encoding="utf-8"))
    return parser


class CarcasaUnaPestana(unittest.TestCase):
    def test_cada_zona_tiene_una_tab_y_un_panel(self):
        app = _app()
        ids = [tab.get("data-panel") for tab in app.tabs]
        self.assertEqual(ids, ["mando", "conversacion", "gobierno", "cuaderno",
                               "lab", "harness", "puerta", "modelos", "ajustes"])
        self.assertEqual(len(ids), len(set(ids)))
        paneles = {panel["id"] for panel in app.panels}
        self.assertEqual(paneles, {"panel-mando", "panel-conversacion", "panel-gobierno",
                                   "panel-cuaderno", "panel-lab", "panel-harness",
                                   "panel-puerta", "panel-modelos", "panel-ajustes"})
        self.assertEqual({tab.get("aria-controls") for tab in app.tabs}, paneles)

    def test_una_sola_zona_activa_y_cabezal_fijo(self):
        app = _app()
        self.assertEqual(sum(tab.get("aria-selected") == "true" for tab in app.tabs), 1)
        self.assertEqual(sum("hidden" not in panel for panel in app.panels), 1)
        html = (RAIZ / "interface/app.html").read_text(encoding="utf-8")
        self.assertIn('<header class="barra">', html)
        self.assertIn("pestanas", app.elements)
        self.assertEqual(app.elements["ir-inicio"][0], "button")

    def test_zona_inactiva_informa_no_data_y_hay_guion_vivo(self):
        app = _app()
        for zona in ("lab", "harness", "puerta", "modelos", "ajustes"):
            self.assertIn(f"id=\"panel-{zona}\"", 
                          (RAIZ / "interface/app.html").read_text(encoding="utf-8"))
        tag, attrs = app.elements["guion-zona"]
        self.assertEqual(attrs.get("role"), "status")
        self.assertEqual(attrs.get("aria-live"), "polite")

    def test_controles_mueven_el_foco_dentro_de_la_misma_pestana(self):
        html = (RAIZ / "interface/app.html").read_text(encoding="utf-8")
        js = (RAIZ / "interface/app.js").read_text(encoding="utf-8")
        self.assertIn("/zonas.js", html)
        self.assertIn('addEventListener("keydown"', js)
        self.assertIn("mostrar(", js)
        self.assertNotIn("location.assign(", js)
        self.assertNotIn("window.location.href", js)

    def test_catalogo_de_zonas_se_sirve_y_se_precachea_offline(self):
        pwa = (RAIZ / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        sw = (RAIZ / "interface/sw.js").read_text(encoding="utf-8")
        self.assertIn('"/zonas.js": ("zonas.js", "application/javascript; charset=utf-8")', pwa)
        self.assertIn('"/app.css?v=3", "/app.js?v=4", "/zonas.js?v=1"', sw)
        html = (RAIZ / "interface/app.html").read_text(encoding="utf-8")
        self.assertIn('<script src="/app.js?v=4"></script>', html)
        self.assertIn('const Cache = "aurelius-armazon-v100"', sw)


if __name__ == "__main__":
    unittest.main()
