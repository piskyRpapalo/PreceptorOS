"""3DFabrika and the two arrows of the tab rail: the core cases, and the contract of the page."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = (ROOT / "interface" / "app.html").read_text(encoding="utf-8")
CSS = (ROOT / "interface" / "app.css").read_text(encoding="utf-8")
JS = (ROOT / "interface" / "app.js").read_text(encoding="utf-8")


class Core(unittest.TestCase):
    def test_the_core_cases_pass_in_node(self):
        r = subprocess.run(["node", "--test", "--test-reporter=tap", "tests/fabrika3d_cases.cjs"], cwd=ROOT,
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-1000:])
        self.assertIn("# pass 11", r.stdout)
        self.assertIn("# fail 0", r.stdout)


class Panel(unittest.TestCase):
    def test_the_tab_is_named_for_every_reader(self):
        tab = re.search(r'<button id="tab-puerta"[^>]*>([^<]*)</button>', HTML)
        self.assertIsNotNone(tab)
        self.assertIn('aria-label="3DFabrika"', tab.group(0))
        self.assertIn('title="3DFabrika"', tab.group(0))
        self.assertEqual(tab.group(1), "3DFabrika")
        self.assertEqual(JS.count('tab_puerta: "3DFabrika"'), 9)

    def test_the_three_steps_are_there_in_order(self):
        order = [HTML.index(x) for x in ("1 · Create", "2 · Review", "3 · Prepare to print")]
        self.assertEqual(order, sorted(order))
        panel = HTML[HTML.index('id="panel-puerta"'):HTML.index('id="panel-modelos"')]
        for wanted in ('id="fab-linea" role="status" aria-live="polite"', 'id="fab-error" role="alert"',
                       'id="fab-maquina"', 'id="fab-voz"', 'for="fab-desc"', 'aria-describedby="fab-desc-ayuda fab-error"'):
            self.assertIn(wanted, panel, wanted)

    def test_the_page_starts_no_printing_and_claims_no_built_part(self):
        panel = HTML[HTML.index('id="panel-puerta"'):HTML.index('id="panel-modelos"')]
        self.assertIn("Nothing is sent to a printer from this screen", panel)
        self.assertNotRegex(panel, r"\bLIVE\b|\bREADY\b")
        wiring = JS[JS.index("/* 3DFabrika · the panel."):JS.index("/* The two arrows of the tab rail")]
        self.assertNotIn("fetch(", wiring)

    def test_the_public_gate_still_lives_in_settings_with_its_ids(self):
        settings = HTML[HTML.index('id="panel-ajustes"'):]
        for wanted in ('id="puerta-estado"', 'id="puerta-llave"', 'id="puerta-copiar-llave"',
                       'id="puerta-documento"', 'id="puerta-copiar-documento"'):
            self.assertIn(wanted, settings, wanted)
            self.assertEqual(HTML.count(wanted), 1, wanted)

    def test_the_nine_zones_are_all_still_there(self):
        zones = re.findall(r'id: "([a-z]+)"', (ROOT / "interface" / "zonas.js").read_text(encoding="utf-8"))
        self.assertEqual(zones, ["mando", "conversacion", "gobierno", "cuaderno", "lab", "harness", "puerta", "modelos", "ajustes"])
        for zone in zones:
            self.assertIn('id="tab-%s"' % zone, HTML)
            self.assertIn('id="panel-%s"' % zone, HTML)


class Arrows(unittest.TestCase):
    def test_two_named_arrows_stand_at_the_ends_of_the_rail(self):
        rail = HTML[HTML.index('class="carril-pestanas"'):HTML.index("</header>")]
        self.assertLess(rail.index('id="panel-anterior"'), rail.index('role="tablist"'))
        self.assertLess(rail.index("</nav>"), rail.index('id="panel-siguiente"'))
        self.assertIn('aria-label="Previous panel"', rail)
        self.assertIn('aria-label="Next panel"', rail)
        self.assertEqual(rail.count('class="flecha"'), 2)
        self.assertEqual(rail.count('role="tab"'), 9)

    def test_the_arrows_are_at_least_44_px_and_show_focus(self):
        rule = re.search(r"\.flecha \{([^}]*)\}", CSS).group(1)
        self.assertIn("min-width: 44px", rule)
        self.assertIn("min-height: 44px", rule)
        self.assertIn("flex: 0 0 44px", rule)
        self.assertRegex(CSS, r"\.flecha:focus-visible \{ outline: 3px solid")
        self.assertIn("forced-colors: active", CSS)

    def test_an_arrow_at_the_end_stays_focusable_and_only_changes_panel(self):
        code = JS[JS.index("/* The two arrows of the tab rail"):]
        self.assertIn('setAttribute("aria-disabled"', code)
        self.assertNotIn(".disabled =", code)
        self.assertNotIn("fetch(", code)
        self.assertIn("mostrar(to)", code)
        self.assertIn("prefers-reduced-motion", code)

    def test_the_tabs_keep_their_own_size_rule(self):
        self.assertIn(".carril-pestanas > .pestanas { flex: 1 1 auto; min-width: 0; }", CSS)


if __name__ == "__main__":
    unittest.main()
