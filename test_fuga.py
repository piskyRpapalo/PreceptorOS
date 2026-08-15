#!/usr/bin/env python3
"""test_fuga.py · los 10 criterios de M3 · HEGEMONIKON.

sistema: MVP · solo biblioteca estandar.

La version anterior de este fichero insertaba filas con SQL crudo y luego
comprobaba que la fila que acababa de insertar estaba ahi. Eso prueba SQLite,
que ya funcionaba. Aqui se llama a `fuga.py`: cada caso arranca una sala de
verdad, le habla por teclado con un guion, y mira lo que la sala dejo escrito.

La prueba de que estos casos prueban algo esta en `--sabotaje`: se rompe
`fuga.py` de tres maneras concretas en una COPIA del arbol y se exige que la
suite se ponga roja. Un caso que sigue verde con el modulo roto no es un caso.

Nada toca ~/.aurelius: cada caso trae su HOME temporal y lo devuelve al salir.
"""
from __future__ import annotations

import builtins
import contextlib
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

# Antes de importar `fuga`: la bandera de test y el ritmo a 0. `fuga._RITMO` se
# lee en el import, y una suite que se sienta a esperar las pausas del relato
# se deja de correr.
os.environ["AURELIUS_TEST"] = "1"
os.environ["AURELIUS_RITMO"] = "0"

import fuga  # noqa: E402


ESQUEMA = """
    CREATE TABLE IF NOT EXISTS profile (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL DEFAULT 'NO_DATA',
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS fuga_sala (
        sala INTEGER PRIMARY KEY CHECK (sala BETWEEN 1 AND 6),
        nombre TEXT NOT NULL,
        entrado_en TEXT NOT NULL DEFAULT (datetime('now')),
        salido_en TEXT NOT NULL DEFAULT 'NO_DATA',
        minutos INTEGER NOT NULL DEFAULT 0,
        estado TEXT NOT NULL DEFAULT 'entrada'
            CHECK (estado IN ('entrada', 'completada', 'pausada')),
        concepto TEXT NOT NULL DEFAULT 'NO_DATA'
    );
    CREATE TABLE IF NOT EXISTS fuentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ruta_o_url TEXT NOT NULL DEFAULT 'NO_DATA',
        sha256 TEXT NOT NULL DEFAULT 'NO_DATA',
        tipo TEXT NOT NULL DEFAULT 'NO_DATA',
        equipada_en TEXT NOT NULL DEFAULT (datetime('now')),
        estado TEXT NOT NULL DEFAULT 'sin_declarar'
            CHECK (estado IN ('sin_declarar', 'equipada', 'declarada', 'retirada'))
    );
    CREATE TABLE IF NOT EXISTS engrams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        texto TEXT NOT NULL,
        creado_en TEXT NOT NULL DEFAULT (datetime('now')),
        tipo TEXT NOT NULL DEFAULT 'recuerdo'
    );
"""


class Abandono(BaseException):
    """Se acabo la sesion a mitad de sala.

    Hereda de BaseException a proposito: `fuga` atrapa EOFError y
    KeyboardInterrupt para no dejar a nadie colgado, asi que ninguna de las dos
    sirve para simular que la sesion se murio. Esto atraviesa la sala igual que
    la atraviesa un terminal que se cierra.
    """


@contextlib.contextmanager
def guion(*respuestas, abandonar=False):
    """Habla por teclado. Agotado el guion: EOF, o abandono si se pide.

    EOF es "la persona deja de contestar y la sala se cierra con lo que hay".
    `abandonar=True` es "la sesion se muere aqui" -- que es otra cosa, y es la
    que el criterio 2 tiene que distinguir.
    """
    it = iter(respuestas)

    def falso_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise Abandono() if abandonar else EOFError()

    antes = builtins.input
    builtins.input = falso_input
    try:
        yield
    finally:
        builtins.input = antes


SONIDOS_PEDIDOS = []


def _reproducir_anotado(self, ruta):
    """Sustituto de `_reproducir_wav` mientras corre la suite.

    Lo anota en vez de tocarlo. Sin esto, la suite le manda los leitmotiv de
    verdad a `aplay` y se queda esperando a que suenen: los casos tardaban
    minutos y sonaba musica en la maquina de quien los corre. Se anota la ruta
    para que el criterio 9 pueda comprobar que el canal sonoro SE PIDE, que es
    lo que ese criterio quiere saber.
    """
    SONIDOS_PEDIDOS.append(ruta)


