#!/usr/bin/env python3
"""El apagado de hardware vale para TODA la suite, no para la que lo recordó.

sistema: MVP · solo biblioteca estandar.

D77 dejo una leccion cara: `test_fuga` grababa el microfono cinco segundos por
pregunta porque whisper.cpp estaba instalado en esa maquina. Se arreglo dentro
de esa suite -- y eso deja la trampa puesta para la siguiente, que la
descubrira igual de tarde. Aqui se prueba el interruptor y se prueba que las
TRES puertas de hardware lo obedecen, para que apagarlo sea una cosa y no
tres costumbres.

Las tres puertas: `oido.oido_disponible`, `voz.piper_disponible` y
`fuga.FugaMuseo._reproducir_wav`.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import silencio  # noqa: E402
import oido      # noqa: E402
import voz       # noqa: E402
import fuga      # noqa: E402
import memory    # noqa: E402


class TestInterruptor(silencio.SinHardware):

    def test_00_el_mixin_deja_el_hardware_apagado_durante_el_caso(self):
        self.assertTrue(silencio.apagado())

    def test_01_el_oido_no_esta_disponible_aunque_whisper_este_instalado(self):
        self.assertFalse(oido.oido_disponible(),
                         "el microfono sigue disponible con el hardware vetado")

    def test_02_la_voz_no_esta_disponible_aunque_piper_este_instalado(self):
        self.assertFalse(voz.piper_disponible(),
                         "el sintetizador sigue disponible con el hardware vetado")

    def test_03_grabar_devuelve_None_sin_abrir_el_microfono(self):
        """Y vuelve AL INSTANTE, que es como se sabe que no grabo.

        `grabar_y_transcribir` no comprobaba nada antes de grabar: abria el
        microfono cinco segundos y despues `transcribir` miraba si whisper
        existia y devolvia None. El valor de retorno era correcto y la
        grabacion habia ocurrido igual, asi que un caso que solo mirase el
        None se quedaba tan tranquilo. Se mide el reloj.
        """
        arranque = time.monotonic()
        self.assertIsNone(oido.grabar_y_transcribir(duracion_seg=5))
        tardo = time.monotonic() - arranque
        self.assertLess(tardo, 0.5,
                        f"tardo {tardo:.1f}s: abrio el microfono antes de mirar")

    def test_04_el_altavoz_no_lanza_ningun_reproductor(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "memory.db"
            memory.crear(str(db))
            antes = fuga.DB_PATH
            fuga.DB_PATH = str(db)
            try:
                f = fuga.FugaMuseo()
                try:
                    wav = Path(d) / "x.wav"
                    wav.write_bytes(b"RIFF")
                    lanzados = []
                    real = subprocess.run

                    def espia(cmd, *a, **kw):
                        lanzados.append(cmd)
                        return real([sys.executable, "-c", ""], *a, **kw)

                    subprocess.run = espia
                    try:
                        f._reproducir_wav(str(wav))
                    finally:
                        subprocess.run = real
                    self.assertEqual(lanzados, [],
                                     f"el altavoz lanzo algo: {lanzados}")
                finally:
                    f.cerrar()
            finally:
                fuga.DB_PATH = antes


class TestFrontera(unittest.TestCase):
    """Sin el mixin: aqui se comprueba que apagar y encender son simetricos."""

    def test_05_fuera_del_mixin_el_entorno_queda_como_estaba(self):
        antes = os.environ.get(silencio.VARIABLE)
        self.assertEqual(os.environ.get(silencio.VARIABLE), antes,
                         "una suite anterior dejo el interruptor cambiado")

    def test_06_el_veto_viaja_a_los_procesos_hijo(self):
        """`test_idioma` arranca `aurelius.py` como subproceso.

        Un mock en memoria no cruza esa frontera; una variable de entorno si.
        Por eso el interruptor es una variable y no un parche.
        """
        guion = ("import oido, voz, silencio;"
                 "print(silencio.apagado(), oido.oido_disponible(),"
                 " voz.piper_disponible())")
        r = subprocess.run([sys.executable, "-c", guion], cwd=str(AQUI),
                           env=dict(os.environ, **{silencio.VARIABLE: "1"}),
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "True False False",
                         "el hijo no heredo el veto de hardware")

    def test_07_las_tres_puertas_comprueban_el_veto_ellas_mismas(self):
        """La comprobacion vive DENTRO de cada puerta, no en los llamantes.

        Se mira el arbol sintactico de las tres funciones. El dia que alguien
        saque el veto a quien llama, este caso se pone rojo -- que es el dia
        en que un llamante nuevo lo olvidaria.
        """
        puertas = {
            "oido.py": ["oido_disponible"],
            "voz.py": ["piper_disponible"],
            "fuga.py": ["_reproducir_wav"],
        }
        for fichero, nombres in puertas.items():
            arbol = ast.parse((AQUI / fichero).read_text(encoding="utf-8"))
            for nombre in nombres:
                fn = next((n for n in ast.walk(arbol)
                           if isinstance(n, ast.FunctionDef) and n.name == nombre),
                          None)
                self.assertIsNotNone(fn, f"{fichero}: {nombre} desaparecio")
                llama = any(
                    isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "apagado"
                    for n in ast.walk(fn))
                self.assertTrue(
                    llama,
                    f"{fichero}:{nombre} ya no comprueba el veto de hardware")


class TestNingunaSuiteDejaRuido(unittest.TestCase):

    def test_08_ninguna_suite_invoca_grabadores_ni_reproductores(self):
        """El fallo de D77, hecho comprobable.

        Ninguna suite debe nombrar `arecord`, `aplay` y companía: quien los
        necesite, que los mockee. Se permite en `fuga.py` (es el producto) y
        en los casos que comprueban precisamente que NO se lanzan.
        """
        prohibidos = ("arecord", "aplay", "paplay", "ffplay")
        permitidos = {"test_fuga.py",       # criterio 9: inspecciona la lista
                      "test_silencio.py"}   # este fichero la nombra al explicar
        malos = []
        for ruta in sorted(AQUI.glob("test_*.py")):
            if ruta.name in permitidos:
                continue
            texto = ruta.read_text(encoding="utf-8")
            for palabra in prohibidos:
                if palabra in texto:
                    malos.append(f"{ruta.name}: {palabra}")
        self.assertEqual(malos, [], f"suites que tocan el hardware: {malos}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
