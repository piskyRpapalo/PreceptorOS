#!/usr/bin/env python3
"""test_fuga.py · los 10 criterios de M3 · HEGEMONIKON.

sistema: MVP · solo biblioteca estandar.

La version anterior de este fichero insertaba filas con SQL crudo y luego
comprobaba que la fila que acababa de insertar estaba ahi. Eso prueba SQLite,
que ya funcionaba. Aqui se llama a `fuga.py`: cada caso arranca una sala de
verdad, le habla por teclado con un guion, y mira lo que la sala dejo escrito.

La prueba de que estos casos prueban algo esta en `--sabotaje`: se rompe
`fuga.py` de seis maneras concretas en una COPIA del arbol y se exige que la
suite se ponga roja. Un caso que sigue verde con el modulo roto no es un caso.

Tampoco se fabrica el esquema. Lo ponen `memory.crear` (M2) y
`FugaMuseo.__init__` (M3), como en casa de la persona -- ver el comentario de
abajo, que cuenta lo que la copia inventada estuvo tapando.

Nada toca ~/.aurelius: cada caso trae su HOME temporal y lo devuelve al salir.
"""
from __future__ import annotations

import builtins
import contextlib
import hashlib
import io
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

import fuga     # noqa: E402
import memory   # noqa: E402


# Aqui NO hay esquema. Lo habia -- una copia entera de las cuatro tablas en el
# setUp -- y esa copia era el problema: la suite fabricaba las tablas que iba a
# comprobar, asi que no podia notar que `fuga.py` no las creaba en ningun sitio.
# En una maquina limpia M3 reventaba con "no such table: fuga_sala", y la suite
# estaba verde. Ahora `memory.crear` pone las de M2 y `FugaMuseo.__init__` pone
# las de M3, que es exactamente lo que pasa en casa de la persona.


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

        # Las tablas de M2 las hace M2. Las de M3 las hace M3, al conectarse.
        memory.crear(str(self.db_path))

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
                "SELECT what, origin FROM engrams ORDER BY id")]
        finally:
            conn.close()


