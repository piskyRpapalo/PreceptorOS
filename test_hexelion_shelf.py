"""Hexelion's rack shelf (probe 2026-11-12): the OR query keeps only content words, nested third-party clones stay
out, one live facts document answers the questions CLI preceptors really ask, and quote candidates come from the
sentences that hold the question's words."""
import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import hexelion_book
import indice_rack as I

ROOT = Path(__file__).resolve().parent


def builder():
    loader = importlib.machinery.SourceFileLoader("indice_rack_bin", str(ROOT / "bin/indice-rack"))
    spec = importlib.util.spec_from_loader("indice_rack_bin", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


APP_SW = 'const Cache = "preceptoros-armazon-v169";'
APP_HTML = '<script src="/app.js?v=27"></script><script src="/notebook.js?v=5"></script>'
WEB_SW = "const VERSION = 'preceptoros-2026-25-hi';"
PRS = [("preceptoros-web", 814, "HITL · Radio layer 2 on /openworld/", "311e8d99a2e9"), ("lab", 9, "Draft: notes", "abc")]


class Query(unittest.TestCase):
    def test_function_words_and_tags_leave_the_or_query(self):
        self.assertEqual(I._consulta_fts("[probe] how do I run the app gate"), '"run" OR "app" OR "gate"')
        self.assertEqual(I._consulta_fts("which PR is waiting for HITL"), '"PR" OR "waiti"* OR "HITL"')

    def test_content_words_win_over_a_noisy_corpus(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "rack.db"
            noise = [("rack: p0x/x%d.md" % i, "x", "How do the people run which things for the world " * 3, "") for i in range(30)]
            facts = [(I.ORIGEN_HECHOS, "House facts", I.hechos(APP_SW, APP_HTML, WEB_SW, PRS, "now"), "")]
            I.construir(db, noise + facts)
            found = I.buscar("[probe] how do I run the app gate", db)
            self.assertIn("bin/pruebas --rapido", found["fuentes"][0]["texto"])
            self.assertIn("preceptoros-web #814", I.buscar("[probe] which PR waits for HITL", db)["fuentes"][0]["texto"])


    def test_the_chunk_holding_more_question_words_beats_one_that_repeats_a_word(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "rack.db"
            I.construir(db, [("rack: a.md", "gate", "gate gate gate gate gate gate gate gate", ""),
                             ("rack: b.md", "notes", "Long notes about many things. " * 6 + "To run the app gate use the script.", "")])
            self.assertEqual(I.buscar("how do I run the app gate", db, limite=1)["fuentes"][0]["texto"].split("\n")[0], "rack: b.md")

    def test_at_equal_coverage_the_live_fact_comes_first(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "rack.db"
            I.construir(db, [("rack: doc.md", "cache", "The app cache version was v100 in October.", ""),
                             (I.ORIGEN_HECHOS, "House facts", "The current app cache version on main is v168.", "")])
            self.assertTrue(I.buscar("app cache version", db, limite=1)["fuentes"][0]["texto"].startswith(I.ORIGEN_HECHOS))


class Facts(unittest.TestCase):
    def test_live_facts_are_plain_quotable_sentences(self):
        text = I.hechos(APP_SW, APP_HTML, WEB_SW, PRS, "2026-11-12 15:00 UTC")
        for line in ("The current app cache version on main is preceptoros-armazon-v169 (interface/sw.js).",
                     "The current app script version on main is app.js?v=27 and notebook.js?v=5 (interface/app.html).",
                     "The current web service worker version on main is preceptoros-2026-25-hi (public/sw.js).",
                     "To run the app gate: bin/pruebas --rapido for the fast gate, bin/pruebas for the full gate (AGENTS.md)."):
            self.assertIn(line, text)
        self.assertIn("preceptoros-web #814 Radio layer 2 on /openworld/ at head 311e8d99", text)
        self.assertNotIn("Draft: notes", text)                       # only HITL titles wait for a signature
        self.assertTrue(all(len(c.encode()) <= I.CHUNK_B for c in I.trozos(I.ORIGEN_HECHOS, text)))

    def test_an_unreadable_value_is_no_data_with_its_cause(self):
        text = I.hechos("", "", "", [], "now")
        self.assertIn("The current app cache version on main is NO_DATA (app sw.js unreadable)", text)
        self.assertIn("The current web service worker version on main is NO_DATA (web sw.js unreadable)", text)
        self.assertIn("Each open PR that waits for signature (HITL) now: none.", text)


class Sources(unittest.TestCase):
    def test_nested_git_clones_are_skipped_and_house_files_kept(self):
        b = builder()
        with tempfile.TemporaryDirectory() as d:
            top = Path(d) / "propuestas"
            (top / "eyes" / "awesome" / ".git").mkdir(parents=True)
            (top / "eyes" / "awesome" / "README.md").write_text("third party")
            (top / "plan.md").write_text("house")
            (top / "eyes" / "notes.md").write_text("house too")
            self.assertTrue(b.clonado(top / "eyes" / "awesome" / "README.md", top))
            self.assertFalse(b.clonado(top / "plan.md", top))
            self.assertFalse(b.clonado(top / "eyes" / "notes.md", top))

    def test_builder_reads_facts_first_and_the_handoff_notes(self):
        src = (ROOT / "bin/indice-rack").read_text(encoding="utf-8")
        self.assertIn('[("facts", desde_hechos())]', src)
        self.assertIn('("memory", desde_memoria())', src)
        self.assertIn("and not clonado(p, P0X / sub)", src)


class Candidates(unittest.TestCase):
    SOURCE = [{"id": 7, "texto": "rack: facts (live, from main)\nMeasured from main at now.\nThe sky is blue today.\n"
                               "Some other line here.\nAnd one more filler line.\nThe app cache version on main is v168."}]

    def quotes(self, question):
        fmt = hexelion_book.formato_citas(self.SOURCE, question)
        return fmt["properties"]["citas"]["items"]["properties"]["quote"]["enum"]

    def test_the_sentence_that_answers_is_a_candidate(self):
        self.assertEqual(self.quotes("what is the app cache version")[0], "The app cache version on main is v168.")
        self.assertNotIn("The app cache version on main is v168.", self.quotes(None))   # old order: opening lines only

    def test_every_candidate_is_still_an_exact_substring(self):
        for q in self.quotes("what is the app cache version"):
            self.assertIn(q, self.SOURCE[0]["texto"])


class Wiring(unittest.TestCase):
    def test_the_chat_door_passes_the_question_to_the_candidates(self):
        src = (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        self.assertIn('_hexelion_book.formato_citas(prepared["fuentes"], text)', src)


if __name__ == "__main__":
    unittest.main()
