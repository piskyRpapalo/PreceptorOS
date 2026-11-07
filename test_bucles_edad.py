"""Pruebas de bucles_edad.py: la edad por bucle del sensor de timers, sin reloj propio."""

import json
import unittest
from pathlib import Path

import bucles_edad as B

AHORA = 1_800_000_000
FUENTE_MODULO = Path(__file__).with_name("bucles_edad.py")


def _fuente(*filas):
    return {"estado": "ok", "propios": list(filas)}


class BuclesEdad(unittest.TestCase):
    def test_fresh_dentro_de_dos_periodos(self):
        r = B.vista(_fuente({"unidad": "a.timer", "ultima": AHORA - 100, "periodo_s": 300}), AHORA)
        self.assertEqual(r["esquema"], "preceptoros.bucles-edad/1")
        self.assertEqual(r["bucles"], [{"nombre": "a.timer", "edad_s": 100,
                                        "estado": "fresh", "causa": "within_threshold"}])
        self.assertEqual(r["no_data"], [])

    def test_stale_pasado_dos_periodos(self):
        r = B.vista(_fuente({"unidad": "a.timer", "ultima": AHORA - 601, "periodo_s": 300}), AHORA)
        self.assertEqual(r["bucles"][0]["estado"], "stale")
        self.assertEqual(r["bucles"][0]["causa"], "over_threshold")
        self.assertEqual(r["bucles"][0]["edad_s"], 601)

    def test_sin_periodo_umbral_de_3600(self):
        r = B.vista(_fuente({"unidad": "f.timer", "ultima": AHORA - 3600},
                            {"unidad": "g.timer", "ultima": AHORA - 3601}), AHORA)
        estados = {b["nombre"]: b["estado"] for b in r["bucles"]}
        self.assertEqual(estados, {"f.timer": "fresh", "g.timer": "stale"})

    def test_sin_marca_de_tiempo_es_no_data(self):
        r = B.vista(_fuente({"unidad": "x.timer"},
                            {"unidad": "y.timer", "ultima": "hoy"},
                            {"unidad": "z.timer", "ultima": True}), AHORA)
        for b in r["bucles"]:
            self.assertEqual((b["estado"], b["edad_s"], b["causa"]), ("NO_DATA", None, "no_last_run"))
        self.assertEqual(len(r["bucles"]), 3)

    def test_reloj_adelantado_es_no_data(self):
        r = B.vista(_fuente({"unidad": "r.timer", "ultima": AHORA + 5, "periodo_s": 60}), AHORA)
        self.assertEqual(r["bucles"][0]["estado"], "NO_DATA")
        self.assertEqual(r["bucles"][0]["causa"], "clock_ahead")
        self.assertIsNone(r["bucles"][0]["edad_s"])

    def test_sin_fuente_no_lanza(self):
        for mala in (None, [], "texto", {"estado": "ok"}, {"propios": "no-lista"}):
            r = B.vista(mala, AHORA)
            self.assertEqual(r["bucles"], [])
            self.assertEqual(r["no_data"], [{"campo": "bucles", "causa": "no_source"}])

    def test_orden_stale_fresh_no_data_y_nombre(self):
        r = B.vista(_fuente(
            {"unidad": "n2.timer"},
            {"unidad": "f2.timer", "ultima": AHORA - 1, "periodo_s": 60},
            {"unidad": "s2.timer", "ultima": AHORA - 9999, "periodo_s": 60},
            {"unidad": "f1.timer", "ultima": AHORA - 1, "periodo_s": 60},
            {"unidad": "s1.timer", "ultima": AHORA - 9999, "periodo_s": 60},
            {"unidad": "n1.timer"}), AHORA)
        nombres = [b["nombre"] for b in r["bucles"]]
        self.assertEqual(nombres, ["s1.timer", "s2.timer", "f1.timer", "f2.timer", "n1.timer", "n2.timer"])

    def test_recorte_bajo_1024_con_marca_de_frame(self):
        filas = [{"unidad": "bucle-" + "x" * 40 + f"{i:03d}", "ultima": AHORA - 9999, "periodo_s": 60}
                 for i in range(60)]
        r = B.vista(_fuente(*filas), AHORA)
        self.assertLessEqual(B._bytes(r), 1023)
        self.assertLess(len(r["bucles"]), 60)
        self.assertEqual(r["no_data"][-1], {"campo": "bucles", "causa": "frame_over_1024"})

    def test_determinismo_dos_llamadas_iguales(self):
        fuente = _fuente({"unidad": "b.timer", "ultima": AHORA - 10, "periodo_s": 60},
                         {"unidad": "a.timer"})
        r1 = B.vista(fuente, AHORA)
        r2 = B.vista(fuente, AHORA)
        self.assertEqual(r1, r2)
        self.assertEqual(B._bytes(r1), B._bytes(r2))
        self.assertEqual(json.dumps(r1), json.dumps(r2))

    def test_el_modulo_no_usa_reloj(self):
        codigo = FUENTE_MODULO.read_text(encoding="utf-8")
        for prohibido in ("time.time", ".now(", "utcnow", "today(", "monotonic", "perf_counter", "import time"):
            self.assertNotIn(prohibido, codigo)

    def test_reloj_invalido_no_lanza(self):
        for malo in (None, True, "1800000000", float("nan")):
            r = B.vista(_fuente({"unidad": "c.timer", "ultima": AHORA - 5}), malo)
            self.assertEqual(r["bucles"][0]["causa"], "no_clock")
            self.assertEqual(r["bucles"][0]["estado"], "NO_DATA")

    def test_fila_que_no_es_objeto_se_declara(self):
        r = B.vista(_fuente("basura", {"unidad": "ok.timer", "ultima": AHORA - 1, "periodo_s": 60}), AHORA)
        self.assertEqual(len(r["bucles"]), 1)
        self.assertIn({"campo": "bucles", "causa": "row_invalid"}, r["no_data"])



class Systemd(unittest.TestCase):  # format measured on the Nexo sensor, 2026-11-07
  def test_systemd_time_period_from_next(self):
    f = {"propios": [{"unidad": "a", "ultima": "Sat 2026-11-07 03:00:00 WET", "proxima": "Sun 2026-11-08 03:00:00 WET"}]}
    b = B.vista(f, 1794020400 + 72000)["bucles"][0]
    self.assertEqual((b["edad_s"], b["estado"]), (72000, "fresh"))
  def test_unknown_zone_no_data(self):
    b = B.vista({"propios": [{"unidad": "a", "ultima": "Sat 2026-11-07 03:00:00 XYZ"}]}, 1794020400)["bucles"][0]
    self.assertEqual(b["estado"], "NO_DATA")

if __name__ == "__main__":
    unittest.main()
