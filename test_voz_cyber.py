#!/usr/bin/env python3
"""M3 · la garganta de Aurelius: efectos, resolucion de rutas, y no bloquear.

sistema: MVP · solo biblioteca estandar.

Dos mitades y la frontera entre ellas:

  · Lo que se puede probar SIEMPRE, en cualquier maquina, sin Piper y sin
    modelo: los efectos (pitch, saturacion, reverb) sobre un WAV sintetico que
    esta suite se fabrica, la resolucion de rutas, y que la voz ausente
    devuelve None en vez de reventar.
  · Lo que solo se puede probar si Piper esta compilado y el modelo bajado.
    Eso se SALTA, y al saltarlo se dice por que. Una prueba que se salta en
    silencio es una prueba que no existe y que ademas miente sobre el total.

Ninguna ruta de carpeta personal vive en este repo. El caso `test_00` lo
comprueba leyendo `voz.py`: el repo es publico, y una ruta bajo el home es
justo lo que `guardrails` redacta al exportar. Quien tenga Piper en su casa lo
declara con AURELIUS_ESPEAK_DATA / AURELIUS_PIPER.
"""
from __future__ import annotations

import math
import os
import re
import struct
import sys
import tempfile
import unittest
import wave

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import voz  # noqa: E402


def wav_sintetico(ruta, hz=220, segundos=0.25, framerate=22050, amplitud=12000):
    """Un tono puro escrito a mano. Sin Piper, sin red, sin fichero de nadie."""
    n = int(framerate * segundos)
    muestras = [int(amplitud * math.sin(2 * math.pi * hz * i / framerate))
                for i in range(n)]
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(framerate)
        w.writeframes(struct.pack(f"<{len(muestras)}h", *muestras))
    return muestras


def leer_wav(ruta):
    with wave.open(ruta, "rb") as w:
        framerate = w.getframerate()
        canales = w.getnchannels()
        ancho = w.getsampwidth()
        crudo = w.readframes(w.getnframes())
    return list(struct.unpack(f"<{len(crudo)//2}h", crudo)), framerate, canales, ancho


