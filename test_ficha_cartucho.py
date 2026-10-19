import copy
import io
import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from ficha_cartucho import FichaInvalida, validar
from orquestador import ESQUEMA, enrutar
from clasificador_cuaternario import parsear


def ficha():
    return {"esquema": "preceptoros.ficha_cartucho/1",
            "verbos": ["DEPLOY_BUILDING", "QUERY_STATE"],
            "mesuras": [{"id": "cooperabilidad", "valor": None,
                         "unidad": "J/token", "estado": "NO_DATA",
                         "causa": "sin_medicion"}],
            "posturas": ["cooperar", "combatir"],
            "cooldown_ticks": 12, "ram_bytes": 268435456}


def manifiesto():
    return {"esquema": "preceptoros.edificio/1", "id": "ensayo", "tipo": "boya",
            "col": 0, "fila": 0, "huella": 1, "nace_tic": 0,
            "madura_tics": 1, "desgaste_por_tic": 0, "ficha": ficha()}


class FichaCartuchoTests(unittest.TestCase):
    def test_esquemas_de_tarjeta_y_cartucho_son_json_lecturable(self):
        root = os.path.dirname(os.path.abspath(__file__))
        for name in ("ficha_cartucho.schema.json", "edificio.schema.json",
                     "orquestador.schema.json", "orquestador-respuesta.schema.json"):
            with self.subTest(name=name):
                with open(os.path.join(root, "data", name), encoding="utf-8") as fh:
                    self.assertEqual(json.load(fh)["$schema"],
                                     "https://json-schema.org/draft/2020-12/schema")

    def test_clasificador_cuaternario_es_exacto_y_falla_a_no_data(self):
        self.assertEqual(parsear("SI"), {"decision": "SI", "causa": None})
        self.assertEqual(parsear("NO_DATA:sin_fuente"),
                         {"decision": "NO_DATA", "causa": "sin_fuente"})
        for raw in ("SI.", "CUANDO porque sí", "NO_DATA:inventada", b"\xff"):
            with self.subTest(raw=raw):
                self.assertEqual(parsear(raw)["decision"], "NO_DATA")

    def test_ficha_canonica_viaja_en_etiqueta_bajo_1024_bytes(self):
        raw = validar(ficha())
        self.assertLess(len(raw), 1024)
        self.assertEqual(raw, validar(copy.deepcopy(ficha())))

    def test_separa_datos_de_piel_y_rechaza_campos_visuales(self):
        visual = ficha()
        visual["silhouette_hex"] = "ab" * 32
        with self.assertRaises(FichaInvalida):
            validar(visual)

    def test_measured_exige_numero_y_no_data_exige_causa(self):
        bad = ficha()
        bad["mesuras"][0].update(estado="MEASURED", causa=None)
        with self.assertRaises(FichaInvalida):
            validar(bad)
        bad["mesuras"][0].update(estado="NO_DATA", valor=None, causa=None)
        with self.assertRaises(FichaInvalida):
            validar(bad)

    def test_router_exige_ficha_y_deja_despliegue_como_propuesta(self):
        request = {"esquema": ESQUEMA, "intent": "DEPLOY_BUILDING",
                   "payload": {"manifiesto": manifiesto()}}
        result = enrutar(json.dumps(request, separators=(",", ":")).encode())
        self.assertEqual(result["estado"], "PROPOSED")
        self.assertEqual(result["requiere"], "FIRMO DESPLIEGUE")
        del request["payload"]["manifiesto"]["ficha"]
        result = enrutar(json.dumps(request, separators=(",", ":")).encode())
        self.assertEqual(result["estado"], "NO_DATA")

    def test_query_sella_estado_origen_y_update_rag_no_escribe(self):
        manifest = manifiesto()
        manifest["desgaste_por_tic"] = 100
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "ensayo.json"), "w", encoding="utf-8") as fh:
                json.dump(manifest, fh)

            def query(estado):
                req = {"esquema": ESQUEMA, "intent": "QUERY_STATE",
                       "payload": {"id": "ensayo"}}
                raw = json.dumps(req, separators=(",", ":")).encode()
                return enrutar(raw, raiz=root,
                               leer_estado=lambda _: {"estado": estado,
                                                      "dato": {"tic": 42},
                                                      "origen": "rack:test"})

            measured = query("MEASURED")
            stale = query("STALE")
            self.assertEqual((measured["estado"], measured["origen"]),
                             ("MEASURED", "rack:test"))
            self.assertEqual((stale["estado"], stale["origen"]),
                             ("STALE", "rack:test"))

        update = {"esquema": ESQUEMA, "intent": "UPDATE_RAG", "payload": {}}
        result = enrutar(json.dumps(update, separators=(",", ":")).encode())
        self.assertEqual(result["estado"], "NO_DATA")
        self.assertIn("no RAG write", result["causa"])

    def test_pwa_expone_router_local_con_techo_duro_de_1024_bytes(self):
        import importlib.util
        import os
        from importlib.machinery import SourceFileLoader
        root = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(root, "bin", "preceptoros-pwa")
        spec = importlib.util.spec_from_loader(
            "orquestador_pwa_test", SourceFileLoader("orquestador_pwa_test", path))
        pwa = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pwa)

        def invoke(raw):
            h = pwa.PWA.__new__(pwa.PWA)
            h.server = SimpleNamespace()
            h.path = "/api/orquestador"
            h.headers = {"Content-Length": str(len(raw))}
            h.rfile = io.BytesIO(raw)
            h.send_response = lambda code: setattr(h, "code", code)
            h.send_header = lambda *_: None
            h.end_headers = lambda: None
            h.wfile = io.BytesIO()
            h._orquestador()
            body = h.wfile.getvalue()
            return h.code, json.loads(body), body

        raw = json.dumps({"esquema": ESQUEMA, "intent": "QUERY_STATE",
                          "payload": {"id": "x"}}, separators=(",", ":")).encode()
        code, receipt, body = invoke(raw)
        self.assertEqual(code, 200)
        self.assertEqual(receipt["estado"], "NO_DATA")
        self.assertTrue(receipt["causa"])
        self.assertLess(len(body), 1024)
        code, _, _ = invoke(b" " * 1024)
        self.assertEqual(code, 400)

    def test_preflight_deja_solo_el_origen_web_exacto_y_content_type(self):
        import importlib.util
        from importlib.machinery import SourceFileLoader
        root = os.path.dirname(os.path.abspath(__file__))
        spec = importlib.util.spec_from_loader(
            "orquestador_cors_test", SourceFileLoader(
                "orquestador_cors_test", os.path.join(root, "bin", "preceptoros-pwa")))
        pwa = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pwa)

        def invoke(origin, headers):
            h = pwa.PWA.__new__(pwa.PWA)
            h.path = "/api/orquestador"
            h.headers = {"Origin": origin, **headers}
            h.send_response = lambda code: setattr(h, "code", code)
            h.send_header = lambda key, value: h.sent.append((key, value))
            h.end_headers = lambda: None
            h.wfile = io.BytesIO()
            h.sent = []
            pwa.PWA.do_OPTIONS(h)
            return h

        good = invoke("https://preceptoros.org", {
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"})
        self.assertEqual(good.code, 204)
        self.assertIn(("Access-Control-Allow-Origin", "https://preceptoros.org"), good.sent)
        bad_origin = invoke("https://example.invalid", {
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"})
        self.assertEqual(bad_origin.code, 403)
        bad_header = invoke("https://preceptoros.org", {
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, authorization"})
        self.assertEqual(bad_header.code, 403)


if __name__ == "__main__":
    unittest.main()
