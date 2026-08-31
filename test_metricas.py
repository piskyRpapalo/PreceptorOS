#!/usr/bin/env python3
"""El esquema de METRICAS_NORMA, y sobre todo lo que NO se puede medir.

La mitad del valor de este modulo es que se niegue a publicar cifras. Un
panel de metricas es el sitio donde un cero decorativo se cuela mas facil:
todo el mundo espera ver numeros, asi que un 0 en VRAM pasa por dato. Aqui
se comprueba que no pasa.
"""
from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metricas as MET  # noqa: E402


class TestEsquema(unittest.TestCase):

    def test_estan_los_once_campos_de_la_norma(self):
        """Los once, y con esos nombres. El esquema existe antes que el dato."""
        d = MET.paquete()
        claves = {m["clave"] for m in d["metricas"]}
        self.assertEqual(MET.CAMPOS, claves,
                         f"faltan o sobran: {MET.CAMPOS ^ claves}")

    def test_toda_metrica_esta_medida_o_declara_su_causa(self):
        """La regla de contadores.py, aplicada al MVP."""
        for m in MET.paquete()["metricas"]:
            with self.subTest(clave=m["clave"]):
                self.assertIn(m["estado"], ("MEDIDO", "NO_DATA", "NORMA"))
                if m["estado"] == "NO_DATA":
                    self.assertTrue(m.get("causa"), "NO_DATA sin causa")
                    self.assertIsNone(m["valor"], "NO_DATA con valor")
                else:
                    self.assertIsNotNone(m["valor"])
                    self.assertTrue(m.get("como"), "MEDIDO sin decir como")

    def test_la_vram_jamas_sale_con_cifra(self):
        """La 780M es iGPU: comparte la DDR5 y no tiene VRAM propia.

        Este es el caso que justifica el modulo entero. Un `0` aqui seria
        mentira, y un valor cualquiera tambien: no existe la magnitud. El
        hueco se declara para que nadie improvise su nombre el dia que haya
        una GPU de verdad; el valor se niega.
        """
        v = MET.campo(MET.paquete(), "vram_mb")
        self.assertEqual("NO_DATA", v["estado"])
        self.assertIsNone(v["valor"])
        self.assertIn("iGPU", v["causa"] + v.get("detalle", ""))

    def test_el_cero_decorativo_no_existe(self):
        for m in MET.paquete()["metricas"]:
            if m["estado"] == "NO_DATA":
                with self.subTest(clave=m["clave"]):
                    self.assertNotEqual(0, m["valor"])


class TestTemperatura(unittest.TestCase):

    def test_el_hwmon_se_busca_por_nombre_y_no_por_indice(self):
        """`hwmon3` hoy es k10temp; manana puede ser otro.

        La numeracion de hwmon depende del orden de registro de los drivers y
        no es estable entre arranques. Leer `hwmon3` a ciegas es como leer el
        indice de al lado: da una cifra, y es de otro sensor. En este nodo
        `thermal_zone0` es `acpitz` y marca 20 grados constantes -- un sensor
        muerto que parece vivo.
        """
        fuente = MET.__doc__ + open(MET.__file__, encoding="utf-8").read()
        self.assertIn("k10temp", fuente)
        self.assertNotIn('hwmon3"', fuente, "el indice esta incrustado")
        self.assertNotIn("thermal_zone0", fuente.split("acpitz")[0],
                         "usa thermal_zone0, que en este nodo esta muerto")

    def test_sin_sensor_sale_no_data_y_no_cero(self):
        with mock.patch.object(MET, "_hwmon_por_nombre", return_value=None):
            t = MET.campo(MET.paquete(), "temp_cpu_c")
            self.assertEqual("NO_DATA", t["estado"])
            self.assertIsNone(t["valor"])


class TestConsumoRAM(unittest.TestCase):
    """La cicatriz: `ollama` contiene «llama», y por eso mentia.

    La primera version buscaba procesos cuyo nombre contuviera «llama» y
    tomaba su RSS. El unico que casaba era el propio demonio `ollama` en
    reposo --39 MB-- y el panel publicaba esos 39 MB como «lo que ocupa el
    modelo». Es peor que un NO_DATA: es una cifra plausible, del orden de
    magnitud equivocado, y nadie la habria mirado dos veces.

    La cura no es una lista de nombres mejor: es preguntarle a quien sabe.
    `ollama ps` dice que modelos hay CARGADOS. Si no hay ninguno, no hay
    consumo que medir, por muchos procesos con nombre parecido que corran.
    """

    def test_sin_modelo_cargado_no_hay_consumo_que_medir(self):
        with mock.patch.object(MET, "_modelos_cargados", return_value=[]):
            c = MET.campo(MET.paquete(), "consumo_ram_mb")
            self.assertEqual("NO_DATA", c["estado"])
            self.assertIsNone(c["valor"])

    def test_el_demonio_en_reposo_no_cuenta_como_modelo(self):
        """39 MB no es un modelo de 2,5 GB, y el modulo tiene que saberlo."""
        with mock.patch.object(MET, "_modelos_cargados", return_value=[]):
            c = MET.campo(MET.paquete(), "consumo_ram_mb")
            self.assertNotEqual(39, c["valor"])
            self.assertIn("cargado", c["causa"])


class TestNormasFijas(unittest.TestCase):

    def test_las_dos_normas_se_declaran_antes_de_medir(self):
        """`tokens_sesion` y `ventana_contexto` describen las CONDICIONES.

        Sin ellas dos paquetes no son comparables aunque los dos midan
        honestamente: el mismo modelo con num_ctx 2048 va mas rapido que con
        32768 porque hace menos trabajo.
        """
        d = MET.paquete()
        for clave in ("tokens_sesion", "ventana_contexto"):
            with self.subTest(clave=clave):
                self.assertEqual("NORMA", MET.campo(d, clave)["estado"])
        self.assertIn("norma", d, "el paquete no declara sus normas")

    def test_modelo_base_es_obligatorio(self):
        """Comparar dos LoRA sobre bases distintas es comparar dos cosas."""
        d = MET.paquete()
        self.assertIn("modelo_base", {m["clave"] for m in d["metricas"]})


if __name__ == "__main__":
    unittest.main()