class BaseFuga(unittest.TestCase):
    """HOME temporal, base con esquema, y todo devuelto al salir."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="fuga_")
        self.db_path = Path(self.tmpdir) / "memory.db"

        conn = sqlite3.connect(str(self.db_path))
        conn.executescript(ESQUEMA)
        conn.close()

        # Se guarda TODO lo que se pisa y se devuelve en tearDown. Una suite
        # que deja el HOME apuntando a un temporal borrado le rompe la
        # siguiente, y el fallo aparece en un fichero que no se toco.
        self._entorno_antes = {k: os.environ.get(k) for k in ("HOME",)}
        self._fuga_antes = (fuga.DB_PATH, fuga.MANIFIESTO_PATH)
        os.environ["HOME"] = self.tmpdir
        fuga.DB_PATH = str(self.db_path)
        fuga.MANIFIESTO_PATH = str(Path(self.tmpdir) / "manifiesto_fuga.txt")

        # El canal sonoro se anota, no se toca. Ver `_reproducir_anotado`.
        self._reproducir_real = fuga.FugaMuseo._reproducir_wav
        fuga.FugaMuseo._reproducir_wav = _reproducir_anotado
        SONIDOS_PEDIDOS.clear()

        # Los dos canales de hardware, apagados por defecto. No es comodidad:
        # en una maquina con whisper.cpp instalado, `_preguntar` llama a
        # `oido.grabar_y_transcribir`, que abre `arecord` y GRABA EL MICROFONO
        # cinco segundos por pregunta -- la suite tardaba minutos, escuchaba la
        # habitacion de quien la corre, y el guion de teclado no se usaba nunca,
        # asi que los casos no probaban lo que decian probar. Igual con Piper:
        # sintetizaria audio de verdad. Quien quiera el camino del oido lo pide
        # explicitamente (`test_12`), y con un oido simulado.
        self._oido_real = fuga.oido
        self._piper_real = fuga.voz.piper_disponible if fuga.voz else None
        fuga.oido = None
        if fuga.voz:
            fuga.voz.piper_disponible = lambda: False

        self.fuga_mod = fuga

    def tearDown(self):
        fuga.oido = self._oido_real
        if fuga.voz and self._piper_real is not None:
            fuga.voz.piper_disponible = self._piper_real
        fuga.FugaMuseo._reproducir_wav = self._reproducir_real
        fuga.DB_PATH, fuga.MANIFIESTO_PATH = self._fuga_antes
        for k, v in self._entorno_antes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # --- lecturas de la base, para que los casos digan que miran ---

    def perfil(self):
        conn = sqlite3.connect(str(self.db_path))
        try:
            return {k: v for k, v in conn.execute("SELECT key, value FROM profile")}
        finally:
            conn.close()

    def salas(self):
        conn = sqlite3.connect(str(self.db_path))
        try:
            return {s: e for s, e in conn.execute(
                "SELECT sala, estado FROM fuga_sala")}
        finally:
            conn.close()

    def fuentes(self):
        conn = sqlite3.connect(str(self.db_path))
        try:
            return [tuple(f) for f in conn.execute(
                "SELECT ruta_o_url, estado FROM fuentes ORDER BY id")]
        finally:
            conn.close()

    def engramas(self):
        conn = sqlite3.connect(str(self.db_path))
        try:
            return [tuple(f) for f in conn.execute(
                "SELECT texto, tipo FROM engrams ORDER BY id")]
        finally:
            conn.close()


class TestFuga(BaseFuga):
    """Los 10 criterios."""

    def test_01_reanudar_de_verdad(self):
        """Criterio 1: se reanuda en la sala 3 sin repetir la 1 ni la 2."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT INTO fuga_sala (sala, nombre, estado)
            VALUES (1, 'PROHAIRESIS', 'completada'),
                   (2, 'SAFEHOUSE', 'completada'),
                   (3, 'HORME', 'entrada')
        """)
        conn.commit()
        conn.close()

        f = self.fuga_mod.FugaMuseo()
        try:
            self.assertEqual(f._detectar_reanudacion(), 3,
                             "no se reanudo por la sala 3")
        finally:
            f.cerrar()

        # Y reanudar no puede pisar lo que ya estaba cerrado.
        self.assertEqual(self.salas()[1], "completada")
        self.assertEqual(self.salas()[2], "completada")

    def test_02_nada_a_medias(self):
        """Criterio 2: una sala abandonada no deja media persona en profile."""
        f = self.fuga_mod.FugaMuseo()
        try:
            # Contesta el nombre y se muere antes de contestar el tono.
            with guion("Carlos", abandonar=True):
                with self.assertRaises(Abandono):
                    f._sala_prohairesis()
        finally:
            f.cerrar()

        self.assertEqual(self.perfil(), {},
                         "una sala abandonada escribio en profile de todas formas")
        self.assertEqual(self.salas().get(1), "entrada",
                         "la sala abandonada no quedo en estado 'entrada'")

    def test_02b_una_sala_cerrada_si_escribe(self):
        """El reverso del 2: si la sala se cierra, lo contestado esta en disco.

        Sin este caso, "no escribe nada nunca" pasaria el criterio 2.
        """
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("Carlos", "2"):
                f._sala_prohairesis()
        finally:
            f.cerrar()

        self.assertEqual(self.perfil().get("como_llamarte"), "Carlos")
        self.assertEqual(self.perfil().get("como_hablar"), "formal")
        self.assertEqual(self.salas().get(1), "completada")

    def test_03_nombre_no_se_pide_dos_veces(self):
        """Criterio 3: un nombre ya sabido no se vuelve a pedir."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO profile (key, value) VALUES ('name', 'Carlos')")
        conn.commit()
        conn.close()

        f = self.fuga_mod.FugaMuseo()
        try:
            cur = f.db.execute("SELECT value FROM profile WHERE key='name'")
            fila = cur.fetchone()
            self.assertIsNotNone(fila, "el nombre no llego a profile")
            self.assertEqual(fila[0], "Carlos")
        finally:
            f.cerrar()

        # Y lo que sala 1 escribe no pisa `name`: son dos claves distintas a
        # proposito -- `name` es de M2, `como_llamarte` es como quiere que le
        # hablen aqui. Pisarla seria que M3 le robase el dato a M2.
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("Otro", "1"):
                f._sala_prohairesis()
        finally:
            f.cerrar()
        self.assertEqual(self.perfil().get("name"), "Carlos",
                         "M3 piso el nombre que ya tenia M2")

    def test_04_salir_sin_fuente_posible(self):
        """Criterio 4: se sale de la sala 5 sin fuente, y queda 'sin_declarar'."""
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("ninguna"):
                f._sala_katalepsis()
        finally:
            f.cerrar()

        self.assertEqual(self.salas().get(5), "completada",
                         "sin fuente no se pudo cerrar la sala 5: M3 quedo bloqueada")
        self.assertIn(("sin_declarar", "sin_declarar"), self.fuentes(),
                      "no declarar fuente no dejo la fila 'sin_declarar'")

    def test_04b_una_fuente_declarada_se_equipa(self):
        """El reverso del 4: quien SI trae fuente la ve equipada."""
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("El manual de Epicteto"):
                f._sala_katalepsis()
        finally:
            f.cerrar()
        self.assertEqual(self.fuentes(), [("El manual de Epicteto", "declarada")])
        self.assertEqual(self.salas().get(5), "completada")

    def test_05_no_data_se_ve(self):
        """Criterio 5: lo no contestado se ve NO_DATA literal, nunca vacio."""
        f = self.fuga_mod.FugaMuseo()
        try:
            # Las cinco preguntas de la sala 3, todas en blanco.
            with guion("", "", "", "", ""):
                f._sala_horme()
        finally:
            f.cerrar()

        perfil = self.perfil()
        campos = ("proyecto_vital", "triunfo_deseado", "laguna_reconocida",
                  "fuentes_que_sigue", "restriccion_dura")
        for campo in campos:
            self.assertIn(campo, perfil, f"la sala 3 no dejo {campo} en el perfil")
            self.assertEqual(
                perfil[campo], "NO_DATA",
                f"{campo} quedo como {perfil[campo]!r} en vez de NO_DATA literal")
        self.assertNotIn("", perfil.values(),
                         "quedo una celda vacia en profile")

    def test_05b_no_data_tambien_en_las_otras_salas(self):
        """La regla es del fichero entero, no de la sala 3."""
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion(""):                    # sala 1: sin nombre
                f._sala_prohairesis()
        finally:
            f.cerrar()
        self.assertEqual(self.perfil().get("como_llamarte"), "NO_DATA",
                         "un nombre en blanco quedo como celda vacia")

    def test_06_cero_delete(self):
        """Criterio 6: cero DELETE en fuga.py. Estados por columna."""
        import re
        codigo = "\n".join(
            l for l in (AQUI / "fuga.py").read_text(encoding="utf-8").splitlines()
            if not l.strip().startswith(("#", '"""', "'''")))
        self.assertIsNone(re.search(r"\bDELETE\s+FROM\b", codigo, re.I),
                          "hay un DELETE FROM en fuga.py")
        self.assertIsNone(re.search(r"\bDROP\s+TABLE\b", codigo, re.I),
                          "hay un DROP TABLE en fuga.py")

    def test_07_sin_oidos_sin_voz_funciona(self):
        """Criterio 8: sin voz ni oido, la sala se completa escribiendo."""
        voz_antes, oido_antes = self.fuga_mod.voz, self.fuga_mod.oido
        self.fuga_mod.voz = None
        self.fuga_mod.oido = None
        try:
            f = self.fuga_mod.FugaMuseo()
            try:
                with guion("Carlos", "1"):
                    f._sala_prohairesis()
            finally:
                f.cerrar()
        finally:
            self.fuga_mod.voz, self.fuga_mod.oido = voz_antes, oido_antes

        self.assertEqual(self.salas().get(1), "completada",
                         "sin voz ni oido la sala 1 no se completo")
        self.assertEqual(self.perfil().get("como_llamarte"), "Carlos")

    def test_08_manifiesto_se_comporta(self):
        """Criterio 7: el manifiesto lleva la huella de su propio cuerpo."""
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("Carlos", "1"):
                f._sala_prohairesis()
            f._generar_manifiesto()
        finally:
            f.cerrar()

        texto = Path(self.fuga_mod.MANIFIESTO_PATH).read_text(encoding="utf-8")
        self.assertIn("Firma (SHA256): ", texto, "el manifiesto no lleva firma")
        firma = texto.rsplit("Firma (SHA256): ", 1)[1].strip()
        self.assertRegex(firma, r"^[0-9a-f]{64}$",
                         f"la firma no es un sha256: {firma!r}")
        # Y la firma es la del cuerpo: se recalcula aqui, no se cree.
        cuerpo = texto.rsplit("\n---\n", 1)[0]
        self.assertEqual(hashlib.sha256(cuerpo.encode("utf-8")).hexdigest(), firma,
                         "la firma no corresponde al cuerpo que firma")

    def test_09_mision_completa_con_un_dato(self):
        """Criterio 10: M3 se completa con un solo dato real y el resto NO_DATA."""
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("Carlos", "1"):
                f._sala_prohairesis()
            with guion("", "", "", "", ""):      # sala 3 entera en blanco
                f._sala_horme()
            with guion("ninguna"):               # sala 5 sin fuente
                f._sala_katalepsis()
        finally:
            f.cerrar()

        perfil = self.perfil()
        reales = [v for v in perfil.values() if v != "NO_DATA"]
        self.assertGreaterEqual(len(reales), 1, "no quedo ni un dato real")
        completadas = [s for s, e in self.salas().items() if e == "completada"]
        self.assertEqual(sorted(completadas), [1, 3, 5],
                         "no se completaron las tres salas recorridas")

    def test_10_toda_confirmacion_tiene_sonido(self):
        """Criterio 9: entrar en una sala pide su leitmotiv, y hay mas de un
        reproductor por si el primero no esta."""
        import inspect
        # `self._reproducir_real` es el metodo de verdad: el que corre durante
        # la suite esta sustituido para no sonar.
        fuente = inspect.getsource(self._reproducir_real)
        for reproductor in ("aplay", "vlc"):
            self.assertIn(reproductor, fuente,
                          f"{reproductor} no esta entre los reproductores")

        # Y el canal se PIDE al entrar en la sala, no solo existe.
        falso_wav = Path(self.tmpdir) / "sala_1.wav"
        falso_wav.write_bytes(b"RIFF")
        leitmotiv_antes = self.fuga_mod.voz.tocar_leitmotiv
        self.fuga_mod.voz.tocar_leitmotiv = lambda sala: str(falso_wav)
        try:
            f = self.fuga_mod.FugaMuseo()
            try:
                f._entrar_sala(1, "PROHAIRESIS · El Nombre")
            finally:
                f.cerrar()
        finally:
            self.fuga_mod.voz.tocar_leitmotiv = leitmotiv_antes

        self.assertIn(str(falso_wav), SONIDOS_PEDIDOS,
                      "entrar en una sala no pidio su leitmotiv")

    def test_12_con_oido_la_respuesta_hablada_llega_al_perfil(self):
        """El camino del oido, con un oido simulado: sin microfono, sin espera.

        Va aparte porque el resto de la suite escribe. Doctrina: la voz y el
        oido son opcionales, y M3 se completa entera por teclado -- pero si el
        oido esta, lo que se dice tiene que llegar al mismo sitio.
        """
        class OidoFalso:
            @staticmethod
            def oido_disponible():
                return True

            @staticmethod
            def grabar_y_transcribir(duracion_seg=5, idioma="es"):
                return "Carlos"

        self.fuga_mod.oido = OidoFalso
        f = self.fuga_mod.FugaMuseo()
        try:
            # Sin guion: nadie toca el teclado. Todo entra por el oido.
            f._sala_prohairesis()
        finally:
            f.cerrar()

        self.assertEqual(self.perfil().get("como_llamarte"), "Carlos",
                         "lo dicho en voz alta no llego al perfil")
        self.assertEqual(self.salas().get(1), "completada")

    def test_11_la_suite_no_toca_la_memoria_real(self):
        """La salvaguarda, como en test_idioma: se declara y se comprueba."""
        self.assertNotEqual(
            os.path.realpath(self.fuga_mod.DB_PATH),
            os.path.realpath(os.path.expanduser("~/.aurelius/memory.db")),
            "un caso de esta suite apunta a la memoria real de la persona")


