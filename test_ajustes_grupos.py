"""Settings folds into four named groups; every card keeps its id, and nothing is lost or duplicated."""
import pathlib
import re
import unittest
from html.parser import HTMLParser

HTML = (pathlib.Path(__file__).resolve().parent / "interface/app.html").read_text(encoding="utf-8")
GROUPS = [("ajustes-dispositivo", "This device and privacy", ["energy-title", "captura-consent", "redaccion-titulo", "keep-device-title"]),
          ("ajustes-voz", "Voice and creations", ["creation-voice-title", "creation-publish-title"]),
          ("ajustes-nodo", "Node identity", ["nodo-export-title", "node-registration-title", "node-building-title"]),
          ("ajustes-puerta", "Public gate and local tray", ["puerta-ajustes", "tray-heading"])]


class Balance(HTMLParser):
    VOID = {"meta", "link", "input", "br", "img", "hr", "source", "path", "circle", "rect", "line", "polyline"}

    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append((tag, self.stack[-3:]))
        else:
            self.stack.pop()


class SettingsGroups(unittest.TestCase):
    def panel(self):
        return HTML[HTML.index('id="panel-ajustes"'):HTML.index("</main>")]

    def test_four_groups_in_order_each_holding_its_cards(self):
        panel = self.panel()
        found = re.findall(r'<details class="grupo ajustes-grupo" id="([a-z-]+)"', panel)
        self.assertEqual(found, [g for g, _, _ in GROUPS])
        bounds = [panel.index('id="%s"' % g) for g, _, _ in GROUPS] + [len(panel)]
        for i, (gid, title, cards) in enumerate(GROUPS):
            chunk = panel[bounds[i]:bounds[i + 1]]
            self.assertIn('<summary><h3 id="%s-titulo">%s</h3></summary>' % (gid, title), chunk)
            for card in cards:
                self.assertEqual(HTML.count('id="%s"' % card), 1, card)
                self.assertIn('id="%s"' % card, chunk, card)
        self.assertIn('id="ajustes-dispositivo" open>', panel)
        self.assertEqual(panel.count(" open>"), 1)            # only the first group starts open

    def test_header_stays_first_and_markup_balances(self):
        panel = self.panel()
        self.assertLess(panel.index('class="panel-cabecera"'), panel.index("ajustes-grupo"))
        b = Balance()
        b.feed(HTML)
        self.assertEqual(b.errors, [])


if __name__ == "__main__":
    unittest.main()
