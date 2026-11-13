"""Talk keeps the person's place (P1 accessibility, measured 2026-11-13 in a headless browser at 360 px).

Before: pressing «Say it» disabled the focused button, so focus fell to <body> after every question and a keyboard
or screen-reader user had to find the box again. The waiting bubble was Spanish inside the English MVP interface.
These are source checks; the live keyboard walk is in the PR receipt."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "interface/app.js").read_text(encoding="utf-8")


def submit_handler():
    start = APP.index('$("form-chat").addEventListener("submit"')
    return APP[start:APP.index("\n});", start)]


class Focus(unittest.TestCase):
    def test_focus_is_remembered_before_anything_is_disabled(self):
        h = submit_handler()
        self.assertLess(h.index("const volverA = document.activeElement;"), h.index('$("enviar").disabled = true;'))

    def test_every_re_enable_gives_focus_back(self):
        h = submit_handler()
        enables = [m.end() for m in re.finditer(re.escape('$("enviar").disabled = false;'), h)]
        self.assertEqual(len(enables), 2)                            # preceptor thread and Hexelion paths
        for end in enables:
            self.assertTrue(h[end:end + 40].lstrip().startswith("devolverFoco(volverA);"))

    def test_focus_comes_back_only_when_it_was_lost(self):
        helper = APP[APP.index("function devolverFoco("):APP.index('$("form-chat").addEventListener("submit"')]
        self.assertIn("document.activeElement === document.body", helper)
        self.assertIn(".focus({ preventScroll: true })", helper)


class Language(unittest.TestCase):
    def test_the_waiting_bubble_speaks_the_interface_language(self):
        h = submit_handler()
        bubble = re.search(r'burbuja\("([^"]+)", "espera"\)', h).group(1)
        self.assertEqual(bubble, "thinking… on a phone this can take minutes")
        self.assertNotIn("pensando", h)



class TabsMoveFromFocus(unittest.TestCase):
    """WAI-ARIA tabs: arrow keys move from the tab that has focus, not from the open panel."""

    def test_arrows_count_from_the_focused_tab(self):
        js = (Path(__file__).resolve().parent / "interface/app.js").read_text(encoding="utf-8")
        self.assertIn('if (e.key === "ArrowRight") siguiente = (n + 1) % paneles.length;', js)
        self.assertIn('if (e.key === "ArrowLeft") siguiente = (n + paneles.length - 1) % paneles.length;', js)
        self.assertNotIn("(panelActual + 1) % paneles.length", js)


if __name__ == "__main__":
    unittest.main()
