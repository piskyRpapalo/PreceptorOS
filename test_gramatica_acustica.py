import json
import os
import tempfile
import unittest

import gramatica_acustica
from orquestador import ESQUEMA, enrutar
from test_ficha_cartucho import manifiesto


def pedir(intent, payload):
    return json.dumps({"esquema": ESQUEMA, "intent": intent,
                       "payload": payload}, separators=(",", ":")).encode()


class GramaticaAcusticaTests(unittest.TestCase):
    def test_pares_validos_tienen_codigo_y_locucion_unicos_y_estables(self):
        pares = gramatica_acustica.pares()
        self.assertEqual(set(pares), gramatica_acustica.PARES_VALIDOS)
        motivos = [par["motivo"] for par in pares.values()]
        locuciones = [par["habla"] for par in pares.values()]
        self.assertEqual(len(motivos), len(set(motivos)))
        self.assertEqual(len(locuciones), len(set(locuciones)))
        for (intent, estado), esperado in pares.items():
            with self.subTest(intent=intent, estado=estado):
                self.assertEqual(gramatica_acustica.frase(intent, estado), esperado)
                self.assertLessEqual(len(esperado["habla"]), 80)
        with self.assertRaises(ValueError):
            gramatica_acustica.frase("UPDATE_RAG", "MEASURED")

    def test_esquema_de_respuesta_y_gramatica_tienen_paridad_1_a_1(self):
        ruta = os.path.join(os.path.dirname(__file__), "data",
                            "orquestador-respuesta.schema.json")
        with open(ruta, encoding="utf-8") as fh:
            esquema = json.load(fh)
        declarados = {}
        for variante in esquema["oneOf"]:
            props = variante["properties"]
            clave = (props["intent"]["const"], props["estado"]["const"])
            declarados[clave] = {"motivo": props["motivo"]["const"],
                                 "habla": props["habla"]["const"]}
        self.assertEqual(declarados, gramatica_acustica.pares())

    def test_cada_intencion_devuelve_motivo_y_habla_del_estado(self):
        propuesta = enrutar(pedir("DEPLOY_BUILDING", {"manifiesto": manifiesto()}))
        rechazo = enrutar(pedir("DEPLOY_BUILDING", {}))
        rag = enrutar(pedir("QUERY_STATE", {"consulta": "¿estado?"}),
                      consultar_rag=lambda _: {
                          "estado": "MEASURED", "origen": "memory.fts5",
                          "respuesta": "Respuesta medida", "fuentes": 1,
                          "tokens_rag_aprox": 4, "rag_completo": True})
        bloqueado = enrutar(pedir("UPDATE_RAG", {"consulta": "texto"}))
        for respuesta in (propuesta, rechazo, rag, bloqueado):
            with self.subTest(intent=respuesta["intent"], estado=respuesta["estado"]):
                esperada = gramatica_acustica.frase(respuesta["intent"],
                                                    respuesta["estado"])
                self.assertEqual((respuesta["motivo"], respuesta["habla"]),
                                 (esperada["motivo"], esperada["habla"]))

    def test_consulta_de_estado_mantiene_paridad_measured_stale_y_no_data(self):
        with tempfile.TemporaryDirectory() as raiz:
            with open(os.path.join(raiz, "ensayo.json"), "w", encoding="utf-8") as fh:
                json.dump(manifiesto(), fh)
            res = {}
            for estado in ("MEASURED", "STALE"):
                res[estado] = enrutar(
                    pedir("QUERY_STATE", {"id": "ensayo"}), raiz=raiz,
                    leer_estado=lambda _, estado=estado: {
                        "estado": estado, "origen": "rack:prueba", "dato": {"tic": 8}})
            res["NO_DATA"] = enrutar(pedir("QUERY_STATE", {"id": "ensayo"}),
                                     raiz=raiz)
        for estado, respuesta in res.items():
            with self.subTest(estado=estado):
                self.assertEqual(respuesta["estado"], estado)
                self.assertEqual(respuesta["motivo"],
                                 gramatica_acustica.frase("QUERY_STATE", estado)["motivo"])
                self.assertEqual(respuesta["habla"],
                                 gramatica_acustica.frase("QUERY_STATE", estado)["habla"])


if __name__ == "__main__":
    unittest.main()
