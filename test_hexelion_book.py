import hashlib
import json
import unittest
from unittest import mock

import hexelion_book as book
import memory_lookup


def source(ident, text, updated="2026-11-06T00:00:00Z"):
    raw = text.encode("utf-8")
    return {"id": ident, "updated_at": updated,
            "sha256": hashlib.sha256(raw).hexdigest(), "texto": text}


class HexelionBookTests(unittest.TestCase):
    def evidence(self, rows):
        return {"esquema": memory_lookup.SCHEMA, "estado": "MEASURED", "fuentes": rows}

    def test_three_sources_768_bytes_prompt_measures_2352_bytes(self):
        rows = [source(i, "x" * 256) for i in range(1, 5)]
        result, prompt = book.construir_prompt("🙂" * 250, self.evidence(rows))
        self.assertEqual(result["estado"], "MEASURED")
        self.assertEqual([item["id"] for item in result["fuentes"]], [1, 2, 3])
        self.assertEqual(result["texto_fuentes_b"], 768)
        self.assertEqual(result["prompt_b"], 2352)
        self.assertEqual(len(prompt.encode("utf-8")), 2352)
        self.assertLessEqual(book.MAX_PROMPT_B, 4096)

    def test_memory_search_no_data_and_empty_sources_stay_caused_no_data(self):
        for evidence, cause in (
                (memory_lookup.unavailable("no_matches"), "no_matches"),
                (self.evidence([]), "memory_no_cited_sources")):
            with self.subTest(cause=cause):
                result, prompt = book.construir_prompt("question", evidence)
                self.assertEqual(result, {"estado": "NO_DATA", "causa": cause})
                self.assertIsNone(prompt)

    def test_changed_hash_and_context_overflow_fail_closed(self):
        bad = source(1, "The source.")
        bad["sha256"] = "0" * 64
        result, prompt = book.construir_prompt("question", self.evidence([bad]))
        self.assertEqual(result["causa"], "memory_source_hash_mismatch")
        self.assertIsNone(prompt)
        result, prompt = book.construir_prompt("question", self.evidence([source(1, "x" * 769)]))
        self.assertEqual(result["causa"], "memory_context_source_budget_exceeded")
        self.assertIsNone(prompt)

    def test_prompt_operational_ceiling_is_enforced(self):
        rows = [source(1, "small source")]
        with mock.patch.object(book, "MAX_PROMPT_B", 12):
            result, prompt = book.construir_prompt("question", self.evidence(rows))
        self.assertEqual(result, {"estado": "NO_DATA", "causa": "memory_context_prompt_budget_exceeded"})
        self.assertIsNone(prompt)

    def test_only_exact_utf8_source_substrings_are_accepted(self):
        row = source(7, "The archive states: arco 🌙 is measured.")
        valid = json.dumps({"citas": [{"id": 7, "quote": "arco 🌙"}]}, ensure_ascii=False)
        result, citations = book.verificar_citas(valid, [row])
        self.assertEqual(result["texto"], "arco 🌙")
        self.assertEqual(citations[0]["sha256"], row["sha256"])
        for invalid in (
                json.dumps({"citas": [{"id": 7, "quote": "arco🌙"}]}, ensure_ascii=False),
                json.dumps({"citas": [{"id": 8, "quote": "arco 🌙"}]}),
                json.dumps({"citas": [{"id": 7, "quote": "invented"}]}),
                '{"citas":[],"citas":[]}'):
            with self.subTest(invalid=invalid[:32]):
                result, citations = book.verificar_citas(invalid, [row])
                self.assertEqual(result["estado"], "NO_DATA")
                self.assertIsNone(citations)

    def test_one_json_fence_and_duplicate_source_ids_are_accepted_once(self):
        row = source(7, "The archive states: arco 🌙 is measured.")
        payload = json.dumps({"citas": [
            {"id": 7, "quote": "arco 🌙"}, {"id": 7, "quote": "is measured"}
        ]}, ensure_ascii=False)
        for opening in ("```\n", "```json\n"):
            with self.subTest(opening=opening):
                result, citations = book.verificar_citas(opening + payload + "\n```", [row])
                self.assertEqual(result["estado"], "MEASURED")
                self.assertEqual(result["texto"], "arco 🌙\nis measured")
                self.assertEqual([item["id"] for item in citations], [7])

    def test_fenced_paragraphs_excess_items_and_garbage_stay_no_data(self):
        row = source(7, "The archive states: " + "x" * 400)
        valid = json.dumps({"citas": [{"id": 7, "quote": "The archive"}]})
        too_many = json.dumps({"citas": [
            {"id": 7, "quote": "x"} for _ in range(4)
        ]})
        oversized = json.dumps({"citas": [{"id": 7, "quote": "x" * 321}]})
        for invalid in (
                "```json\n" + valid + "\n```\nextra",
                "preamble\n```json\n" + valid + "\n```",
                "```\n```json\n" + valid + "\n```\n```",
                "```json\n" + too_many + "\n```",
                oversized,
                "not json"):
            with self.subTest(invalid=invalid[:40]):
                result, citations = book.verificar_citas(invalid, [row])
                self.assertEqual(result["estado"], "NO_DATA")
                self.assertIsNone(citations)

    def test_no_quote_and_quote_over_320_bytes_fail_closed(self):
        row = source(1, "x" * 400)
        for answer, cause in (
                ('{"citas":[]}', "station_extract_not_verified"),
                (json.dumps({"citas": [{"id": 1, "quote": "x" * 321}]}),
                 "station_extract_not_verified")):
            with self.subTest(cause=cause):
                result, citations = book.verificar_citas(answer, [row])
                self.assertEqual(result["estado"], "NO_DATA")
                self.assertIsNone(citations)

    def test_three_citation_receipt_with_320_byte_quote_is_886_bytes(self):
        rows = [source(i, "x" * 256) for i in range(1, 4)]
        _, citations = book.verificar_citas(json.dumps({"citas": [
            {"id": row["id"], "quote": "x" * 100} for row in rows]}, ensure_ascii=False), rows)
        response = {"estado": "MEASURED", "respuesta": {
            "estado": "MEASURED", "texto": "x" * 320, "voz": "hexelion",
            "maquina": {"modelo": "hexelion:latest", "ms": 123.45}, "fuentes": citations},
            "causa": "verified_memory_sources; no authority inferred"}
        self.assertEqual(len(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode()), 886)


if __name__ == "__main__":
    unittest.main()
