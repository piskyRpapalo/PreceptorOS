#!/usr/bin/env python3
"""M3 · el generador de leitmotivs es determinista, o no sirve de nada.

sistema: MVP · solo biblioteca estandar.

El generador viaja con el repo en vez de los seis WAV para que un clon pese
poco y suene igual. La segunda mitad de esa frase es la que hay que probar:
hasta D78 el ruido salia de `hash(str(i))`, aleatorizado por proceso, y dos
ejecuciones daban huellas distintas. Aqui se exige la huella, como en
`descarga.py`: mismo nombre -> mismo sha256, en este proceso y en otro.

Ninguna prueba escribe en ~/.aurelius/ real: todas trabajan en un tmpdir y el
caso 00 lo comprueba mirando el import, que es donde estaba el agujero.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
import wave

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import generar_leitmotivs as G  # noqa: E402


def huella(ruta):
    with open(ruta, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class TestNoTocaLaCasa(unittest.TestCase):

    def test_00_importar_el_modulo_no_escribe_en_la_casa_de_nadie(self):
        """El agujero de D78: `os.makedirs` al nivel del modulo.

        Se prueba en un proceso aparte con HOME temporal, que es la unica
        forma honesta: en este ya esta importado.
        """
        with tempfile.TemporaryDirectory() as home:
            entorno = dict(os.environ, HOME=home)
            entorno.pop("AURELIUS_TEST", None)
            r = subprocess.run(
                [sys.executable, "-c", "import generar_leitmotivs"],
                cwd=AQUI, env=entorno, capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(
                os.path.exists(os.path.join(home, ".aurelius")),
                "importar el generador creo la casa de la persona")

    def test_01_el_directorio_por_defecto_se_calcula_al_llamar(self):
        antes = os.environ.get("HOME")
        with tempfile.TemporaryDirectory() as home:
            os.environ["HOME"] = home
            try:
                self.assertTrue(G.directorio_defecto().startswith(home),
                                "el destino se congelo en el import")
            finally:
                if antes is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = antes


class TestDeterminismo(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.destino = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_02_dos_generaciones_seguidas_dan_la_misma_huella(self):
        G.generar_todos(self.destino, forzar=True)
        primera = {n: huella(os.path.join(self.destino, f"{n}.wav"))
                   for n, _, _ in G.LEITMOTIVS}
        G.generar_todos(self.destino, forzar=True)
        segunda = {n: huella(os.path.join(self.destino, f"{n}.wav"))
                   for n, _, _ in G.LEITMOTIVS}
        self.assertEqual(primera, segunda,
                         "el generador no es determinista dentro del proceso")

    def test_03_otro_proceso_con_otra_semilla_de_hash_da_la_misma_huella(self):
        """El caso que D78 fallaba. PYTHONHASHSEED distinto en cada rama.

        Si el ruido volviera a salir de `hash()`, estas dos huellas
        divergirian y el clon de otra persona sonaria distinto.
        """
        guion = (
            "import sys, hashlib, generar_leitmotivs as G;"
            "d = sys.argv[1];"
            "G.generar_todos(d, forzar=True);"
            "print('\\n'.join(n + ' ' + hashlib.sha256("
            "open(d + '/' + n + '.wav','rb').read()).hexdigest()"
            " for n, _, _ in G.LEITMOTIVS))"
        )
        salidas = []
        for semilla in ("0", "1", "12345"):
            with tempfile.TemporaryDirectory() as d:
                r = subprocess.run(
                    [sys.executable, "-c", guion, d], cwd=AQUI,
                    env=dict(os.environ, PYTHONHASHSEED=semilla),
                    capture_output=True, text=True, timeout=120)
                self.assertEqual(r.returncode, 0, r.stderr)
                salidas.append(r.stdout.strip())
        self.assertEqual(len(set(salidas)), 1,
                         "PYTHONHASHSEED cambia los sonidos: el generador "
                         "sigue dependiendo de hash()\n" + "\n--\n".join(salidas))

    def test_04_el_codigo_no_llama_a_hash(self):
        """La causa, no solo el sintoma: una llamada a `hash()` es reincidir.

        Se mira el arbol sintactico, no el texto. Un grep tambien encuentra la
        palabra en la prosa que explica por que no hay que usarla -- este caso
        se puso rojo la primera vez por su propio docstring. Lo que se prohibe
        es LLAMARLA, y eso solo lo sabe el parser.
        """
        import ast
        with open(os.path.join(AQUI, "generar_leitmotivs.py"), encoding="utf-8") as fh:
            arbol = ast.parse(fh.read())
        llamadas = [n for n in ast.walk(arbol)
                    if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == "hash"]
        self.assertEqual(
            [n.lineno for n in llamadas], [],
            "el generador vuelve a llamar a hash(): es la funcion cuyo "
            "resultado cambia con PYTHONHASHSEED")

    def test_05_las_seis_huellas_son_distintas_entre_si(self):
        G.generar_todos(self.destino, forzar=True)
        huellas = {n: huella(os.path.join(self.destino, f"{n}.wav"))
                   for n, _, _ in G.LEITMOTIVS}
        self.assertEqual(len(set(huellas.values())), 6,
                         f"dos salas suenan exactamente igual: {huellas}")


class TestOndas(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.destino = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def pico(self, nombre, frecuencias, tipo):
        return max(abs(m) for m in G._muestras(nombre, frecuencias, tipo))

    def test_06_la_sala_5_no_suena_al_doble_que_las_demas(self):
        """El bucle de mas: 'ascendente' sumaba un barrido por frecuencia.

        Con dos frecuencias eso era exactamente el doble de amplitud. Se
        compara contra el mismo barrido declarando UNA sola frecuencia: si el
        bucle volviera, la version de dos frecuencias picaria mas alto.
        """
        una = self.pico("sala_5_katalepsis", (440,), "ascendente")
        dos = self.pico("sala_5_katalepsis", (440, 660), "ascendente")
        self.assertLess(abs(dos - una) / max(una, 1), 0.35,
                        f"el barrido se suma mas de una vez: {una} vs {dos}")

    def test_07_ninguna_sala_satura(self):
        for nombre, frecuencias, tipo in G.LEITMOTIVS:
            pico = self.pico(nombre, frecuencias, tipo)
            self.assertLessEqual(pico, 32767, f"{nombre} se sale del rango")
            self.assertGreater(pico, 1000, f"{nombre} sale practicamente mudo")

    def test_08_los_seis_wav_son_wav_de_verdad(self):
        G.generar_todos(self.destino, forzar=True)
        for nombre, _, _ in G.LEITMOTIVS:
            ruta = os.path.join(self.destino, f"{nombre}.wav")
            with wave.open(ruta, "rb") as w:
                self.assertEqual(w.getframerate(), G.FRAMERATE, nombre)
                self.assertEqual(w.getnchannels(), 1, nombre)
                self.assertEqual(w.getsampwidth(), 2, nombre)
                self.assertGreater(w.getnframes(), 0, nombre)

    def test_09_los_nombres_son_los_que_voz_sabe_tocar(self):
        """Si esta tabla y la de `voz.tocar_leitmotiv` divergen, M3 enmudece
        sin decir nada: `tocar_leitmotiv` devuelve None y no es un error."""
        import voz
        antes = voz.SONIDOS_DIR
        voz.SONIDOS_DIR = self.destino
        try:
            G.generar_todos(self.destino, forzar=True)
            for sala in range(1, 7):
                self.assertIsNotNone(
                    voz.tocar_leitmotiv(sala),
                    f"voz no encuentra el leitmotiv de la sala {sala}: los "
                    "nombres del generador y los de voz.py no coinciden")
        finally:
            voz.SONIDOS_DIR = antes


class TestAsegurar(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.destino = os.path.join(self.tmp.name, "sonidos")

    def tearDown(self):
        self.tmp.cleanup()

    def test_10_asegurar_genera_los_que_faltan_y_solo_esos(self):
        self.assertEqual(len(G.asegurar(self.destino)), 6,
                         "la primera vez tienen que salir los seis")
        self.assertEqual(G.faltan(self.destino), [])
        self.assertEqual(G.asegurar(self.destino), [],
                         "la segunda vez no hay que regenerar nada")

    def test_11_si_falta_uno_solo_se_repone_ese(self):
        G.generar_todos(self.destino, forzar=True)
        os.unlink(os.path.join(self.destino, "sala_3_horme.wav"))
        self.assertEqual(G.faltan(self.destino), ["sala_3_horme"])
        hechos = G.asegurar(self.destino)
        self.assertEqual([os.path.basename(h) for h in hechos],
                         ["sala_3_horme.wav"])

    def test_12_un_destino_imposible_no_levanta(self):
        """Doctrina: la musica es adorno del relato. Nunca bloquea M3."""
        self.assertEqual(G.asegurar("/proc/no/se/puede/escribir/aqui"), [],
                         "asegurar() levanto en vez de seguir en silencio")


if __name__ == "__main__":
    unittest.main(verbosity=2)
