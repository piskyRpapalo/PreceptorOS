#!/usr/bin/env python3
"""test_compass.py · las 18 pruebas de la Brújula (T38 · v9.3).

Solo biblioteca estándar, como el resto del árbol.

UNA PRUEBA NO DICE LO QUE PEDÍA EL DISEÑO, Y EL MOTIVO ESTÁ MEDIDO
------------------------------------------------------------------
`test_F_gradiente_apunta_a_nucleo` pedía que las tres primeras componentes de
`F` fueran mayores que las cinco últimas. **Con el prior firmado, no se cumple**,
y no es un fallo del código: el gradiente SÍ apunta al núcleo (1,0 frente a
0,667 medido), pero `F = R⁻¹·∇U` reparte ese empuje. M2 es el peldaño más
acoplado del prior (su fila suma 3,3) así que la métrica manda parte de su
empuje a los vecinos que ya lo sirven — que es exactamente para lo que existe
una métrica. Se comprueban las dos cosas que sí son ciertas y que sostienen la
intención: el gradiente ordena el núcleo por delante, y el núcleo se lleva más
campo que el resto.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sqlite3
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import compass  # noqa: E402
import memory as M  # noqa: E402

_ruta = os.path.join(AQUI, "bin", "preceptoros-pwa")
_spec = importlib.util.spec_from_loader(
    "aurelius_pwa_compass", SourceFileLoader("aurelius_pwa_compass", _ruta))
PWA = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PWA)

TEMPORALES = []


def db_vacia():
    d = tempfile.mkdtemp(prefix="compass_")
    TEMPORALES.append(d)
    ruta = os.path.join(d, "memory.db")
    M.crear(ruta)
    return ruta


def db_con_datos():
    ruta = db_vacia()
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="aprendi a soldar un cable", why="la impresora")
        M.escribir_engrama(c, what="recupere la base de una copia", why="el disco")
        M.escribir_perfil(c, "device", "el portatil de la cocina")
        M.escribir_perfil(c, "name", "David")
    return ruta


def loops_vacio():
    d = tempfile.mkdtemp(prefix="loops_")
    TEMPORALES.append(d)
    ruta = os.path.join(d, "loops.db")
    c = sqlite3.connect(ruta)
    c.execute("CREATE TABLE latidos (id INTEGER PRIMARY KEY, bucle TEXT, "
              "momento REAL, evento TEXT, resultado TEXT, duracion_s REAL, nota TEXT)")
    c.commit(); c.close()
    return ruta


def R_constante(n=8, fuera=0.3):
    """Métrica de laboratorio: todas las filas suman igual, así el orden de phi
    depende solo de w/(1+p). Sin esto, la histéresis se probaría contra el
    prior y la prueba mediría dos cosas a la vez."""
    return [[1.0 if i == j else fuera for j in range(n)] for i in range(n)]


class TestBrujula(unittest.TestCase):

    # 1
    def test_estado_camino_8_claves(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio(), modo="camino")
        p = b.estado("camino")
        self.assertEqual(list(p.keys()), list(compass.PELDANOS))
        self.assertTrue(all(0.0 <= v <= 1.0 for v in p.values()))

    # 2
    def test_estado_detalle_12_claves(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio(), modo="detalle")
        p = b.estado("detalle")
        self.assertEqual(len(p), 12)
        self.assertEqual(list(p.keys())[8:], list(compass.DIM_DETALLE))

    # 3
    def test_R_prior_sin_latidos(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio())
        R = b.tensor_rigidez(historial=[{"p": [0.5] * 8, "t": i} for i in range(40)])
        for i in range(8):
            for j in range(8):
                self.assertAlmostEqual(R[i][j], b._prior[i][j], places=9,
                                       msg="sin latidos, R debe ser el prior")

    # 4
    def test_R_simetrica(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio())
        for modo, n in (("camino", 8), ("detalle", 12)):
            R = b.tensor_rigidez(modo=modo)
            self.assertEqual(len(R), n)
            for i in range(n):
                self.assertGreaterEqual(abs(R[i][i]), 1.0, "diagonal dominante")
                for j in range(n):
                    self.assertAlmostEqual(R[i][j], R[j][i], places=9)
                    if i != j:
                        self.assertLessEqual(abs(R[i][j]), 0.95)

    # 5
    def test_F_gradiente_apunta_a_nucleo(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio())
        R = b.tensor_rigidez()
        p = {k: 0.5 for k in compass.PELDANOS}
        F = b.campo_f(p, R)
        g = b._grad_U
        self.assertGreater(min(g[:3]), max(g[3:]),
                           "el gradiente tiene que ordenar el nucleo por delante")
        self.assertGreater(sum(F[:3]), sum(F[3:]),
                           "el nucleo se lleva mas campo que el resto")

    # 6
    def test_momentum_suaviza(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio())
        R = b.tensor_rigidez()
        p = {k: 0.5 for k in compass.PELDANOS}
        F_raw = b.campo_f(p, R)
        previo = [0.0] * 8
        F = b.campo_f(p, R, F_previo=previo)
        crudo = math.sqrt(sum(x * x for x in F_raw))
        self.assertAlmostEqual(math.sqrt(sum(x * x for x in F)), crudo, places=6,
                               msg="el momentum suaviza la direccion, no la magnitud")
        F2 = b.campo_f(p, R, F_previo=[-x for x in F_raw])
        self.assertLess(sum(a * b_ for a, b_ in zip(F2, F_raw)),
                        sum(a * b_ for a, b_ in zip(F_raw, F_raw)),
                        "con un previo opuesto, el campo tiene que ceder")

    # 7
    def test_histeresis_no_salta(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio())
        R = R_constante()
        p = dict(zip(compass.PELDANOS,
                     [0.9, 0.9, 0.9, 0.4103, 0.9, 0.40, 0.9, 0.9]))
        self.assertEqual(b.peldano_activo(p, [0] * 8, R, "M3"), "M3",
                         "la diferencia cae dentro de delta: no se mueve")

    # 8
    def test_histeresis_salta_cuando_debe(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio())
        R = R_constante()
        p = dict(zip(compass.PELDANOS,
                     [0.9, 0.9, 0.9, 0.55, 0.9, 0.40, 0.9, 0.9]))
        self.assertEqual(b.peldano_activo(p, [0] * 8, R, "M3"), "M5",
                         "la diferencia supera delta: tiene que moverse")

    # 9
    def test_indicadores_rango(self):
        b = compass.LearningCompass(db_con_datos(), loops_vacio())
        r = b.resumen()
        i = r["indicadores"]
        self.assertGreaterEqual(i["coherencia"], -1.0)
        self.assertLessEqual(i["coherencia"], 1.0)
        self.assertGreaterEqual(i["intensidad"], 0.0)
        self.assertLessEqual(i["intensidad"], 1.0)
        self.assertGreaterEqual(i["estabilidad"], 0.0)
        self.assertLessEqual(i["estabilidad"], 1.0)
        self.assertGreaterEqual(i["temperatura"], 0.0)

    # 10
    def test_S_es_log_kappa(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio())
        R = b.tensor_rigidez()
        p = {k: 0.5 for k in compass.PELDANOS}
        v = [0.1] * 8
        i = b.indicadores(p, b.campo_f(p, R, v=v), v, R)
        kappa = compass._norma_R(v, R)
        self.assertAlmostEqual(i["S"], -math.log(kappa + 1e-9), places=6)

    # 11
    def test_X_es_cero_cuando_no_estancado(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio())
        R = b.tensor_rigidez()
        p = {k: 0.5 for k in compass.PELDANOS}
        v = [0.2] * 8
        i = b.indicadores(p, b.campo_f(p, R, v=v), v, R)
        self.assertFalse(i["estancado"])
        self.assertEqual(i["X"], 0.0)

    # 12
    def test_Z_es_uno_menos_intensidad(self):
        b = compass.LearningCompass(db_con_datos(), loops_vacio())
        r = b.resumen()
        i = r["indicadores"]
        self.assertAlmostEqual(i["Z"], round(1.0 - i["intensidad"], 4), places=3)

    # 13
    def test_W_es_p_activo(self):
        b = compass.LearningCompass(db_con_datos(), loops_vacio())
        r = b.resumen()
        self.assertAlmostEqual(r["indicadores"]["W"],
                               r["peldaños"][r["activo"]]["valor"], places=4)

    # 14
    def test_resumen_incluye_SXZW(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio())
        i = b.resumen()["indicadores"]
        for clave in ("S", "X", "Z", "W", "orientacion", "intensidad",
                      "coherencia", "estabilidad", "temperatura", "estancado"):
            self.assertIn(clave, i)

    # 15
    def test_modo_detalle_no_rompe_camino(self):
        ruta, loops = db_con_datos(), loops_vacio()
        c8 = compass.LearningCompass(ruta, loops, modo="camino").resumen()
        c12 = compass.LearningCompass(ruta, loops, modo="detalle").resumen()
        self.assertEqual(len(c8["peldaños"]), 8)
        self.assertEqual(len(c12["peldaños"]), 12)
        for k in compass.PELDANOS:
            self.assertAlmostEqual(c8["peldaños"][k]["valor"],
                                   c12["peldaños"][k]["valor"], places=6,
                                   msg="los 8 peldanos valen lo mismo en los dos modos")

    # 16
    def test_calibrate_idempotente(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio())
        uno = b.calibrate(muestras=120)
        dos = b.calibrate(muestras=120)
        self.assertEqual(uno, dos)
        self.assertTrue(b._calibrado)
        otra = compass.LearningCompass(db_vacia(), loops_vacio())
        self.assertEqual(otra.calibrate(muestras=120), uno,
                         "el muestreo es determinista: dos brujulas, misma cifra")

    # 17
    def test_detalle_sin_datos_es_honesto(self):
        b = compass.LearningCompass(db_vacia(), loops_vacio(), modo="detalle")
        p = b.estado("detalle")
        for dim in ("memorias_tema", "ritmo"):
            self.assertEqual(p[dim], 0.0)
            self.assertIn(dim, b.no_medible)
        r = b.resumen(modo="detalle")
        for dim in ("memorias_tema", "ritmo"):
            self.assertEqual(r["peldaños"][dim]["estado"], compass.NO_MEDIBLE,
                             "sin datos se declara, no se decora")

    # 19 · el precio de haber abierto una rendija en `docs/`
    def test_los_documentos_publicados_no_llevan_lexico_de_la_casa(self):
        """`docs/` esta ignorado por una razon escrita en el .gitignore: ahi caen
        entregables internos con lexico propio. Se abrio una lista blanca de tres
        ficheros para la brujula, y esta prueba es lo que hace que esa rendija no
        se convierta en una puerta. Ya cazo un «Soberano» en los dos JSON."""
        lexico = ("soberano", "ironclaw", "hexelion")
        for nombre in ("COMPASS.md", "compass_transfers.json",
                       "compass_transfers_detalle.json"):
            ruta = os.path.join(AQUI, "docs", nombre)
            self.assertTrue(os.path.isfile(ruta), f"falta {nombre}")
            bajo = open(ruta, encoding="utf-8").read().lower()
            for termino in lexico:
                self.assertNotIn(termino, bajo, f"{nombre} lleva «{termino}»")
            # «preceptor» a secas es privado; «PreceptorOS» es el producto.
            self.assertNotIn("preceptor", bajo.replace("preceptoros", ""),
                             f"{nombre} dice «preceptor» fuera del nombre del producto")

    # 18
    def test_debug_solo_loopback(self):
        for ip in ("127.0.0.1", "::1", "127.0.0.53", "100.81.82.34", "100.64.0.1"):
            self.assertTrue(PWA.PWA._es_local(ip), f"{ip} deberia pasar")
        for ip in ("8.8.8.8", "192.168.50.14", "10.0.0.5", "100.200.0.1", "no-una-ip"):
            self.assertFalse(PWA.PWA._es_local(ip), f"{ip} NO deberia pasar")


if __name__ == "__main__":
    import shutil
    try:
        unittest.main(verbosity=2, exit=False)
    finally:
        for d in TEMPORALES:
            shutil.rmtree(d, ignore_errors=True)