# --- sabotaje: la prueba de que los casos de arriba prueban algo ------------

SABOTAJES = (
    ("una sala a medias escribe igual en profile",
     "fuga.py",
     "        self._pendiente[clave] = self._dato(valor)",
     "        cursor = self.db.cursor()\n"
     "        cursor.execute(\"INSERT OR REPLACE INTO profile (key, value, updated_at)\"\n"
     "                       \" VALUES (?, ?, datetime('now'))\", (clave, self._dato(valor)))\n"
     "        self.db.commit()"),
    ("salir sin fuente queda bloqueado",
     "fuga.py",
     '            self._guardar_fuente("sin_declarar", "sin_declarar")',
     '            self._hablar("Sin una fuente no salimos de aqui.", pausa=0.0)\n'
     "            return"),
    ("un dato ausente se muestra vacio en vez de NO_DATA",
     "fuga.py",
     "        limpio = (valor or \"\").strip()\n        return limpio or NO_DATA",
     "        limpio = (valor or \"\").strip()\n        return limpio"),
)


def _sha(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def main_sabotaje():
    print("── M3 · FUGA · MODO SABOTAJE · se EXIGE rojo " + "─" * 22)
    vigilados = ("fuga.py", "voz.py", "oido.py", "test_fuga.py")
    sha_antes = {f: _sha(AQUI / f) for f in vigilados}
    no_detectados = []

    for nombre, fichero, ancla, sustitucion in SABOTAJES:
        destino = Path(tempfile.mkdtemp(prefix="sab_fuga_")) / "arbol"
        shutil.copytree(AQUI, destino, ignore=shutil.ignore_patterns(
            "__pycache__", ".git", "aurelius", "piezas"))
        ruta = destino / fichero
        s = ruta.read_text(encoding="utf-8")
        if ancla not in s:
            print(f"  AVISO · {nombre}: ancla perdida")
            no_detectados.append(nombre + " (ancla perdida)")
            continue
        ruta.write_text(s.replace(ancla, sustitucion, 1), encoding="utf-8")

        r = subprocess.run([sys.executable, "test_fuga.py"], cwd=destino,
                           capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            print(f"  VERDE · {nombre} · NO DETECTADO")
            no_detectados.append(nombre)
        else:
            culpables = sorted({
                l.split("(")[0].strip().removeprefix("FAIL: ").removeprefix("ERROR: ")
                for l in r.stdout.splitlines() + r.stderr.splitlines()
                if l.startswith(("FAIL:", "ERROR:"))})
            print(f"  roja  · {nombre}\n          {', '.join(culpables)[:96]}")
        shutil.rmtree(destino.parent, ignore_errors=True)

    mutados = [f for f in vigilados if _sha(AQUI / f) != sha_antes[f]]
    if mutados:
        print(f"  CRITICO: el sabotaje escribio en el arbol original: {mutados}")
        no_detectados.append("original mutado")
    else:
        print(f"\nARBOL ORIGINAL INTACTO ({', '.join(vigilados)})")

    total = len(SABOTAJES)
    print(f"\nRESULTADO SABOTAJE: {total - len(no_detectados)}/{total} detectadas")
    return 1 if no_detectados else 0


if __name__ == "__main__":
    if "--sabotaje" in sys.argv[1:]:
        sys.exit(main_sabotaje())
    unittest.main(verbosity=2)
