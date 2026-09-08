#!/usr/bin/env python3
"""El medidor de la app hablando el esquema que la web publica.

La prueba que importa no es que el diccionario tenga la forma que yo creo: es
que tenga la que el OTRO repo exige. `medidas.json` publica su `contrato` con
la lista de campos obligatorios, y esta suite la lee de ahi. Si alguien anade
un campo obligatorio en la web, esto se pone rojo aqui -- que es el unico sitio
donde puede verse, porque la web no conoce este traductor.
"""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import medidas as MD                             # noqa: E402
import metricas as MT                            # noqa: E402

WEB = os.path.expanduser("~/p0x/preceptoros-web/public/medidas.json")


def paquete_con(**valores):
    """Un paquete de `metricas` con las claves que se le pidan MEDIDAS."""
    m = []
    for clave, valor in valores.items():
        if valor is None:
            m.append(MT.sin_dato(clave, "asi lo pide la prueba", "x"))
        else:
            m.append(MT.medido(clave, valor, "x", "asi lo pide la prueba"))
    return {"esquema": 1, "norma": {}, "metricas": m}


class TestMedidas(unittest.TestCase):

    # --- el contrato del otro lado ----------------------------------------

    def test_estan_TODOS_los_campos_que_la_web_declara_obligatorios(self):
        if not os.path.isfile(WEB):
            self.skipTest("el repo de la web no esta a mano")
        contrato = json.loads(open(WEB, encoding="utf-8").read())["contrato"]
        d = MD.desde_paquete(paquete_con(modelo_nombre="Qwen"))
        for campo in contrato["obligatorio"]:
            with self.subTest(campo=campo):
                cursor, resto = d, campo
                if resto.startswith("lineas[]."):
                    self.assertTrue(d["lineas"], "sin ni una linea")
                    cursor, resto = d["lineas"][0], resto.split(".", 1)[1]
                for parte in resto.split("."):
                    self.assertIn(parte, cursor,
                                  f"la web exige «{campo}» y aqui no sale")
                    cursor = cursor[parte]

    # --- la regla del hueco -----------------------------------------------

    def test_lo_que_no_se_midio_sale_null_Y_con_su_causa(self):
        """Un null sin causa obliga a adivinar si falto el dato o el medidor."""
        d = MD.desde_paquete(paquete_con(tokens_por_segundo=None))
        self.assertIsNone(d["lineas"][0]["generacion"])
        self.assertTrue(any("generacion" in h["que"] for h in d["huecos"]))
        for h in d["huecos"]:
            with self.subTest(hueco=h["que"]):
                self.assertTrue(h["causa"].strip(),
                                f"«{h['que']}» sale sin causa")

    def test_el_prompt_JAMAS_se_deduce_de_la_generacion(self):
        """Son dos velocidades, y aqui se diferencian en un factor de tres.

        Copiar una en la otra no seria aproximar: seria publicar una cifra
        falsa con toda la pinta de estar medida.
        """
        d = MD.desde_paquete(paquete_con(tokens_por_segundo=7.4))
        self.assertEqual(d["lineas"][0]["generacion"], 7.4)
        self.assertIsNone(d["lineas"][0]["prompt"])
        self.assertTrue(any(h["que"].startswith("prompt") for h in d["huecos"]))

    def test_los_tres_huecos_que_siguen_abiertos_se_declaran(self):
        d = MD.desde_paquete(paquete_con(modelo_nombre="Qwen"))
        ques = {h["que"] for h in d["huecos"]}
        for q in ("media por hora", "sha256", "firma"):
            self.assertIn(q, ques)

    # --- lo que esta app SI aporta ----------------------------------------

    def test_el_TTFT_se_llena_porque_esta_app_lo_cronometra(self):
        """Es uno de los cuatro huecos que la web declara hoy."""
        d = MD.desde_paquete(paquete_con(latencia_primer_token_ms=412))
        self.assertEqual(d["lineas"][0]["ttft"], 412)
        self.assertFalse(any(h["que"] == "TTFT" for h in d["huecos"]))

    def test_sin_turno_el_TTFT_es_null_y_no_cero(self):
        """Cero seria «respondio al instante». No lo hubo, que es otra cosa."""
        d = MD.desde_paquete(paquete_con(latencia_primer_token_ms=None))
        self.assertIsNone(d["lineas"][0]["ttft"])

    # --- el modelo ---------------------------------------------------------

    def test_el_modelo_junta_nombre_y_tamano_como_hace_la_web(self):
        d = MD.desde_paquete(paquete_con(modelo_nombre="Qwen3-4B",
                                         modelo_tamano_gb=2.5))
        self.assertEqual(d["modelo"], "Qwen3-4B · 2.5 GB")

    def test_sin_nombre_el_modelo_es_null_con_su_causa(self):
        d = MD.desde_paquete(paquete_con(modelo_nombre=None))
        self.assertIsNone(d["modelo"])
        self.assertTrue(any(h["que"] == "modelo" for h in d["huecos"]))

    # --- el backend --------------------------------------------------------

    def test_sin_modelo_cargado_el_backend_es_null_y_NO_cpu(self):
        """Decir CPU por defecto seria publicar una cifra en la columna
        equivocada: la misma maquina da un factor de tres segun donde corra."""
        real = MD._ollama_ps
        MD._ollama_ps = lambda: "NAME  ID  SIZE  PROCESSOR  UNTIL \n"
        try:
            b, detalle, causa = MD.backend()
            self.assertIsNone(b)
            self.assertIn("no hay ningun modelo cargado", causa)
        finally:
            MD._ollama_ps = real

    def test_el_backend_sale_de_la_columna_PROCESSOR(self):
        real = MD._ollama_ps
        MD._ollama_ps = lambda: (
            "NAME            ID            SIZE      PROCESSOR    UNTIL \n"
            "qwen3:4b        abc123        2.5 GB    100% GPU     4 min \n")
        try:
            b, detalle, causa = MD.backend()
            self.assertEqual(b, "GPU")
            self.assertEqual(detalle, "100% GPU")
            self.assertIsNone(causa)
        finally:
            MD._ollama_ps = real

    def test_un_reparto_entre_los_dos_se_dice_entero(self):
        """«53%/47% CPU/GPU» no es CPU ni es GPU, y el detalle lo aclara."""
        real = MD._ollama_ps
        MD._ollama_ps = lambda: (
            "NAME       ID       SIZE      PROCESSOR         UNTIL \n"
            "qwen:27b   def456   15 GB     53%/47% CPU/GPU   9 min \n")
        try:
            b, detalle, _ = MD.backend()
            self.assertEqual(b, "CPU/GPU")
            self.assertEqual(detalle, "53%/47% CPU/GPU")
        finally:
            MD._ollama_ps = real

    def test_si_ollama_no_contesta_se_dice_en_vez_de_suponer(self):
        real = MD._ollama_ps
        MD._ollama_ps = lambda: None
        try:
            b, _, causa = MD.backend()
            self.assertIsNone(b)
            self.assertIn("ollama ps", causa)
        finally:
            MD._ollama_ps = real

    # --- la ventana --------------------------------------------------------

    def test_la_ventana_no_se_inventa_sus_extremos(self):
        d = MD.desde_paquete(paquete_con(modelo_nombre="Q"))
        self.assertIsNone(d["ventana"]["desde"])
        self.assertIsNone(d["ventana"]["hasta"])
        self.assertEqual(d["ventana"]["muestras"], 1)
        self.assertTrue(d["ventana"]["causa"].strip())

    def test_quien_tiene_los_relojes_los_pasa(self):
        d = MD.desde_paquete(paquete_con(modelo_nombre="Q"),
                             ventana=("2026-09-08T09:00:00Z",
                                      "2026-09-08T10:00:00Z"))
        self.assertEqual(d["ventana"]["desde"], "2026-09-08T09:00:00Z")

    # --- la maquina --------------------------------------------------------

    def test_la_maquina_no_publica_la_palabra_desconocido(self):
        """Un valor verdadero que no dice nada es peor que uno vacio.

        `platform.processor()` devuelve en esta maquina la cadena
        «desconocido» --la palabra, traducida por el sistema-- en vez de una
        cadena vacia. Con un `x or y` eso pasa el filtro y se publica
        «desconocido · 16 hilos · Linux» con toda la pinta de estar medido. Se
        vio en la primera llamada real a `/api/medidas`, no en una prueba: por
        eso hay una ahora.
        """
        m = MD.maquina()
        self.assertNotIn("desconocido", m.lower())
        self.assertNotIn("unknown", m.lower())

    def test_el_modelo_de_cpu_sale_de_proc_cpuinfo(self):
        cpu = MD._cpu()
        if not os.path.exists("/proc/cpuinfo"):
            self.skipTest("sin /proc/cpuinfo")
        self.assertTrue(cpu, "/proc/cpuinfo existe y no dio modelo de CPU")
        self.assertIn(cpu, MD.maquina())

    # --- de punta a punta --------------------------------------------------

    def test_un_paquete_real_del_medidor_se_traduce_sin_reventar(self):
        d = MD.desde_paquete(MT.paquete())
        self.assertEqual(d["esquema"], MD.ESQUEMA)
        self.assertTrue(json.dumps(d))          # serializable, que es el punto
        self.assertIn("maquina", d)
        self.assertTrue(d["maquina"].strip())


if __name__ == "__main__":
    unittest.main()
