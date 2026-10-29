import json
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import estado_compacto
import lab
import memory
from orquestador import ESQUEMA, enrutar


class ConsultaRAGTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        memory.crear(os.path.join(self.root, "memory.db"))
        with memory.abrir(os.path.join(self.root, "memory.db")) as c:
            memory.escribir_engrama(c, "Atlantis arena uses integer rounds",
                                    why="measured rule source", learned="seed rule")

    def tearDown(self):
        self.tmp.cleanup()

    def test_local_rag_uses_read_only_retrieval_and_does_not_store_chat(self):
        db = os.path.join(self.root, "memory.db")
        before = Path(db).read_bytes()
        prompt_seen = []
        result = lab.consultar_rag(
            "Atlantis rounds", self.root,
            motor=lambda prompt: (prompt_seen.append(prompt) or "The arena uses integer rounds."))
        self.assertEqual(result["estado"], "MEASURED")
        self.assertEqual(result["origen"], "memory.fts5")
        self.assertEqual(result["respuesta"], "The arena uses integer rounds.")
        self.assertIn("Contexto RAG recuperado", prompt_seen[0])
        self.assertEqual(Path(db).read_bytes(), before)
        self.assertFalse(os.path.exists(os.path.join(self.root, "canales")))

    def test_ausencia_de_indice_memoria_o_resultados_es_no_data_con_causa(self):
        absent = tempfile.mkdtemp(prefix="rag-vacio-")
        try:
            result = lab.consultar_rag("hola", absent, motor=lambda _: self.fail("no debe inferir"))
            self.assertEqual(result["estado"], "NO_DATA")
            self.assertIn("no existe", result["causa"])
        finally:
            os.rmdir(absent)
        result = lab.consultar_rag("palabra-sin-coincidencia", self.root,
                                   motor=lambda _: self.fail("no debe inferir sin fuente"))
        self.assertEqual(result["estado"], "NO_DATA")
        self.assertIn("no encontró", result["causa"])

    def test_corrupt_model_never_starts_rag_engine(self):
        import conversacion
        store = Path(self.root) / "models"
        blob = store / "blobs" / ("sha256-" + "a" * 64)
        blob.parent.mkdir(parents=True)
        blob.write_bytes(b"synthetic different bytes")
        ficha = {"mini": {"disponible": True, "sha256": "a" * 64}}
        with mock.patch.object(lab, "modelos_lab", return_value=ficha), \
             mock.patch.object(conversacion, "motor_llama") as start:
            result = lab.consultar_rag("Atlantis rounds", self.root, raiz_ollama=store)
        self.assertEqual(result["estado"], "NO_DATA")
        self.assertIn("SHA-256", result["causa"])
        start.assert_not_called()

    def test_router_sella_respuesta_por_origen_y_respeta_el_sobre(self):
        request = {"esquema": ESQUEMA, "intent": "QUERY_STATE",
                   "payload": {"consulta": "pregunta medida"}}
        raw = json.dumps(request, separators=(",", ":")).encode()
        result = enrutar(raw, consultar_rag=lambda _: {
            "estado": "MEASURED", "origen": "memory.fts5",
            "respuesta": "respuesta local", "fuentes": 1,
            "tokens_rag_aprox": 9, "rag_completo": True})
        self.assertEqual((result["estado"], result["origen"]),
                         ("MEASURED", "memory.fts5"))
        self.assertLess(len(estado_compacto.serializar_objeto(result)), 1024)

    def test_router_no_convierte_respuesta_sin_fuente_en_measured(self):
        request = {"esquema": ESQUEMA, "intent": "QUERY_STATE",
                   "payload": {"consulta": "pregunta"}}
        result = enrutar(json.dumps(request).encode(), consultar_rag=lambda _: {
            "estado": "NO_DATA", "origen": "memory.fts5", "causa": "index absent"})
        self.assertEqual(result["estado"], "NO_DATA")
        self.assertEqual(result["causa"], "index absent")

    def test_router_conserva_causa_de_rag_local_sin_coincidencias(self):
        request = {"esquema": ESQUEMA, "intent": "QUERY_STATE",
                   "payload": {"consulta": "palabra-sin-coincidencia"}}
        raw = json.dumps(request, separators=(",", ":")).encode()
        result = enrutar(raw, raiz=self.root,
                         consultar_rag=lambda consulta: lab.consultar_rag(
                             consulta, self.root,
                             motor=lambda _: self.fail("no debe inferir sin fuente")))
        self.assertEqual(result["estado"], "NO_DATA")
        self.assertIn("no encontró", result["causa"])
        self.assertEqual(result["origen"], "rag")

    def test_update_rag_desde_chat_no_invoca_adaptador(self):
        request = {"esquema": ESQUEMA, "intent": "UPDATE_RAG",
                   "payload": {"consulta": "contenido"}}
        result = enrutar(json.dumps(request).encode(), desde_chat=True,
                         consultar_rag=lambda _: self.fail("UPDATE_RAG nunca llama RAG"))
        self.assertEqual(result["estado"], "NO_DATA")


if __name__ == "__main__":
    unittest.main()
