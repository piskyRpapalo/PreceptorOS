"""Hexelion recall (probe 2026-11-12: 0 of 9 answers right): a tag or one extra word no longer hides a memory, and an
exact but unrelated quote is no longer counted as an answer. Every content word is still required (signed rule,
test_memory_lookup: a wrong premise must not pull a memory)."""
from pathlib import Path
import tempfile
import unittest

import hexelion_book
import memory
import memory_lookup
import turnos_hexelion


class Recall(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'memory.db'
        memory.crear(str(self.db))
        with memory.abrir(str(self.db)) as con:
            self.garden = memory.escribir_engrama(con, 'Synthetic garden uses a measured seed', why='fixture', where_ref='fixture:one')['id']
            self.tide = memory.escribir_engrama(con, 'The tide gauge reports every cycle', why='fixture', where_ref='fixture:two')['id']

    def tearDown(self):
        self.temp.cleanup()

    def test_a_bracketed_tag_is_not_a_word_of_the_question(self):
        self.assertEqual(memory_lookup.contenido('[probe] Which seed does the garden use?'), 'seed garden use')
        result = memory_lookup.buscar('[probe] garden seed', self.db)
        self.assertEqual(result['estado'], 'MEASURED')

    def test_question_fillers_are_not_required_but_every_content_word_still_is(self):
        self.assertEqual(memory_lookup.contenido('¿Cuántos garden seeds? tell me please'), 'garden seeds?'.rstrip('?'))
        self.assertEqual(memory_lookup.buscar('[probe] how many garden seed please', self.db)['estado'], 'MEASURED')
        self.assertEqual(memory_lookup.buscar('garden volcano', self.db)['causa'], 'no_matches')   # signed rule kept

    def test_an_exact_quote_must_share_a_word_with_the_question(self):
        self.assertTrue(hexelion_book.relevante('Synthetic garden uses a measured seed', 'Which seed for the garden?'))
        self.assertTrue(hexelion_book.relevante('Hay tres nodos en línea', '¿Cuántos nodo en linea hay?'))  # accents, plural
        self.assertFalse(hexelion_book.relevante('The tide gauge reports every cycle', '[probe] how do I run the app gate?'))
        self.assertFalse(hexelion_book.relevante('the of and', 'what is it'))
        self.assertFalse(hexelion_book.relevante(None, 'garden'))
        archive = [{'id': 9, 'texto': 'The archive says: measured seed 17. The tide is low.'}]
        self.assertTrue(hexelion_book.relevante('measured seed 17', '¿Qué dice el archivo?', archive))   # its sentence
        self.assertFalse(hexelion_book.relevante('The tide is low.', '¿Qué dice el archivo?', archive))  # other sentence

    def test_the_turn_view_explains_the_new_cause_in_plain_words(self):
        self.assertIn('none shares a word with your question', turnos_hexelion.CAUSES['quote_not_relevant'])


class Wiring(unittest.TestCase):
    def test_the_chat_door_checks_relevance_after_verbatim_and_before_answering(self):
        src = (Path(__file__).resolve().parent / 'bin/preceptoros-pwa').read_text(encoding='utf-8')
        verify = src.index('_hexelion_book.verificar_citas(answer')
        relevant = src.index('_hexelion_book.pertinentes(verified["texto"], citations, text, prepared["fuentes"])')
        said = src.index('_canales.di("orquesta", "hexelion"')
        self.assertLess(verify, relevant)
        self.assertLess(relevant, said)
        self.assertIn('return no_data("quote_not_relevant")', src[relevant:said])

    def test_an_unrelated_quote_is_dropped_with_its_citation_and_a_related_one_kept(self):
        sources = [{'id': 1, 'texto': 'LoRA v7 served in Ollama.'}, {'id': 2, 'texto': 'The card carries 3 runs.'}]
        cites = [{'id': 1, 'sha256': 'a'}, {'id': 2, 'sha256': 'b'}]
        text, kept = hexelion_book.pertinentes('LoRA v7 served in Ollama.\nThe card carries 3 runs.', cites, '[probe] LoRA v7', sources)
        self.assertEqual((text, [c['id'] for c in kept]), ('LoRA v7 served in Ollama.', [1]))
        self.assertEqual(hexelion_book.pertinentes('The card carries 3 runs.', cites[1:], 'LoRA v7', sources), (None, None))


if __name__ == '__main__':
    unittest.main()
