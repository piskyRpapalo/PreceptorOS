"""Common panel header: the nine panels open the same way (title, status, refresh where a source is read)."""
import pathlib
import re
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
HTML = (ROOT / "interface/app.html").read_text(encoding="utf-8")
JS = (ROOT / "interface/app.js").read_text(encoding="utf-8")
PANELS = ["mando", "conversacion", "gobierno", "cuaderno", "lab", "harness", "puerta", "modelos", "ajustes"]
ENGLISH = {"mando": "Command", "conversacion": "Talk", "gobierno": "Boundary", "cuaderno": "Notebook", "lab": "Lab",
           "harness": "Harness", "puerta": "3DFabrika", "modelos": "World", "ajustes": "Settings"}
WITH_REFRESH = {"conversacion", "gobierno", "lab", "harness", "ajustes"}   # cuaderno keeps its own labelled button
WITH_STATUS = set(PANELS) - {"mando", "gobierno"}   # Command: compass speaks itself; Boundary: the HITL list does


class Headers(HTMLParser):
    def __init__(self):
        super().__init__()
        self.panel, self.depth, self.inside, self.found = None, 0, False, {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "section" and a.get("role") == "tabpanel":
            self.panel = a["id"].removeprefix("panel-")
            self.found[self.panel] = {"label": a.get("aria-label"), "first": None, "h2": 0, "status": 0, "refresh": []}
            return
        if self.panel is None:
            return
        info = self.found[self.panel]
        if info["first"] is None:
            info["first"] = "header" if tag == "header" and "panel-cabecera" in a.get("class", "") else tag
        if tag == "header" and "panel-cabecera" in a.get("class", ""):
            self.inside, self.depth = True, 0
        elif self.inside:
            if tag == "h2":
                info["h2"] += 1
            if a.get("role") == "status":
                info["status"] += 1
            if tag == "button" and "refrescar" in a.get("class", ""):
                info["refresh"].append(a)

    def handle_endtag(self, tag):
        if tag == "header" and self.inside:
            self.inside = False


class PanelHeader(unittest.TestCase):
    def setUp(self):
        self.p = Headers()
        self.p.feed(HTML)

    def test_every_panel_opens_with_one_header_and_one_title(self):
        self.assertEqual(sorted(self.p.found), sorted(PANELS))
        for panel in PANELS:
            info = self.p.found[panel]
            self.assertEqual(info["first"], "header", panel)
            self.assertEqual(info["h2"], 1, panel)

    def test_status_lines_and_english_names(self):
        for panel in PANELS:
            info = self.p.found[panel]
            self.assertEqual(info["status"], 1 if panel in WITH_STATUS else 0, panel)
            self.assertEqual(info["label"], ENGLISH[panel], panel)

    def test_refresh_only_where_a_loader_exists_and_always_named(self):
        table = re.search(r"const cargadores = \{(.*?)\n\};", JS, re.S).group(1)
        loaders = set(re.findall(r"^  (\w+):", table, re.M))
        self.assertEqual(loaders, WITH_REFRESH | {"cuaderno"})
        for panel in PANELS:
            buttons = self.p.found[panel]["refresh"]
            self.assertEqual(len(buttons), 1 if panel in WITH_REFRESH else 0, panel)
            for b in buttons:
                self.assertEqual(b["data-refrescar"], panel)
                self.assertTrue(b["aria-label"].startswith("Refresh "))
                self.assertEqual(b["type"], "button")

    def test_opening_and_refreshing_use_the_same_loader(self):
        self.assertIn("cargarPanel(paneles[panelActual].id);", JS)
        self.assertIn('closest("button.refrescar[data-refrescar]")', JS)
        self.assertNotIn('paneles[panelActual].id === "lab") { cargarLab()', JS)


if __name__ == "__main__":
    unittest.main()
