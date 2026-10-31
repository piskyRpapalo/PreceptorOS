import json
import os
import unittest

import audio_feedback
import estado_compacto
from orquestador import ESQUEMA, enrutar
from test_ficha_cartucho import manifiesto


class ContratoRespuestaTests(unittest.TestCase):
    def test_respuestas_del_router_validan_el_contrato_publico_y_quedan_bajo_1k(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("NO_DATA · jsonschema ausente")
        raiz = os.path.dirname(__file__)
        with open(os.path.join(raiz, "data", "orquestador-respuesta.schema.json"), encoding="utf-8") as f:
            schema = json.load(f)
        with open(os.path.join(raiz, "data", "edificio.schema.json"), encoding="utf-8") as f:
            edificio = json.load(f)
        with open(os.path.join(raiz, "data", "ficha_cartucho.schema.json"), encoding="utf-8") as f:
            ficha = json.load(f)
        jsonschema.Draft202012Validator.check_schema(schema)
        from referencing import Registry, Resource
        registry = Registry().with_resource("urn:preceptoros:edificio:1", Resource.from_contents(edificio))
        registry = registry.with_resource("urn:preceptoros:ficha-cartucho:1", Resource.from_contents(ficha))
        validator = jsonschema.Draft202012Validator(schema, registry=registry)

        def request(intent, payload):
            return json.dumps({"esquema": ESQUEMA, "intent": intent, "payload": payload},
                              separators=(",", ":")).encode()

        responses = [
            enrutar(request("DEPLOY_BUILDING", {"manifiesto": manifiesto()})),
            enrutar(request("DEPLOY_BUILDING", {})),
            enrutar(request("QUERY_STATE", {"consulta": "estado"}), consultar_rag=lambda _: {
                "estado": "MEASURED", "origen": "memory.fts5", "respuesta": "dato local",
                "fuentes": 1, "tokens_rag_aprox": 4, "rag_completo": True}),
            enrutar(request("QUERY_STATE", {"consulta": "estado"})),
            enrutar(request("UPDATE_RAG", {"consulta": "texto"})),
            enrutar(request("MAP_BRAIN_STATUS", {})),
        ]
        for response in responses:
            with self.subTest(intent=response["intent"], state=response["estado"]):
                self.assertEqual([], list(validator.iter_errors(response)))
                self.assertNotIn("motivo", response)
                self.assertNotIn("habla", response)
                self.assertLess(len(estado_compacto.serializar_objeto(response)), 1024)

    def test_contrato_rechaza_no_data_sin_causa_y_campos_no_firmados(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("NO_DATA · jsonschema ausente")
        raiz = os.path.dirname(__file__)
        with open(os.path.join(raiz, "data", "orquestador-respuesta.schema.json"), encoding="utf-8") as f:
            schema = json.load(f)
        validator = jsonschema.Draft202012Validator(schema)
        base = {"esquema": ESQUEMA, "intent": "UPDATE_RAG", "estado": "NO_DATA", "causa": None}
        self.assertTrue(list(validator.iter_errors(base)))
        self.assertTrue(list(validator.iter_errors({**base, "causa": "blocked", "habla": "invented"})))


    def test_relay_veredicto_tipado_falla_cerrado_y_no_acepta_payload(self):
        def request(payload):
            return json.dumps({"esquema": ESQUEMA, "intent": "MAP_BRAIN_STATUS",
                               "payload": payload}, separators=(",", ":")).encode()
        answer = enrutar(request({}))
        self.assertEqual(answer["dato"], {
            "choice": None, "score": None, "no_data": True,
            "causa": "runtime_integrity_unavailable",
        })
        self.assertEqual(answer["estado"], "NO_DATA")
        self.assertEqual(answer["causa"], "runtime_integrity_unavailable")
        refused = enrutar(request({"node": "invented"}))
        self.assertTrue(refused["dato"]["no_data"])
        self.assertEqual(refused["dato"]["causa"], "map_brain_status_payload_invalid")


class ProyeccionAcusticaTests(unittest.TestCase):
    def test_tres_verbos_y_cuatro_estados_coinciden_con_la_gramatica(self):
        expected = {
            ("DEPLOY_BUILDING", "MEASURED"): (220.0, 440.0, 20, 0.28, False),
            ("DEPLOY_BUILDING", "PROPOSED"): (220.0, 440.0, 35, 0.28, True),
            ("DEPLOY_BUILDING", "STALE"): (220.0, 110.0, 60, 0.5, False),
            ("DEPLOY_BUILDING", "NO_DATA"): (220.0, 308.0, 180, 0.4, False),
            ("QUERY_STATE", "MEASURED"): (277.18, 554.36, 20, 0.28, False),
            ("QUERY_STATE", "PROPOSED"): (277.18, 554.36, 35, 0.28, True),
            ("QUERY_STATE", "STALE"): (277.18, 138.59, 60, 0.5, False),
            ("QUERY_STATE", "NO_DATA"): (277.18, 388.05, 180, 0.4, False),
            ("UPDATE_RAG", "MEASURED"): (369.99, 739.98, 20, 0.28, False),
            ("UPDATE_RAG", "PROPOSED"): (369.99, 739.98, 35, 0.28, True),
            ("UPDATE_RAG", "STALE"): (369.99, 185.0, 60, 0.5, False),
            ("UPDATE_RAG", "NO_DATA"): (369.99, 517.99, 180, 0.4, False),
        }
        labels = {"DEPLOY_BUILDING": "Deploy", "QUERY_STATE": "State", "UPDATE_RAG": "Sources"}
        verbs = {"DEPLOY_BUILDING": "deploy", "QUERY_STATE": "state", "UPDATE_RAG": "rag"}
        states = {
            "MEASURED": "measured", "PROPOSED": "proposed, waits a signature",
            "STALE": "stale", "NO_DATA": "NO_DATA",
        }
        for (intent, state), motif in expected.items():
            with self.subTest(intent=intent, state=state):
                result = audio_feedback.project({"intent": intent, "estado": state, "causa": None})
                self.assertEqual(result["verbo"], verbs[intent])
                self.assertEqual(result["estado"], state)
                self.assertEqual(set(result), {
                    "verbo", "estado", "sonido", "sonido_causa", "motivo", "texto", "causa"
                })
                self.assertEqual(tuple(result["motivo"].values()), motif)
                suffix = " (cause not declared by the caller)" if state == "NO_DATA" else ""
                self.assertEqual(result["texto"], labels[intent] + ": " + states[state] + suffix)
                self.assertEqual(result["sonido"], "INACTIVO")

    def test_causa_no_data_y_salida_acustica_no_conectada(self):
        result = audio_feedback.project({
            "intent": "UPDATE_RAG", "estado": "NO_DATA", "causa": "local adapter is not attached",
        })
        self.assertEqual(result["causa"], "local adapter is not attached")
        self.assertIn("(local adapter is not attached)", result["texto"])
        self.assertEqual(result["sonido_causa"], "sound is off until you turn it on")
        missing = audio_feedback.project({"intent": "UPDATE_RAG", "estado": "NO_DATA", "causa": None})
        self.assertEqual(missing["causa"], "cause not declared by the caller")

    def test_seis_entradas_sabotaje_rechazadas(self):
        invalid = (
            None, [],
            {"intent": "WRITE_STATE", "estado": "MEASURED", "causa": None},
            {"intent": "QUERY_STATE", "estado": "UNKNOWN", "causa": None},
            {"intent": 7, "estado": "MEASURED", "causa": None},
            {"intent": "QUERY_STATE", "estado": ["MEASURED"], "causa": None},
        )
        self.assertEqual(len(invalid), 6)
        for value in invalid:
            with self.subTest(value=value):
                self.assertIsNone(audio_feedback.project(value))

    def test_repeticion_y_techo_de_canal(self):
        response = {"intent": "DEPLOY_BUILDING", "estado": "PROPOSED", "causa": None}
        first = audio_feedback.project(response)
        self.assertEqual(first, audio_feedback.project(response))
        encoded = json.dumps(first, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.assertLess(len(encoded), 1024)


if __name__ == "__main__":
    unittest.main()
