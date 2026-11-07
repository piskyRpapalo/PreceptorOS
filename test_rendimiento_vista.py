"""Pruebas de rendimiento_vista.py. Lectura pura: entra la forma de
captura.rendimiento(...) (captura.py:438-470) y sale el documento de la
pestaña Harness. Ninguna prueba abre base de datos ni red: las filas son dicts
a mano con la misma forma.
"""

import json
import unittest

import rendimiento_vista as V


def fila(modelo="m:v1", tarea="instalar", turnos=10, juzgados=10, tasa=0.8,
         ctx_fuera=0.5):
    return {"modelo": modelo, "tarea": tarea, "turnos": turnos,
            "juzgados": juzgados, "aciertos": 0, "tasa": tasa,
            "alucinaciones": 0, "mudos": 0, "ctx_tokens_medio": 300,
            "ctx_fuera_medio": ctx_fuera, "parciales": 0}


def tam(doc):
    return len(json.dumps(doc, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


class VistaRendimiento(unittest.TestCase):

    def test_sin_juzgar_es_no_data_y_jamas_cero(self):
        r = V.vista([fila(turnos=90, juzgados=0, tasa=None)])["filas"][0]
        self.assertEqual(r["estado"], "NO_DATA")
        self.assertIsNone(r["tasa"])
        self.assertEqual(r["causa"], "no_judged_turns")
        self.assertEqual(r["turnos"], 90)

    def test_medido_solo_con_juzgados_y_tasa(self):
        r = V.vista([fila(juzgados=5, tasa=0.4, ctx_fuera=0.2)])["filas"][0]
        self.assertEqual(r["estado"], "MEASURED")
        self.assertEqual(r["tasa"], 0.4)
        self.assertEqual(r["juzgados"], 5)
        self.assertIsNone(r["causa"])

    def test_sin_measured_cuando_juzgados_es_cero(self):
        d = V.vista([fila(juzgados=0, tasa=None),
                     fila(modelo="b", juzgados=0, tasa=None)])
        self.assertEqual(len(d["filas"]), 2)
        self.assertTrue(all(r["estado"] == "NO_DATA" for r in d["filas"]))

    def test_context_short_no_es_fallo_del_modelo(self):
        r = V.vista([fila(tasa=0.3, juzgados=10, ctx_fuera=1.4)])["filas"][0]
        self.assertEqual(r["estado"], "MEASURED")
        self.assertEqual(r["causa"], "context_short_not_model")

    def test_context_no_aplica_con_tasa_alta_o_contexto_en_1(self):
        d = V.vista([fila(modelo="a", tasa=0.5, ctx_fuera=1.4),
                     fila(modelo="b", tasa=0.3, ctx_fuera=1.0)])
        self.assertTrue(all(r["causa"] is None for r in d["filas"]))

    def test_orden_tasa_desc_none_al_final_luego_modelo_y_tarea(self):
        d = V.vista([
            fila(modelo="z", tarea="a", juzgados=0, tasa=None),
            fila(modelo="b", tarea="y", tasa=0.5),
            fila(modelo="a", tarea="x", tasa=0.5),
            fila(modelo="c", tarea="x", tasa=0.9),
            fila(modelo="a", tarea="w", tasa=0.5),
        ])
        orden = [(r["modelo"], r["tarea"]) for r in d["filas"]]
        self.assertEqual(orden, [("c", "x"), ("a", "w"), ("a", "x"),
                                 ("b", "y"), ("z", "a")])

    def test_recorte_bajo_1023_con_frame_over(self):
        filas = [fila(modelo="modelo-%03d" % i, tarea="t" * 40, tasa=i / 1000)
                 for i in range(60)]
        d = V.vista(filas)
        self.assertLessEqual(tam(d), 1023)
        self.assertLess(len(d["filas"]), 60)
        self.assertIn({"campo": "filas", "causa": "frame_over_1024"},
                      d["no_data"])

    def test_fila_malformada_se_omite_y_se_cuenta(self):
        d = V.vista([fila(), {"modelo": "x"}])
        self.assertEqual(len(d["filas"]), 1)
        self.assertIn({"campo": "fila", "causa": "malformed_row"}, d["no_data"])

    def test_varias_malformadas_van_en_una_entrada_con_recuento(self):
        d = V.vista([None, 3, {"modelo": "x"}, fila(tasa=1.5)])
        self.assertEqual(d["filas"], [])
        self.assertEqual([e for e in d["no_data"] if e["campo"] == "fila"],
                         [{"campo": "fila", "causa": "malformed_row:4"}])

    def test_lista_vacia_no_rows(self):
        d = V.vista([])
        self.assertEqual(d["esquema"], "preceptoros.rendimiento-vista/1")
        self.assertEqual(d["filas"], [])
        self.assertEqual(d["no_data"],
                         [{"campo": "rendimiento", "causa": "no_rows"}])

    def test_determinismo_n2(self):
        entrada = [fila(modelo="b", tasa=0.2),
                   fila(modelo="a", tarea="z", tasa=None, juzgados=0),
                   fila(modelo="a", tasa=0.2)]
        a = json.dumps(V.vista(entrada))
        self.assertEqual(a, json.dumps(V.vista(entrada)))
        self.assertEqual(a, json.dumps(V.vista(list(reversed(entrada)))))

    def test_tamano_siempre_menor_de_1024(self):
        for n in (0, 1, 5, 20, 200):
            d = V.vista([fila(modelo="m%d-ñññññ" % i, tarea="t" * 30,
                              tasa=(i % 10) / 10) for i in range(n)])
            self.assertLess(tam(d), 1024, "n=%d" % n)

    def test_entrada_basura_no_lanza(self):
        for entrada in (None, "x", 42, {"a": 1}):
            d = V.vista(entrada)
            self.assertEqual(d["filas"], [])


if __name__ == "__main__":
    unittest.main()
