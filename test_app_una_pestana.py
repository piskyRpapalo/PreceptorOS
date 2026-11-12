"""Contrato de la carcasa reorganizable de la app."""
import json
from html.parser import HTMLParser
from pathlib import Path
import re
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
        self.assertNotIn("toggle-panel", app.elements)

    def test_cabecero_sin_esfera_ni_control_de_plegado(self):
        html = (RAIZ / "interface/app.html").read_text(encoding="utf-8")
        css = (RAIZ / "interface/app.css").read_text(encoding="utf-8")
        js = (RAIZ / "interface/app.js").read_text(encoding="utf-8")
        self.assertNotIn("rostro-preceptor", html + css)
        self.assertNotIn("preceptoros-up.png", css)
        self.assertNotIn('id="toggle-panel"', html)
        self.assertNotIn("panel-cerrado", html + css + js)
        self.assertNotIn('$("toggle-panel")', js)
        self.assertIn('"/transicion.js?v=2"', (RAIZ / "interface/sw.js").read_text(encoding="utf-8"))

    def test_el_chat_no_repite_ayudas_y_el_modelo_va_al_estado_superior(self):
        html = (RAIZ / "interface/app.html").read_text(encoding="utf-8")
        js = (RAIZ / "interface/app.js").read_text(encoding="utf-8")
        self.assertNotIn('id="pie-chat"', html)
        self.assertNotIn('id="estado-chat-lab"', html + js)
        self.assertNotIn("Each turn takes minutes on a phone. It has not frozen.", js)
        self.assertNotIn("Local orchestrator ready.", js)
        self.assertIn('$("estado").textContent = `${t.chat_modelo(modelo)}${ms}${causaRespuesta}`', js)
        self.assertIn('$("estado").textContent = t.chat_sin_respuesta(causa)', js)
        self.assertIn('respuesta.fuentes.forEach((f) => burbuja(t.chat_fuente(f.id, f.updated_at, f.sha256)))', js)

    def test_talk_no_confunde_motor_antiguo_y_conserva_borrador(self):
        js = (RAIZ / "interface/app.js").read_text(encoding="utf-8")
        self.assertIn('Number.isSafeInteger(cuenta.turnos)', js)
        self.assertIn('"NO_DATA: memory_counts_not_verified"', js)
        self.assertNotIn('$("estado").textContent = d.motor', js)
        # Three failure paths keep the draft: station error, transport error, and an addressed send that was not delivered.
        self.assertEqual(js.count('if (!$("dicho").value.trim()) $("dicho").value = escrito;'), 3)

    def test_tema_instalado_coincide_con_cara_crema(self):
        html = (RAIZ / "interface/app.html").read_text(encoding="utf-8")
        manifest = json.loads((RAIZ / "interface/manifest.json").read_text(encoding="utf-8"))
        css = (RAIZ / "interface/app.css").read_text(encoding="utf-8")
        self.assertIn("--ground: #f4ecda", css)
        self.assertEqual(manifest["theme_color"], "#f4ecda")
        self.assertEqual(manifest["background_color"], "#f4ecda")
        self.assertIn('<meta name="theme-color" content="#f4ecda">', html)

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
        self.assertIn('"/transicion.js": ("transicion.js", "application/javascript; charset=utf-8")', pwa)
        self.assertIn("/transicion.js?v=2", sw)
        self.assertIn('<script src="/transicion.js?v=2"></script>', (RAIZ / "interface/app.html").read_text(encoding="utf-8"))
        cache = re.search(r'preceptoros-armazon-v(\d+)', sw)
        precache = re.search(r'"/app\.js\?v=(\d+)"', sw)
        html = (RAIZ / "interface/app.html").read_text(encoding="utf-8")
        request = re.search(r'<script src="/app\.js\?v=(\d+)"></script>', html)
        self.assertIsNotNone(cache)
        self.assertIsNotNone(precache)
        self.assertIsNotNone(request)
        self.assertGreater(int(cache.group(1)), 104)
        self.assertEqual(precache.group(1), request.group(1))
        self.assertIn('/sting.js?v=1', sw)


if __name__ == "__main__":
    unittest.main()


class RedaccionEnAjustes(unittest.TestCase):
    def test_redaccion_es_tarjeta_de_ajustes_y_frontera_queda_para_a2a(self):
        html = (RAIZ / "interface/app.html").read_text(encoding="utf-8")
        ajustes = html.split('id="panel-ajustes"', 1)[1]
        frontera = html.split('id="panel-gobierno"', 1)[1].split("</section>", 1)[0]
        self.assertIn('id="tarjeta-frontera"', ajustes)
        self.assertNotIn('id="tarjeta-frontera"', frontera)
        self.assertIn("NO_DATA", frontera)


class TecladoMovil(unittest.TestCase):
    def test_el_teclado_redimensiona_el_contenido(self):
        # Joya 7 (Mesa, 2026-11-07): the mobile keyboard resizes the content, so the anchored composer
        # stays visible while typing instead of being covered.
        html = (RAIZ / "interface/app.html").read_text(encoding="utf-8")
        viewport = html.split('name="viewport"', 1)[1].split(">", 1)[0]
        self.assertIn("interactive-widget=resizes-content", viewport)
