import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import memory
import memory_lookup


class LookupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'memory.db'
        memory.crear(str(self.db))
        with memory.abrir(str(self.db)) as con:
            self.ident = memory.escribir_engrama(con, 'Synthetic garden uses a measured seed',
                                                why='fixture provenance', where_ref='fixture:one')['id']

    def tearDown(self):
        self.temp.cleanup()

    def test_existing_index_returns_exact_citation_without_writes(self):
        before = self.db.read_bytes()
        result = memory_lookup.buscar('garden', self.db)
        self.assertEqual(result['estado'], 'MEASURED')
        source = result['fuentes'][0]
        self.assertEqual(source['id'], self.ident)
        self.assertEqual(source['sha256'], hashlib.sha256(source['texto'].encode()).hexdigest())
        self.assertTrue(source['updated_at'])
        self.assertLess(len(memory_lookup.encoded(result)), 1024)
        self.assertEqual(self.db.read_bytes(), before)

    def test_archive_never_returns_through_lookup(self):
        with memory.abrir(str(self.db)) as con:
            memory.archivar(con, self.ident)
        result = memory_lookup.buscar('garden', self.db)
        self.assertEqual(result['causa'], 'no_matches')

    def test_missing_database_is_not_created(self):
        missing = Path(self.temp.name) / 'absent.db'
        self.assertEqual(memory_lookup.buscar('garden', missing)['estado'], 'NO_DATA')
        self.assertFalse(missing.exists())

    def test_index_missing_fails_closed_without_building_it(self):
        import sqlite3
        bare = Path(self.temp.name) / 'bare.db'
        sqlite3.connect(bare).close()
        before = bare.read_bytes()
        self.assertEqual(memory_lookup.buscar('garden', bare)['causa'], 'memory_index_unavailable')
        self.assertEqual(bare.read_bytes(), before)

    def test_final_utf8_ceiling_reports_whole_source_omissions(self):
        with memory.abrir(str(self.db)) as con:
            for _ in range(9):
                memory.escribir_engrama(con, 'garden ' + '漢' * 65)
        result = memory_lookup.buscar('garden', self.db)
        self.assertLess(len(memory_lookup.encoded(result)), 1024)
        self.assertGreater(result['fuera'], 0)
        self.assertFalse(result['completo'])

    def test_invalid_inputs_never_reach_database(self):
        for query in ('', None, 'a' * 601, '漢' * 500):
            self.assertEqual(memory_lookup.buscar(query, self.db)['estado'], 'NO_DATA')

    def test_decision_without_a_local_adapter_is_no_data(self):
        result = memory_lookup.decision_unavailable()
        self.assertEqual(result['estado'], 'NO_DATA')
        self.assertEqual(result['causa'], 'no_local_decision_adapter')
        self.assertEqual(result['fuentes'], [])
        self.assertLess(len(memory_lookup.encoded(result)), 1024)


class NaturalQuestionTests(unittest.TestCase):
    """A natural question keeps only its content words; every content word is still required."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'memory.db'
        memory.crear(str(self.db))
        with memory.abrir(str(self.db)) as con:
            memory.escribir_engrama(con, 'LoRA v7 servido en Ollama: dos lineas')

    def tearDown(self):
        self.temp.cleanup()

    def test_spanish_question_finds_the_memory(self):
        for q in ('¿Qué LoRA está servido en Ollama?', 'which LoRA is servido in Ollama?'):
            self.assertEqual(memory_lookup.buscar(q, self.db)['estado'], 'MEASURED', q)

    def test_content_words_are_still_all_required(self):
        self.assertEqual(memory_lookup.buscar('¿Qué LoRA está en Kubernetes?', self.db)['causa'], 'no_matches')

    def test_only_function_words_keeps_the_original_query(self):
        self.assertEqual(memory_lookup.contenido('¿qué es esto?'), '¿qué es esto?')
        self.assertEqual(memory_lookup.contenido('¿Qué LoRA está servido?'), 'LoRA servido')


if __name__ == '__main__':
    unittest.main()
