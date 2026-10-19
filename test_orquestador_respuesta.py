import json
import os
import unittest

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


if __name__ == "__main__":
    unittest.main()