class TestSinRutasPersonales(unittest.TestCase):
    """La frontera del repo publico."""

    def test_00_voz_no_lleva_ninguna_ruta_de_carpeta_personal(self):
        with open(os.path.join(AQUI, "voz.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        # Se prohiben las dos formas: la literal (/home/alguien, /Users/alguien)
        # y la que la calcula (expanduser("~/algo")) para todo lo que no sea la
        # casa del producto, ~/.aurelius, que es donde vive lo de la persona a
        # proposito y por doctrina.
        literales = re.findall(r"[\"'](/home/[^\"'/]+|/Users/[^\"'/]+)", fuente)
        self.assertEqual(literales, [],
                         f"voz.py lleva una ruta de home literal: {literales}")
        expandidas = re.findall(r'expanduser\(\s*"~/([^"]*)"', fuente)
        fuera = [e for e in expandidas if not e.startswith(".aurelius")]
        self.assertEqual(fuera, [],
                         "voz.py adivina una carpeta bajo el home que no es la "
                         f"casa del producto: {fuera}")


class TestResolucionEspeak(unittest.TestCase):
    """El orden: entorno declarado -> sistema -> NO_DATA."""

    def setUp(self):
        self.antes = {k: os.environ.get(k)
                      for k in ("AURELIUS_ESPEAK_DATA", "AURELIUS_PIPER")}

    def tearDown(self):
        for k, v in self.antes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_01_lo_declarado_manda_sobre_el_sistema(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ["AURELIUS_ESPEAK_DATA"] = d
            self.assertEqual(voz.espeak_data(), d,
                             "lo declarado por entorno no gano al sistema")

    def test_02_declarado_que_no_existe_es_NO_DATA_y_no_cae_al_sistema(self):
        os.environ["AURELIUS_ESPEAK_DATA"] = "/no/existe/espeak-ng-data"
        self.assertEqual(voz.espeak_data(), voz.NO_DATA,
                         "una ruta declarada y rota cayo al sistema en silencio")

    def test_03_sin_declarar_se_mira_el_sistema_o_se_dice_NO_DATA(self):
        os.environ.pop("AURELIUS_ESPEAK_DATA", None)
        hallado = voz.espeak_data()
        if hallado == voz.NO_DATA:
            self.skipTest("esta maquina no tiene espeak-ng-data en ninguna "
                          "ubicacion del sistema: NO_DATA es la respuesta "
                          "correcta y no hay nada mas que comprobar")
        self.assertTrue(os.path.isdir(hallado),
                        f"se devolvio una ubicacion que no es un directorio: {hallado}")
        self.assertFalse(hallado.startswith(os.path.expanduser("~") + "/"),
                         f"la busqueda del sistema devolvio una ruta del home: {hallado}")

    def test_04_las_ubicaciones_declaradas_son_del_sistema_no_de_nadie(self):
        for patron in voz.ESPEAK_SISTEMA:
            self.assertTrue(patron.startswith("/usr/") or patron.startswith("/opt/"),
                            f"{patron!r} no es una ubicacion del sistema")

    def test_05_piper_sigue_el_mismo_orden(self):
        os.environ["AURELIUS_PIPER"] = "/no/existe/piper"
        self.assertEqual(voz.piper_binario(), voz.NO_DATA,
                         "un piper declarado y roto no se declaro NO_DATA")


class TestEfectos(unittest.TestCase):
    """El cyber de la voz cyber. Se prueba sobre un tono fabricado aqui."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.entrada = os.path.join(self.tmp.name, "base.wav")
        self.salida = os.path.join(self.tmp.name, "cyber.wav")
        self.original = wav_sintetico(self.entrada)

    def tearDown(self):
        self.tmp.cleanup()

    def test_06_resample_con_factor_1_no_toca_la_onda(self):
        muestras = [0, 1000, -1000, 32767, -32768]
        self.assertEqual(voz.resample_grave(muestras, 1.0), muestras)

    def test_07_factor_mayor_que_1_estira_la_onda_es_decir_la_agrava(self):
        estirada = voz.resample_grave(self.original, 1.5)
        self.assertEqual(len(estirada), int(len(self.original) * 1.5),
                         "el estiramiento no dio la longitud pedida")

    def test_08_aplicar_efectos_escribe_un_wav_valido(self):
        self.assertTrue(voz.aplicar_efectos(self.entrada, self.salida),
                        "aplicar_efectos fallo sobre un WAV que acabamos de escribir")
        muestras, framerate, canales, ancho = leer_wav(self.salida)
        self.assertEqual(framerate, 22050, "los efectos cambiaron el framerate")
        self.assertEqual(canales, 1)
        self.assertEqual(ancho, 2)
        self.assertGreater(len(muestras), 0, "el WAV de salida esta vacio")

    def test_09_ninguna_muestra_se_sale_del_rango_de_16_bits(self):
        # Saturacion y reverb suman: si una muestra se pasa de 32767, `struct`
        # revienta al empaquetar. Que el fichero exista ya lo prueba, pero se
        # comprueba el valor para que el dia que se cambie el reverb el fallo
        # diga que paso y no solo "struct.error".
        voz.aplicar_efectos(self.entrada, self.salida, saturacion=3.0,
                            reverb_decay=0.9)
        muestras, _, _, _ = leer_wav(self.salida)
        self.assertTrue(all(-32768 <= m <= 32767 for m in muestras),
                        "una muestra se salio del rango de 16 bits")

    def test_10_el_pitch_alarga_la_salida_respecto_a_la_entrada(self):
        voz.aplicar_efectos(self.entrada, self.salida, pitch=1.25,
                            saturacion=1.0, reverb_decay=0.0)
        muestras, _, _, _ = leer_wav(self.salida)
        self.assertEqual(len(muestras), int(len(self.original) * 1.25),
                         "pitch=1.25 no dejo la onda un 25% mas larga")

    def test_11_un_wav_que_no_existe_devuelve_False_y_no_revienta(self):
        self.assertFalse(
            voz.aplicar_efectos(os.path.join(self.tmp.name, "no_esta.wav"),
                                self.salida),
            "un WAV ausente tenia que devolver False, no una excepcion")


class TestNuncaBloquea(unittest.TestCase):
    """Sin Piper, M3 se completa escribiendo. La voz no es un requisito."""

    def test_12_hablar_sin_piper_devuelve_None(self):
        antes = os.environ.get("AURELIUS_PIPER")
        os.environ["AURELIUS_PIPER"] = "/no/existe/piper"
        try:
            self.assertFalse(voz.piper_disponible())
            with tempfile.TemporaryDirectory() as d:
                self.assertIsNone(voz.hablar("hola", os.path.join(d, "x.wav")),
                                  "sin Piper, hablar() tiene que devolver None")
        finally:
            if antes is None:
                os.environ.pop("AURELIUS_PIPER", None)
            else:
                os.environ["AURELIUS_PIPER"] = antes

    def test_13_leitmotiv_que_no_esta_devuelve_None_y_sala_invalida_tambien(self):
        self.assertIsNone(voz.tocar_leitmotiv(99), "una sala que no existe dio ruta")
        for sala in range(1, 7):
            ruta = voz.tocar_leitmotiv(sala)
            if ruta is not None:
                self.assertTrue(os.path.isfile(ruta),
                                f"sala {sala}: se devolvio una ruta que no existe")


class TestVozReal(unittest.TestCase):
    """La unica mitad que puede saltarse. Y si se salta, dice por que."""

    def test_14_piper_genera_audio_de_verdad(self):
        if voz.piper_binario() == voz.NO_DATA:
            self.skipTest("no hay ejecutable de Piper: ni AURELIUS_PIPER ni "
                          "'piper' en el PATH. La voz es opcional por doctrina; "
                          "M3 se completa escribiendo.")
        if not os.path.isfile(voz.MODELO_DEFECTO):
            self.skipTest(f"falta el modelo de voz en {voz.MODELO_DEFECTO}. "
                          "Se baja en el arranque; sin el, Aurelius escribe.")
        with tempfile.TemporaryDirectory() as d:
            salida = os.path.join(d, "real.wav")
            ruta = voz.hablar("Prueba de la garganta.", salida)
            self.assertIsNotNone(ruta, "Piper esta y el modelo esta, pero no hubo audio")
            self.assertGreater(os.path.getsize(ruta), 44,
                               "el WAV generado no pasa de la cabecera")


if __name__ == "__main__":
    unittest.main(verbosity=2)