class TestFuga(BaseFuga):
    """Los 10 criterios del Soberano, y lo que hizo falta para sostenerlos:
    D1 (parar al acabar cada sala), el permiso del gerente, la gramatica de
    las preguntas numeradas por voz, y el recorrido entero de punta a punta."""

    def test_00_el_numero_del_test_es_el_del_criterio(self):
        """El numero del metodo y el del criterio que declara son el mismo.

        Existe porque NO lo eran: `test_07` cubria el criterio 8, `test_08` el
        7, `test_09` el 10 y `test_10` el 9. Nada fallaba por eso -- los diez
        pasaban -- y precisamente por eso duro: solo se ve auditando, y quien
        auditase por el numero del metodo concluiria que faltan criterios que
        estan.

        Se comprueba por introspeccion y no con una lista escrita a mano: una
        lista es otra cosa mas que se puede desincronizar del arbol, y seria
        el mismo fallo con un fichero mas.
        """
        import inspect
        import re
        desajustes = []
        vistos = {}
        for nombre, metodo in inspect.getmembers(type(self), inspect.isfunction):
            m = re.fullmatch(r"test_(\d\d)_\w+", nombre)
            if not m:
                continue
            doc = inspect.getdoc(metodo) or ""
            d = re.match(r"Criterio (\d+):", doc)
            if not d:
                continue        # no declara criterio: no es uno de los diez
            n_test, n_crit = int(m.group(1)), int(d.group(1))
            if n_test != n_crit:
                desajustes.append(f"{nombre} declara «Criterio {n_crit}»")
            vistos[n_crit] = nombre
        self.assertEqual(desajustes, [], f"el numero no casa: {desajustes}")
        # Y que esten los diez: una renumeracion que borrase uno dejaria la
        # comprobacion de arriba en verde con nueve.
        self.assertEqual(sorted(vistos), list(range(1, 11)),
                         f"no estan los 10 criterios declarados: {sorted(vistos)}")

    def test_01_reanudar_de_verdad(self):
        """Criterio 1: se reanuda en la sala 3 sin repetir la 1 ni la 2.

        Las dos primeras salas se recorren DE VERDAD, no se insertan a mano.
        Un `INSERT` que fabrica el estado que luego se comprueba prueba que
        SQLite guarda lo que le metes; lo que hay que saber es si las salas
        dejan ese estado, y si al volver se entra por donde toca.
        """
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("Carlos", "1"):
                f._sala_prohairesis()
            with guion("2", "Debian"):
                f._sala_safehouse()
            # Se muere entrando en la 3.
            with guion(abandonar=True):
                with self.assertRaises(Abandono):
                    f._sala_horme()
        finally:
            f.cerrar()

        # Otra sesion, otra conexion: como volver al dia siguiente.
        f2 = self.fuga_mod.FugaMuseo()
        try:
            self.assertEqual(f2._detectar_reanudacion(), 3,
                             "no se reanudo por la sala 3")
        finally:
            f2.cerrar()

        # Y reanudar no pisa lo que ya estaba cerrado.
        self.assertEqual(self.salas()[1], "completada")
        self.assertEqual(self.salas()[2], "completada")
        self.assertEqual(self.perfil().get("como_llamarte"), "Carlos")

    def test_01b_las_tablas_de_m3_las_crea_m3(self):
        """En una base de M2 recien hecha, M3 no revienta: se hace su sitio.

        Este caso es el que faltaba. `fuga.py` no creaba estas tablas en
        ninguna parte -- funcionaba solo donde alguien las habia hecho a mano
        -- y la suite no lo veia porque las fabricaba ella en el setUp.
        """
        limpia = Path(self.tmpdir) / "recien_hecha.db"
        memory.crear(str(limpia))
        conn = sqlite3.connect(str(limpia))
        tablas = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        self.assertNotIn("fuga_sala", tablas, "M2 ya no deberia crear tablas de M3")

        self.fuga_mod.DB_PATH = str(limpia)
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("Carlos", "1"):
                f._sala_prohairesis()      # no puede levantar
        finally:
            f.cerrar()

        conn = sqlite3.connect(str(limpia))
        tablas = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        self.assertIn("fuga_sala", tablas)
        self.assertIn("fuentes", tablas)

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

    def test_08_sin_oidos_sin_voz_funciona(self):
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

    def test_07_manifiesto_se_comporta(self):
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

    def test_10_mision_completa_con_un_dato(self):
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

    def test_09_toda_confirmacion_tiene_sonido(self):
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
                # El nombre es pregunta abierta: vale cualquier cosa.
                # El tono es numerada: por voz tambien se dice un numero.
                return next(dichos, None)

        dichos = iter(["Carlos", "dos"])
        self.fuga_mod.oido = OidoFalso
        f = self.fuga_mod.FugaMuseo()
        try:
            # Sin guion: nadie toca el teclado. Todo entra por el oido.
            f._sala_prohairesis()
        finally:
            f.cerrar()

        self.assertEqual(self.perfil().get("como_llamarte"), "Carlos",
                         "lo dicho en voz alta no llego al perfil")
        self.assertEqual(self.perfil().get("como_hablar"), "formal",
                         "el numero dicho en voz alta no eligio la opcion")
        self.assertEqual(self.salas().get(1), "completada")

    # --- D1 · se ofrece parar al acabar cada sala -------------------------

    def test_13_los_minutos_son_medidos_o_son_menos_uno(self):
        """`minutos` es una medida. -1 es 'no medido', no 'cero minutos'."""
        f = self.fuga_mod.FugaMuseo()
        try:
            f._marcar_sala_entrada(2)          # entrada, nunca cerrada
            with guion("Carlos", "1"):
                f._sala_prohairesis()          # cerrada y medida
            filas = {r["sala"]: r["minutos"] for r in f.db.execute(
                "SELECT sala, minutos FROM fuga_sala")}
        finally:
            f.cerrar()
        self.assertEqual(filas[2], -1,
                         "una sala sin cerrar trae un tiempo que nadie midio")
        self.assertGreaterEqual(filas[1], 0,
                                "una sala cerrada no dejo medida")

    def test_14_sin_dos_medidas_no_se_habla_de_minutos(self):
        """D76 literal: no se muestra lo que no se puede medir.

        Nadie ha cruzado las seis salas. Con cero o una sala medida no hay
        media que dar, y lo que se dice es lo unico que se sabe: cuantas
        quedan.
        """
        for medidas in ([], [3]):
            frase = self.fuga_mod.texto_progreso(medidas, [4, 5, 6])
            self.assertIn("Quedan 3 salas", frase)
            self.assertNotIn("minuto", frase,
                             f"con {len(medidas)} medida(s) se hablo de tiempo: {frase!r}")

    def test_15_desde_la_tercera_el_tiempo_sale_de_sus_propias_salas(self):
        frase = self.fuga_mod.texto_progreso([2, 4], [4, 5, 6])
        self.assertIn("unos 3 minutos por sala", frase,
                      f"la media de 2 y 4 no salio como 3: {frase!r}")
        self.assertIn("Quedan 3 salas", frase)
        # Y sale de SUS salas: otra persona con otros tiempos oye otra cosa.
        self.assertIn("unos 9 minutos",
                      self.fuga_mod.texto_progreso([8, 10], [6]))

    def test_16_la_sala_larga_se_avisa_aparte(self):
        con = self.fuga_mod.texto_progreso([2, 4], [3, 4, 5, 6])
        sin = self.fuga_mod.texto_progreso([2, 4], [4, 5, 6])
        self.assertIn("La 3 es la larga", con)
        self.assertNotIn("La 3 es la larga", sin,
                         "se aviso de la sala 3 cuando ya estaba hecha")

    def test_17_parar_deja_la_siguiente_pausada_y_se_reanuda_por_ella(self):
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("Carlos", "1"):
                f._sala_prohairesis()
            with guion("2"):                  # 2 = "lo dejo por hoy"
                sigue = f._ofrecer_continuar(1)
        finally:
            f.cerrar()

        self.assertFalse(sigue, "dijo que paraba y la fuga siguio")
        self.assertEqual(self.salas().get(1), "completada",
                         "parar deshizo la sala que ya estaba cerrada")
        self.assertEqual(self.salas().get(2), "pausada")

        f2 = self.fuga_mod.FugaMuseo()
        try:
            self.assertEqual(f2._detectar_reanudacion(), 2,
                             "al volver no se entra por la sala pausada")
        finally:
            f2.cerrar()

    def test_18_seguir_no_marca_nada_ni_pierde_lo_hecho(self):
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("Carlos", "1"):
                f._sala_prohairesis()
            with guion("1"):                  # 1 = "seguimos"
                sigue = f._ofrecer_continuar(1)
        finally:
            f.cerrar()
        self.assertTrue(sigue)
        self.assertNotIn("pausada", self.salas().values())
        self.assertEqual(self.perfil().get("como_llamarte"), "Carlos")

    # --- el permiso del gerente -------------------------------------------

    def test_19_fila_ausente_es_no_y_no_es_un_error(self):
        f = self.fuga_mod.FugaMuseo()
        try:
            self.assertFalse(self.fuga_mod.permiso_concedido(f.db),
                             "sin fila, el permiso no salio 'no'")
            with self.assertRaises(self.fuga_mod.SinPermiso):
                self.fuga_mod.perfil_para_gerente(f.db)
        finally:
            f.cerrar()

    def test_20_solo_un_si_explicito_abre_la_puerta(self):
        f = self.fuga_mod.FugaMuseo()
        try:
            for valor, esperado in (("no", False), ("NO_DATA", False),
                                    ("", False), ("quiza", False),
                                    ("si", True), ("sí", True), ("SI", True)):
                f.db.execute("INSERT OR REPLACE INTO profile (key, value) "
                             "VALUES (?, ?)",
                             (self.fuga_mod.PERMISO_GERENTE, valor))
                f.db.commit()
                self.assertIs(self.fuga_mod.permiso_concedido(f.db), esperado,
                              f"{valor!r} se interpreto mal")
        finally:
            f.cerrar()

    def test_21_salir_de_la_sala_3_sin_contestar_deja_un_no(self):
        """El defecto prometido al entrar tiene que ser el que se cumple."""
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("", "", "", "", ""):    # cinco en blanco, luego EOF
                f._sala_horme()
        finally:
            f.cerrar()
        self.assertEqual(self.perfil().get(self.fuga_mod.PERMISO_GERENTE), "no")

    def test_22_un_si_en_la_sala_3_abre_la_puerta_y_entrega_el_perfil(self):
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("un compilador", "", "", "", "", "2"):
                f._sala_horme()               # 2 = "sí, puede leerlo"
            self.assertEqual(self.perfil().get(self.fuga_mod.PERMISO_GERENTE), "si")
            perfil = self.fuga_mod.perfil_para_gerente(f.db)
        finally:
            f.cerrar()
        self.assertEqual(perfil.get("proyecto_vital"), "un compilador")
        self.assertEqual(perfil.get("triunfo_deseado"), "NO_DATA",
                         "la ausencia tambien es del perfil y se entrega")
        self.assertNotIn(self.fuga_mod.PERMISO_GERENTE, perfil,
                         "el permiso no es un dato de la persona, es la puerta")

    def test_23_abandonar_la_sala_3_no_deja_un_permiso_suelto(self):
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion("un compilador", "", "", "", "", abandonar=True):
                with self.assertRaises(Abandono):
                    f._sala_horme()
            self.assertEqual(self.perfil(), {},
                             "una sala 3 abandonada dejo algo escrito")
            with self.assertRaises(self.fuga_mod.SinPermiso):
                self.fuga_mod.perfil_para_gerente(f.db)
        finally:
            f.cerrar()

    def test_24_la_comprobacion_vive_dentro_del_camino_de_lectura(self):
        """No se puede saltar porque no hay por donde: la unica funcion que
        devuelve el perfil llama ella misma al permiso.

        Se mira el arbol sintactico. Si manana alguien saca la comprobacion a
        quien llama, este caso se pone rojo -- que es justo el dia en que un
        llamante nuevo se la olvidaria.
        """
        import ast
        with open(AQUI / "fuga.py", encoding="utf-8") as fh:
            arbol = ast.parse(fh.read())
        fn = next((n for n in ast.walk(arbol)
                   if isinstance(n, ast.FunctionDef)
                   and n.name == "perfil_para_gerente"), None)
        self.assertIsNotNone(fn, "perfil_para_gerente desaparecio")
        llamadas = {n.func.id for n in ast.walk(fn)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertIn("permiso_concedido", llamadas,
                      "el camino de lectura ya no comprueba el permiso el mismo")

    # --- D74 · numeros, y solo numeros, tambien por voz --------------------

    def test_25_numero_dicho_acepta_digitos_y_palabras_y_rechaza_lo_demas(self):
        n = self.fuga_mod.numero_dicho
        for texto, esperado in (
                ("1", 1), ("  3 ", 3), ("el 2", 2), ("dos", 2), ("Tres.", 3),
                ("opción cuatro", 4), ("two", 2),
                ("Carlos", None), ("", None), ("sí", None),
                ("cercano", None), ("7", None), ("siete", None),
                ("tengo 3 hijos y 2 gatos", None)):
            self.assertEqual(n(texto, 4), esperado, f"{texto!r}")

    def test_26_una_respuesta_hablada_que_no_es_numero_se_rechaza_en_voz_alta(self):
        """El bug visto en la salida de test_12.

        Decir "Carlos" en "¿cómo quieres que te hable?" caia a 'cercano' sin
        una palabra. Ahora se rechaza, el rechazo NOMBRA los numeros que
        valen, y se vuelve a preguntar.
        """
        dichos = iter(["Carlos", "Carlos", "dos"])

        class OidoTerco:
            @staticmethod
            def oido_disponible():
                return True

            @staticmethod
            def grabar_y_transcribir(duracion_seg=5, idioma="es"):
                return next(dichos, None)

        self.fuga_mod.oido = OidoTerco
        salida = io.StringIO()
        f = self.fuga_mod.FugaMuseo()
        try:
            with contextlib.redirect_stdout(salida):
                elegido = f._preguntar("¿Cómo quieres que te hable?",
                                       opciones=["cercano", "formal",
                                                 "técnico", "poético"],
                                       default="cercano")
        finally:
            f.cerrar()

        texto = salida.getvalue()
        self.assertEqual(elegido, "formal",
                         "el numero dicho al tercer intento no se acepto")
        rechazos = [l for l in texto.splitlines() if "no es un número" in l]
        self.assertEqual(len(rechazos), 2,
                         f"se esperaban dos rechazos, hubo {len(rechazos)}")
        for linea in rechazos:
            for num in ("1", "2", "3", "4"):
                self.assertIn(num, linea,
                              f"el rechazo no nombra el {num}: {linea!r}")

    def test_27_por_teclado_rige_la_misma_gramatica(self):
        """Escribir el texto de la opcion tampoco vale. Una sola gramatica.

        Antes por teclado colaba "cercano" y por voz no: dos gramaticas, y
        ninguna dicha en el enunciado. Es el bug de D74 otra vez, en otra
        pregunta.
        """
        salida = io.StringIO()
        f = self.fuga_mod.FugaMuseo()
        try:
            with contextlib.redirect_stdout(salida):
                with guion("cercano", "2"):
                    elegido = f._preguntar("¿Cómo quieres que te hable?",
                                           opciones=["cercano", "formal"],
                                           default="cercano")
        finally:
            f.cerrar()
        self.assertEqual(elegido, "formal")
        self.assertIn("no es un número", salida.getvalue(),
                      "escribir el texto de la opcion se acepto sin rechistar")

    def test_28_agotados_los_intentos_el_defecto_se_dice(self):
        class OidoRuido:
            @staticmethod
            def oido_disponible():
                return True

            @staticmethod
            def grabar_y_transcribir(duracion_seg=5, idioma="es"):
                return "Carlos"

        self.fuga_mod.oido = OidoRuido
        salida = io.StringIO()
        f = self.fuga_mod.FugaMuseo()
        try:
            with contextlib.redirect_stdout(salida):
                elegido = f._preguntar("¿Sí o no?", opciones=["sí", "no"],
                                       default="no")
        finally:
            f.cerrar()
        self.assertEqual(elegido, "no")
        self.assertIn("Me quedo con «no»", salida.getvalue(),
                      "el defecto se tomo en silencio tras agotar los intentos")

    # --- el cierre · la cita se guarda en la memoria de verdad -------------

    def test_29_la_cita_se_guarda_como_recuerdo_de_m2(self):
        """El bug que el esquema fabricado tapaba durante toda su vida.

        `_guardar_cita` escribia en una `engrams (texto, creado_en, tipo)` que
        no existe: la de verdad tiene `what`, `why`, `origin`. Solo funcionaba
        contra la tabla inventada por el setUp de esta misma suite. Nadie
        habia llegado nunca al final de M3 con una base real.
        """
        f = self.fuga_mod.FugaMuseo()
        try:
            f._guardar_cita("el martes a las siete")
        finally:
            f.cerrar()
        self.assertEqual(self.engramas(),
                         [("el martes a las siete", "intencion")])

    def test_30_una_cita_en_blanco_no_inventa_un_recuerdo(self):
        """NO_DATA es una ausencia, no el texto de un recuerdo."""
        f = self.fuga_mod.FugaMuseo()
        try:
            self.assertIsNone(f._guardar_cita(""))
            self.assertIsNone(f._guardar_cita("   "))
        finally:
            f.cerrar()
        self.assertEqual(self.engramas(), [],
                         "una cita que nadie dio quedo escrita como recuerdo")

    def test_31_la_fuga_entera_de_punta_a_punta(self):
        """Nadie habia ejecutado `ejecutar()` completo. Ahora lo ejecuta esto.

        Las salas sueltas pasaban una a una y el recorrido entero reventaba en
        el ultimo paso. Un caso por sala no es un caso del recorrido.
        """
        libreto = [
            "2",                          # ritual de entrada: linterna
            "Carlos", "1",                # sala 1
            "1",                          # seguimos
            "2", "Debian",                # sala 2
            "1",                          # seguimos
            "un compilador", "", "", "", "", "2",   # sala 3 + permiso si
            "1",                          # seguimos
            "2", "no saco nada fuera",    # sala 4
            "1",                          # seguimos
            "el manual de Epicteto",      # sala 5
            "1",                          # seguimos
            "la vigilia", "el martes",    # sala 6 + ritual de salida
        ]
        f = self.fuga_mod.FugaMuseo()
        try:
            with guion(*libreto):
                completa = f.ejecutar()
            perfil_gerente = self.fuga_mod.perfil_para_gerente(f.db)
        finally:
            f.cerrar()

        self.assertTrue(completa, "la fuga no llego al final")
        self.assertEqual(sorted(self.salas()), [1, 2, 3, 4, 5, 6])
        self.assertEqual(set(self.salas().values()), {"completada"})
        self.assertEqual(perfil_gerente.get("proyecto_vital"), "un compilador")
        self.assertEqual(self.engramas(), [("el martes", "intencion")])
        self.assertEqual(self.fuentes(),
                         [("el manual de Epicteto", "declarada")])
        self.assertTrue(Path(self.fuga_mod.MANIFIESTO_PATH).is_file(),
                        "la fuga acabo sin manifiesto")
        self.assertFalse(self.fuga_mod.hay_fuga_pendiente(str(self.db_path)),
                         "una fuga terminada sigue diciendo que esta pendiente")

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
    ("el gerente lee el perfil sin permiso",
     "fuga.py",
     "    if not permiso_concedido(db):",
     "    if False:"),
    ("una respuesta hablada que no es numero cae al defecto en silencio",
     "fuga.py",
     "            print(f\"  {rechazo}\")\n            self._decir_en_voz(rechazo)",
     "            return default"),
    ("se estima el tiempo sin haber medido ninguna sala",
     "fuga.py",
     "    if len(medidas) >= MINIMO_PARA_ESTIMAR:",
     "    if True:\n        medidas = medidas or [3]"),
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
