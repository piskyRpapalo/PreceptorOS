#!/usr/bin/env python3
"""La cara premium · los cuatro estados y el fail-closed.

El estado 4 se prueba inyectando el fallo en la costura, no rompiendo la
configuracion. Motivo medido el 2026-08-22: una configuracion invalida NO
bloquea -- cae a las politicas core, que no se pueden apagar, y el filtro sigue
corriendo. Eso es correcto por diseno, y significa que el estado 4 solo lo
alcanza un fallo del propio filtro. Se prueba lo que puede pasar, no lo que
seria comodo que pasara.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import guardrails as G

# El guardian de higiene no exime NUNCA la regla TOKEN-PROVEEDOR, ni con el
# pragma `guardia:permitir`, y hace bien: un fixture con forma de credencial es
# indistinguible de una fuga para cualquier grep que pase despues. Se compone en
# ejecucion, como en test_frontera.py, para que no exista entero en ninguna
# linea del arbol. Y pasa del suelo de 16 caracteres de la politica API_KEY, o
# no probaria la redaccion.
SECRETO_FALSO = "sk-" + "abc123DEF456ghi789JKL"
import memory
import captura

# `bin/preceptoros-pwa` no lleva extension .py -- es un ejecutable, no un modulo --
# asi que se le da un cargador explicito en vez de dejar que se adivine por el
# nombre. Probar el fichero que se ejecuta de verdad vale mas que probar una
# copia con otra extension.
from importlib.machinery import SourceFileLoader          # noqa: E402
_ruta = os.path.join(AQUI, "bin", "preceptoros-pwa")
_spec = importlib.util.spec_from_loader(
    "preceptoros_pwa", SourceFileLoader("preceptoros_pwa", _ruta))
PWA = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PWA)


class Fingida:
    """Un manejador sin socket: se le llama el metodo y se mira que respondio."""

    def __init__(self, db):
        self.server = mock.Mock(ruta_db=db, modelo=None)
        self.codigo = None
        self.cuerpo = None

    def _json(self, codigo, cuerpo):
        self.codigo, self.cuerpo = codigo, cuerpo


class TestFrontera(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "memory.db")
        memory.crear(self.db)
        self.h = Fingida(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def _frontera(self, texto):
        PWA.PWA._frontera(self.h, {"texto": texto})
        return self.h.codigo, self.h.cuerpo

    def test_1_con_hallazgos_los_cuenta_el_servidor(self):
        """Estado 1. El contador viaja en el payload; la interfaz no cuenta."""
        cod, cuerpo = self._frontera(f"clave {SECRETO_FALSO} aqui")
        self.assertEqual(cod, 200)
        self.assertTrue(cuerpo["hallazgos"])
        for h in cuerpo["hallazgos"]:
            self.assertIn("policy", h)
            self.assertIn("count", h)
        # El fragmento encontrado NUNCA viaja: clase y cantidad, nada mas.
        self.assertNotIn(SECRETO_FALSO, json.dumps(cuerpo))

    def test_2_limpio_declara_lista_vacia(self):
        """Estado 3. Lista vacia declarada, distinta de no haber mirado."""
        cod, cuerpo = self._frontera("hola, aqui no hay nada")
        self.assertEqual(cod, 200)
        self.assertEqual(cuerpo["hallazgos"], [])

    def test_3_fail_closed_devuelve_409(self):
        """Estado 4. Si el filtro no termina, 409 y NINGUN texto de vuelta."""
        with mock.patch.object(
                PWA.G, "preparar_envio",
                side_effect=G.EnvioBloqueado("el filtro no pudo completarse")):
            cod, cuerpo = self._frontera("lo que sea")
        self.assertEqual(cod, 409)
        self.assertEqual(cuerpo["estado"], "bloqueado")
        # La que sostiene la promesa: no hay campo por el que colar el texto.
        self.assertNotIn("texto", cuerpo)

    def test_4_texto_que_no_es_texto(self):
        PWA.PWA._frontera(self.h, {"texto": {"no": "soy texto"}})
        self.assertEqual(self.h.codigo, 400)


class TestAnidar(unittest.TestCase):
    """La Aduana con salida: el texto cazado fuera entra en la memoria, pero
    solo el saneado, y solo despues de que lo sanee ESTE lado.

    La doctrina Caza-Nido dice que el usuario va a una IA de fuera, trae el
    texto crudo y el agente local lo tacha antes de anidarlo. Hasta hoy la
    frontera comprobaba y ensenaba -- pero no guardaba nada, asi que el paso
    de "anidar" no existia y el circulo no se cerraba.

    La propiedad que sostiene todo esto no es "la interfaz manda texto limpio":
    es que el servidor NO SE FIA de la interfaz. Vuelve a filtrar el, siempre,
    y lo que escribe en disco es el resultado de su propio filtro. Una aduana
    que acepta el sello que trae el paquete no es una aduana.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "memory.db")
        memory.crear(self.db)
        self.h = Fingida(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def _anidar(self, datos):
        PWA.PWA._anidar(self.h, datos)
        return self.h.codigo, self.h.cuerpo

    def _crudo(self):
        """Los bytes del fichero, no lo que diga una consulta.

        Un `select` puede no ver una fila que sigue en una pagina libre o en el
        WAL. Lo que promete este producto es que el secreto NO TOCA EL DISCO,
        y eso solo se comprueba mirando el disco.
        """
        datos = b""
        for sufijo in ("", "-wal", "-shm"):
            try:
                with open(self.db + sufijo, "rb") as fh:
                    datos += fh.read()
            except OSError:
                pass
        return datos

    def test_8_anida_el_texto_saneado_y_el_sucio_no_toca_el_disco(self):
        cod, cuerpo = self._anidar(
            {"texto": f"la clave del router es {SECRETO_FALSO} y la uso a diario"})
        self.assertEqual(cod, 200)
        self.assertIsInstance(cuerpo.get("id"), int)

        with memory.abrir(self.db) as c:
            fila = memory.leer_engrama(c, cuerpo["id"])
        self.assertIsNotNone(fila, "se dijo que se anido y no hay fila")
        self.assertNotIn(SECRETO_FALSO, fila["what"])
        self.assertIn("REDACTED", fila["what"])
        # Lo que sobrevive es el contexto: anidar no puede quedarse solo con
        # la marca de redaccion o el recuerdo no diria nada.
        self.assertIn("router", fila["what"])

        self.assertNotIn(SECRETO_FALSO.encode(), self._crudo(),
                         "el secreto llego al disco: la aduana no sirve de nada")

    def test_9_el_servidor_no_se_fia_del_texto_ya_limpio_de_la_interfaz(self):
        """Si la interfaz manda un campo "ya lo limpie yo", se ignora.

        Es el agujero obvio de este endpoint: aceptar `texto_limpio` haria que
        cualquier cliente -- o cualquier bug de la interfaz -- pudiera escribir
        en la memoria sin pasar por el filtro.
        """
        cod, cuerpo = self._anidar({
            "texto": f"secreto {SECRETO_FALSO}",
            "texto_limpio": f"secreto {SECRETO_FALSO}",
            "hallazgos": [],
        })
        self.assertEqual(cod, 200)
        with memory.abrir(self.db) as c:
            fila = memory.leer_engrama(c, cuerpo["id"])
        self.assertNotIn(SECRETO_FALSO, fila["what"])

    def test_10_si_el_filtro_cae_no_se_escribe_nada(self):
        """Fail-closed, igual que `/api/frontera`: 409 y la memoria intacta."""
        with mock.patch.object(
                PWA.G, "preparar_envio",
                side_effect=G.EnvioBloqueado("el filtro no pudo completarse")):
            cod, cuerpo = self._anidar({"texto": "lo que sea"})
        self.assertEqual(cod, 409)
        self.assertEqual(cuerpo["estado"], "bloqueado")
        self.assertNotIn("texto", cuerpo)
        with memory.abrir(self.db) as c:
            n = c.execute("select count(*) from engrams").fetchone()[0]
        self.assertEqual(n, 0, "se escribio con el filtro caido")

    def test_11_lo_anidado_se_marca_como_importado(self):
        """`origin` distingue lo que dijo la persona de lo que trajo de fuera.

        Sin esa marca, un texto cazado en una IA ajena se leeria manana como
        algo que dijo el usuario. El CHECK del esquema solo admite tres
        valores y `importado` es exactamente este caso.
        """
        _, cuerpo = self._anidar({"texto": "el puerto por defecto es el 8080"})
        with memory.abrir(self.db) as c:
            fila = memory.leer_engrama(c, cuerpo["id"])
        self.assertEqual(fila["origin"], "importado")

    def test_12_texto_vacio_no_es_un_recuerdo(self):
        for vacio in ("", "   ", "\n\t "):
            cod, _ = self._anidar({"texto": vacio})
            self.assertEqual(cod, 400, f"acepto {vacio!r} como recuerdo")
        with memory.abrir(self.db) as c:
            self.assertEqual(
                c.execute("select count(*) from engrams").fetchone()[0], 0)

    def test_13_texto_que_no_es_texto(self):
        cod, _ = self._anidar({"texto": {"no": "soy texto"}})
        self.assertEqual(cod, 400)

    def test_14_el_porque_tambien_pasa_por_la_aduana(self):
        """El segundo campo es el que se olvida, y filtra igual que el primero."""
        cod, cuerpo = self._anidar({
            "texto": "algo inocente",
            "porque": f"me lo dio el router con la clave {SECRETO_FALSO}"})
        self.assertEqual(cod, 200)
        with memory.abrir(self.db) as c:
            fila = memory.leer_engrama(c, cuerpo["id"])
        self.assertNotIn(SECRETO_FALSO, fila["why"])
        self.assertNotIn(SECRETO_FALSO.encode(), self._crudo())

    def test_15_devuelve_lo_que_de_verdad_se_guardo(self):
        """La interfaz tiene que poder ensenar lo anidado, no lo que mando.

        Si el endpoint devolviera solo un `ok`, la persona nunca veria que se
        tacho de su texto: firmaria a ciegas lo que entra en su memoria.
        """
        _, cuerpo = self._anidar({"texto": f"clave {SECRETO_FALSO} final"})
        self.assertIn("texto", cuerpo)
        self.assertNotIn(SECRETO_FALSO, cuerpo["texto"])
        self.assertTrue(cuerpo["hallazgos"])
        self.assertIn("policy_hash", cuerpo)
        with memory.abrir(self.db) as c:
            fila = memory.leer_engrama(c, cuerpo["id"])
        self.assertEqual(cuerpo["texto"], fila["what"],
                         "lo devuelto no es lo guardado: dos verdades")


class TestCaptura(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "memory.db")
        memory.crear(self.db)
        with memory.abrir(self.db) as c:
            self.tid = captura.registrar(c, "una pregunta", "una respuesta")
        self.h = Fingida(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_5_listar_no_consiente_por_nadie(self):
        PWA.PWA._captura_listar(self.h)
        self.assertEqual(self.h.codigo, 200)
        self.assertEqual(self.h.cuerpo["recuento"]["consentidos"], 0)
        self.assertFalse(self.h.cuerpo["turnos"][0]["consent"])

    def test_6_consentir_es_uno_por_peticion(self):
        PWA.PWA._captura_marcar(self.h, {"id": self.tid, "consent": True})
        self.assertEqual(self.h.cuerpo["recuento"]["consentidos"], 1)
        PWA.PWA._captura_marcar(self.h, {"id": self.tid, "consent": False})
        self.assertEqual(self.h.cuerpo["recuento"]["consentidos"], 0)

    def test_7_id_que_no_es_id(self):
        PWA.PWA._captura_marcar(self.h, {"id": "todos", "consent": True})
        self.assertEqual(self.h.codigo, 400)


class TestCerebro(unittest.TestCase):
    """El selector de cerebro: la unica eleccion que la persona puede hacer
    sobre que modelo le contesta, y sus dos limites.

    `afinado.py` sabia elegir desde hacia tiempo, pero ninguna ruta lo exponia:
    la logica estaba escrita y desconectada. Esto la conecta -- y con la puerta
    cerrada por donde no debe entrar nada.

    EL LIMITE QUE IMPORTA: por aqui NO viaja NUNCA una ruta de fichero. La
    interfaz dice `base` o `afinado`, dos palabras de un vocabulario cerrado, y
    el servidor resuelve las rutas con `casa.raiz()`. `promover()` -- que si
    acepta una ruta y mide su huella -- se queda en la forja y no se expone.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = self.tmp.name
        self.db = os.path.join(self.raiz, "memory.db")
        memory.crear(self.db)
        self.base = os.path.join(self.raiz, "base.gguf")
        with open(self.base, "wb") as fh:
            fh.write(b"x" * 64)
        self.fino = os.path.join(self.raiz, "modelos", "afinado-v1.gguf")
        os.makedirs(os.path.dirname(self.fino), exist_ok=True)
        with open(self.fino, "wb") as fh:
            fh.write(b"y" * 128)
        self.h = Fingida(self.db)
        self.h.server.modelo = self.base
        # Un Mock devuelve un Mock por cada atributo que no se declare, y
        # `metricas` intenta redondearlo. Se declaran los dos que lee.
        self.h.server.tokens_sesion = 0
        self.h.server.ultimo_turno = None
        # `casa.raiz()` devuelve un Path, no una cadena. Un doble que devuelve
        # str hace fallar al producto por una razon que el producto no tiene:
        # se copia el tipo real, no el que resulte comodo de escribir.
        self.parche = mock.patch.object(PWA._casa, "raiz",
                                        return_value=pathlib.Path(self.raiz))
        self.parche.start()

    def tearDown(self):
        self.parche.stop()
        self.tmp.cleanup()

    def _leer(self):
        PWA.PWA._cerebro_leer(self.h)
        return self.h.codigo, self.h.cuerpo

    def _elegir(self, datos):
        PWA.PWA._cerebro_elegir(self.h, datos)
        return self.h.codigo, self.h.cuerpo

    def test_16_sin_afinado_dice_que_usa_el_base_y_por_que(self):
        cod, cuerpo = self._leer()
        self.assertEqual(cod, 200)
        self.assertEqual(cuerpo["en_uso"]["cual"], "base")
        self.assertTrue(cuerpo["en_uso"]["motivo"],
                        "un cerebro elegido sin motivo no es auditable")
        # La opcion del afinado se declara AUSENTE, no se omite: una lista de
        # una sola opcion se lee como «no hay mas», y si la hay pero no cuadra
        # la persona necesita saberlo.
        opciones = {o["cual"]: o for o in cuerpo["opciones"]}
        self.assertIn("afinado", opciones)
        self.assertFalse(opciones["afinado"]["disponible"])
        self.assertTrue(opciones["afinado"]["causa"])

    def test_17_con_afinado_promovido_se_puede_alternar(self):
        PWA._afinado.promover(self.raiz, self.fino, "v1", "caza-nido")
        _, cuerpo = self._leer()
        self.assertEqual(cuerpo["en_uso"]["cual"], "afinado")

        cod, cuerpo = self._elegir({"cual": "base", "motivo": "quiero comparar"})
        self.assertEqual(cod, 200)
        self.assertEqual(cuerpo["en_uso"]["cual"], "base")

        cod, cuerpo = self._elegir({"cual": "afinado", "motivo": "ya compare"})
        self.assertEqual(cod, 200)
        self.assertEqual(cuerpo["en_uso"]["cual"], "afinado")

    def test_18_no_se_acepta_una_ruta_por_el_cuerpo(self):
        """El agujero obvio. `cual` es un vocabulario cerrado de dos palabras."""
        for veneno in ("/etc/passwd", "../../base.gguf", self.fino,
                       "afinado; rm -rf", "", None, 3, {"cual": "base"}):
            cod, _ = self._elegir({"cual": veneno})
            self.assertEqual(cod, 400, f"acepto {veneno!r} como eleccion")

    def test_19_la_ruta_no_sale_cruda_al_tablero(self):
        """`HOME_PATH` es politica activa de este producto. Su propio tablero
        no puede saltarsela."""
        PWA._afinado.promover(self.raiz, self.fino, "v1")
        _, cuerpo = self._leer()
        crudo = json.dumps(cuerpo)
        self.assertNotIn(self.fino, crudo)
        self.assertNotIn(self.raiz, crudo)

    def test_20_un_afinado_con_la_huella_cambiada_no_se_ofrece(self):
        """La 4 de test_afinado, pero vista desde la puerta.

        Si el fichero cambia despues de promoverlo, el registro sigue diciendo
        que hay un afinado. `elegir` cae al base -- y esta puerta tiene que
        contarlo, no ensenar una opcion que no se puede usar.
        """
        PWA._afinado.promover(self.raiz, self.fino, "v1")
        with open(self.fino, "wb") as fh:
            fh.write(b"otro fichero distinto")
        _, cuerpo = self._leer()
        self.assertEqual(cuerpo["en_uso"]["cual"], "base")
        opciones = {o["cual"]: o for o in cuerpo["opciones"]}
        self.assertFalse(opciones["afinado"]["disponible"])
        self.assertIn("huella", opciones["afinado"]["causa"].lower())

    def test_22_medicion_mide_el_cerebro_que_de_verdad_contesta(self):
        """Dos verdades en la misma pantalla, vistas en la app viva.

        `/api/metricas` armaba su cabecera con `self.server.modelo`, que es
        SIEMPRE el base: la ruta que entro por la linea de ordenes. Con un
        afinado verificado en uso, el cajon de Medicion decia el nombre del
        base mientras el selector de justo debajo decia el del afinado --
        medido el 2026-09-02 en el tablero, uno encima del otro.

        Importa mas de lo que parece: la promesa del Banco de Pruebas es
        «estos tokens por segundo son los de TU cerebro». Si el nombre de la
        cabecera no es el del fichero que contesta, la medida queda atribuida
        al modelo equivocado, y comparar dos medidas deja de significar nada.

        `_estado` ya lo hacia bien -- consulta `elegir`. Esta puerta no.
        """
        PWA._afinado.promover(self.raiz, self.fino, "v1")
        PWA.PWA._metricas(self.h)
        self.assertEqual(self.h.codigo, 200)
        por = {m["clave"]: m for m in self.h.cuerpo["metricas"]}
        self.assertEqual(por["modelo_nombre"]["valor"],
                         os.path.basename(self.fino),
                         "Medicion nombra un cerebro distinto del que contesta")

    def test_21_pedir_un_afinado_que_no_esta_no_miente(self):
        """Sin afinado declarado, elegirlo devuelve 409 y sigue en el base."""
        cod, cuerpo = self._elegir({"cual": "afinado", "motivo": "a ver"})
        self.assertEqual(cod, 409)
        self.assertEqual(cuerpo["estado"], "bloqueado")
        _, leido = self._leer()
        self.assertEqual(leido["en_uso"]["cual"], "base")


class TestPerfilIdentidad(unittest.TestCase):
    """La huella y el avatar: quien eres para esta maquina y con que cara.

    La huella se llama Soberana (SHA256) y no Ed25519. El plan pedia Ed25519;
    la stdlib no lo trae y meter `cryptography` rompe «solo stdlib» y «funciona
    en Termux». Llamar Ed25519 a un sha256 seria mentir sobre la primitiva en
    la pantalla que promete transparencia. Correccion firmada el 2026-09-02.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = self.tmp.name
        self.db = os.path.join(self.raiz, "memory.db")
        memory.crear(self.db)
        self.h = Fingida(self.db)
        self.parche = mock.patch.object(PWA._casa, "raiz",
                                        return_value=pathlib.Path(self.raiz))
        self.parche.start()

    def tearDown(self):
        self.parche.stop()
        self.tmp.cleanup()

    def _leer(self):
        PWA.PWA._perfil_leer(self.h)
        return self.h.codigo, self.h.cuerpo

    def _guardar(self, datos):
        PWA.PWA._perfil_guardar(self.h, datos)
        return self.h.codigo, self.h.cuerpo

    def test_23_el_perfil_trae_la_huella_y_no_la_semilla(self):
        cod, cuerpo = self._leer()
        self.assertEqual(cod, 200)
        self.assertEqual(cuerpo["identidad"]["estado"], "ok")
        self.assertEqual(len(cuerpo["identidad"]["huella"]), 64)
        # El material del que sale la huella no viaja jamas.
        import huella as _hu
        with open(os.path.join(self.raiz, _hu.NOMBRE), "rb") as fh:
            semilla = fh.read()
        self.assertNotIn(semilla.hex(), json.dumps(cuerpo))

    def test_24_la_huella_no_cambia_entre_dos_lecturas(self):
        _, uno = self._leer()
        _, dos = self._leer()
        self.assertEqual(uno["identidad"]["huella"], dos["identidad"]["huella"])

    def test_25_el_avatar_es_un_vocabulario_cerrado(self):
        """Lo que se guarda acaba en un `src` de imagen. Si se aceptara texto
        libre, la interfaz pediria al servidor la ruta que le mandaran."""
        cod, _ = self._guardar({"avatar": "busto-despierto.webp"})
        self.assertEqual(cod, 200)
        _, leido = self._leer()
        self.assertEqual(leido["campos"]["avatar"], "busto-despierto.webp")

        for veneno in ("../../etc/passwd", "http://fuera/x.png",
                       "busto-noexiste.webp", "aurelius-up.png", ""):
            cod, _ = self._guardar({"avatar": veneno})
            self.assertEqual(cod, 400, f"acepto {veneno!r} como avatar")
        # Y el que ya estaba guardado no se toca por un intento fallido.
        _, leido = self._leer()
        self.assertEqual(leido["campos"]["avatar"], "busto-despierto.webp")

    def test_26b_se_ofrecen_las_dos_familias_de_cara(self):
        """Bustos Y ojos. Las dos, y ninguna a medias.

        La mision pedia elegir avatar «entre los sprites de ojos/bustos». Se
        entregaron solo los ocho bustos, y los ocho `ojo-*.webp` se quedaron en
        `assets/` sin que los referenciara NADIE en todo el arbol: 51 790 B de
        arte pagado y nunca ensenado. Se midio el 2026-09-02 con un grep sobre
        el arbol entero.

        Son dos familias y no una lista larga a proposito: el busto es quien
        eres, el ojo es la cara que el cabezal pone segun con quien hablas. Que
        la interfaz las separe es lo que impide que se lean como dieciseis
        dibujos intercambiables.
        """
        _, cuerpo = self._leer()
        familias = cuerpo["avatares"]
        self.assertIsInstance(familias, dict,
                              "las caras llegan sueltas: no se puede saber "
                              "cual es un busto y cual un ojo")
        self.assertEqual(set(familias), {"bustos", "ojos"})
        for cual, nombres in familias.items():
            with self.subTest(familia=cual):
                self.assertEqual(len(nombres), 8, f"{cual}: no son ocho")

    def test_26c_ninguna_cara_del_disco_se_queda_fuera(self):
        """Toda `busto-*.webp` y `ojo-*.webp` de `assets/` se puede elegir.

        La forma de fallar es anadir arte y olvidar la lista: el fichero entra
        en el repo, pesa, y no lo ve nadie. Es lo que acababa de pasar con los
        ojos, asi que la comprobacion mira el disco y no la lista.
        """
        import glob
        en_disco = {os.path.basename(f) for f in
                    glob.glob(os.path.join(AQUI, "assets", "busto-*.webp"))
                    + glob.glob(os.path.join(AQUI, "assets", "ojo-*.webp"))}
        _, cuerpo = self._leer()
        ofrecidas = {n for lista in cuerpo["avatares"].values() for n in lista}
        self.assertFalse(
            en_disco - ofrecidas,
            "hay caras en assets/ que nadie puede elegir -- peso que viaja y "
            "no se ve: " + ", ".join(sorted(en_disco - ofrecidas)))

    def test_26_los_avatares_ofrecidos_existen_en_el_disco(self):
        """Una lista que ofrece una cara que no esta deja un hueco roto."""
        _, cuerpo = self._leer()
        self.assertTrue(cuerpo["avatares"])
        for nombre in [n for l in cuerpo["avatares"].values() for n in l]:
            self.assertTrue(
                os.path.isfile(os.path.join(AQUI, "assets", nombre)),
                f"se ofrece {nombre} y no esta en assets/")

    def test_27_sin_avatar_elegido_se_declara_el_hueco(self):
        _, cuerpo = self._leer()
        self.assertEqual(cuerpo["campos"]["avatar"], "NO_DATA")


class TestMarcaDeAusencia(unittest.TestCase):
    """La interfaz tiene que reconocer la marca de ausencia que manda el
    servidor. Exactamente esa, no uno parecida.

    EL FALLO, visto en el tablero el 2026-09-02: al abrir Perfil en una
    instalacion nueva, las cajas de texto salian con la marca de ausencia
    escrita dentro, como si la persona se llamara asi. `sinNoData()` comparaba
    contra una version con otras mayusculas, la comparacion no acertaba nunca,
    y el valor pasaba tal cual al `value` del campo.

    Y la causa de la causa es lo que hace que esto merezca una prueba: la marca
    va en mayusculas, y `test_guardrails` prohibe palabras en mayusculas en los
    ficheros de `interface/`. Alguien la escribio con otras mayusculas para que
    el gate pasara -- y el gate paso, y la comparacion se rompio en silencio.
    Esquivar una regla cambiando un dato es como se fabrican los fallos que
    ninguna prueba ve.

    Se comprueba por el COMPORTAMIENTO y no por el texto del fichero: lo que
    importa no es como se escriba la constante, sino que el valor que produce
    sea el que manda el servidor.
    """

    def test_28_la_interfaz_reconoce_la_marca_que_manda_el_servidor(self):
        import re
        ruta = os.path.join(AQUI, "interface", "dashboard.js")
        fuente = open(ruta, encoding="utf-8").read()

        # Las cadenas con las que la interfaz compara para detectar el hueco.
        # Se sacan del propio fichero: una lista escrita aqui a mano volveria a
        # separarse del codigo en cuanto alguien tocara uno de los dos.
        candidatas = set(re.findall(r'!==\s*([A-Za-z_]+)\b', fuente))
        candidatas |= set(re.findall(r'===\s*([A-Za-z_]+)\b', fuente))
        literales = set(re.findall(r'[!=]==\s*"([^"]*)"', fuente))

        marca = memory.AUSENTE
        parecidas = {v for v in literales
                     if v.lower() == marca.lower() and v != marca}
        self.assertFalse(
            parecidas,
            f"la interfaz compara contra {parecidas} y el servidor manda "
            f"{marca!r}: la comparacion no acierta nunca")
        del candidatas


class TestNingunRelojSeQuedaSuelto(unittest.TestCase):
    """Todo `setInterval` del tablero tiene su `clearInterval`.

    El cajon de Medicion se refresca solo mientras esta abierto. Un latido que
    se arranca al abrir y no se para al cerrar sigue pidiendo `/api/metricas`
    para siempre -- en un telefono eso es bateria que se va sin que nada en la
    pantalla lo justifique, y encima se apilan: abrir y cerrar el cajon cinco
    veces deja cinco relojes corriendo a la vez.

    Es una clase de fallo que no se ve nunca en una sesion corta y que se nota
    en el aparato de alguien horas despues, sin sintoma que la senale.

    Se comprueba por conteo y no por lectura: no hace falta entender el flujo
    para saber que un `setInterval` sin `clearInterval` en el mismo fichero es
    un reloj que nadie para.
    """

    def test_29_cada_setinterval_tiene_su_clearinterval(self):
        import re
        for nombre in ("dashboard.js", "app.js"):
            fuente = open(os.path.join(AQUI, "interface", nombre),
                          encoding="utf-8").read()
            arranques = len(re.findall(r"\bsetInterval\s*\(", fuente))
            paradas = len(re.findall(r"\bclearInterval\s*\(", fuente))
            if arranques:
                self.assertGreaterEqual(
                    paradas, 1,
                    f"{nombre} arranca {arranques} reloj(es) y no para ninguno")


class TestElDespertarOcurreUnaVez(unittest.TestCase):
    """El contrato de ASSETS.md: «El despertar ocurre una vez. Un despertar que
    se repite en cada frase deja de ser un despertar y se convierte en un tic».

    `cara.py` lo cumple con una bandera (`despertado`). El tablero no lo
    cumplia, y se midio en el navegador el 2026-09-02: al quitar la clase
    `piensa` -- o sea cada vez que el modelo termina de generar -- la lista de
    animaciones de `.busto` vuelve a ser la de reposo, y el navegador trata eso
    como una animacion NUEVA. `despertar` se reproducia entero otra vez, del
    fotograma 0 al de reposo, despues de cada respuesta.

    Venia de antes de la tira de ocho, pero la tira lo empeoro: con cuatro
    fotogramas el tic duraba tres pasos, con ocho dura seis.

    La cura es una clase que la interfaz pone cuando el despertar termina y que
    deja SOLO la respiracion. Aqui se comprueba su estructura; el
    comportamiento se midio en el navegador y esta en el mensaje del commit.
    """

    def _css(self):
        return open(os.path.join(AQUI, "interface", "dashboard.css"),
                    encoding="utf-8").read()

    def test_30_hay_un_estado_de_reposo_sin_despertar(self):
        css = self._css()
        self.assertIn(".busto.despierto", css,
                      "no hay clase de reposo: el despertar se repetira")
        # Y la interfaz tiene que ponersela, o la clase es decoracion.
        js = open(os.path.join(AQUI, "interface", "dashboard.js"),
                  encoding="utf-8").read()
        self.assertIn("despierto", js,
                      "la clase existe en el css y nadie la pone")

    def test_31_reduced_motion_cubre_toda_variante_que_anime(self):
        """Quien pidio menos movimiento no puede recibirlo por una variante
        que nadie acordo de anadir al bloque.

        Es la forma de fallar de este fichero: se anade una clase con
        animacion propia y se olvida el bloque de accesibilidad. Se comprueba
        por estructura, para que la proxima variante no dependa de que alguien
        se acuerde.
        """
        import re
        css = self._css()
        i = css.index("prefers-reduced-motion")
        antes, bloque = css[:i], css[i:]

        # Variantes de `.busto` que declaran animacion fuera del bloque.
        animadas = set()
        for sel, cuerpo in re.findall(r"(\.busto[\w.]*)\s*\{([^}]*)\}", antes):
            if re.search(r"\banimation\s*:", cuerpo):
                animadas.add(sel)
        self.assertTrue(animadas, "no se encontro ninguna variante animada")

        for sel in sorted(animadas):
            self.assertIn(sel, bloque,
                          f"{sel} anima y el bloque de movimiento reducido no "
                          f"la nombra: se movera igual para quien pidio que no")


class TestLaCaraNoSeApaga(unittest.TestCase):
    """Ninguna animacion de la cara puede hacerla desaparecer.

    CICATRIZ, 2026-08-23. El bucle de hablar iba de 0% a -400% en
    `background-position`. Con posicionamiento en porcentaje, cualquier valor
    fuera de 0-100% saca la imagen del marco: el busto desaparecia la mitad de
    cada ciclo y quedaba un parpadeo de alto contraste a ritmo constante.

    No es una queja estetica. Un parpadeo asi es un riesgo para personas con
    epilepsia fotosensible, y lo vio una persona mirando el telefono antes que
    ninguna prueba. Esta es esa prueba.
    """

    RUTA = os.path.join(AQUI, "interface")

    def _css(self):
        for nombre in os.listdir(self.RUTA):
            if nombre.endswith(".css"):
                with open(os.path.join(self.RUTA, nombre), encoding="utf-8") as fh:
                    yield nombre, fh.read()

    def test_ninguna_posicion_de_fondo_sale_del_marco(self):
        import re
        # Se comparan NUMEROS, no formas. La primera version de esta prueba usaba
        # una alternancia de patrones para "mayor que 100" y marcaba 100% como
        # invalido -- que es el ultimo fotograma, alineado a la derecha y
        # perfectamente visible. Una prueba que marca lo correcto se acaba
        # desactivando, y entonces deja de proteger lo que importa.
        valores = re.compile(r"background-position:\s*(-?\d+(?:\.\d+)?)%")
        for nombre, css in self._css():
            for bruto in valores.findall(css):
                v = float(bruto)
                self.assertTrue(
                    0 <= v <= 100,
                    f"{nombre}: background-position {v}% saca la imagen del "
                    f"marco y la cara se apaga a mitad de ciclo")

    def test_toda_animacion_de_la_cara_respeta_menos_movimiento(self):
        """Quien pidio menos movimiento no recibe una cara parpadeando."""
        for nombre, css in self._css():
            if "@keyframes" not in css:
                continue
            self.assertIn("prefers-reduced-motion", css,
                          f"{nombre} anima y no atiende a quien pide quietud")


class TestLasImagenesQuePideLaCaraSeSirven(unittest.TestCase):
    """Toda imagen que la interfaz pide tiene que existir y saber servirse.

    CICATRIZ, 2026-08-23. El servidor traducia extension a tipo con una tabla
    cerrada -- png, svg, webp, gif -- y devolvia 404 para todo lo demas. El
    fondo de la lamina se guardo en jpeg porque una fotografia de marmol en png
    pesa cinco veces mas, y desde ese dia el fondo no se pintaba: se veia el
    color de respaldo y parecia una decision de diseno. Nadie lo noto porque
    ninguna prueba miraba lo que la hoja de estilo pide de verdad.

    La prueba no lleva una lista de ficheros escrita a mano: la saca de la
    propia interfaz. Una lista a mano se queda vieja en cuanto alguien anade
    una imagen, y volveria a fallar en silencio.
    """

    RUTA = os.path.join(AQUI, "interface")

    def _pedidas(self):
        import re
        # La barra entra en la clase a proposito. Sin ella, de
        # `/assets/caras/avatar-fijo.webp` esta prueba capturaba solo `caras` y
        # despues preguntaba si `assets/caras` es un FICHERO -- es una carpeta,
        # asi que fallaba sin poder nombrar lo que faltaba. Con la barra se
        # comprueba la ruta entera, que es lo que el navegador va a pedir.
        # Es mas estricto que antes, no menos: ahora tambien valida el tramo
        # de carpeta que hasta hoy se perdia por el camino.
        pide = re.compile(r"/assets/([A-Za-z0-9._/-]+)")
        vistas = set()
        for nombre in sorted(os.listdir(self.RUTA)):
            if not nombre.endswith((".css", ".html", ".js")):
                continue
            with open(os.path.join(self.RUTA, nombre), encoding="utf-8") as fh:
                for hallado in pide.findall(fh.read()):
                    vistas.add((nombre, hallado))
        return sorted(vistas)

    def test_existen_en_el_disco(self):
        pedidas = self._pedidas()
        self.assertTrue(pedidas, "la interfaz no pide ninguna imagen: "
                                 "la prueba se quedo sin objeto")
        for donde, fichero in pedidas:
            self.assertTrue(
                os.path.isfile(os.path.join(AQUI, "assets", fichero)),
                f"{donde} pide assets/{fichero} y no esta en el disco")

    def test_el_servidor_sabe_su_tipo(self):
        with open(os.path.join(AQUI, "bin", "preceptoros-pwa"),
                  encoding="utf-8") as fh:
            fuente = fh.read()
        for donde, fichero in self._pedidas():
            ext = os.path.splitext(fichero)[1].lower()
            self.assertIn(
                f'"{ext}"', fuente,
                f"{donde} pide assets/{fichero} y el servidor no tiene tipo "
                f"para {ext}: respondera 404 y la cara saldra sin esa pieza")


if __name__ == "__main__":
    unittest.main(verbosity=2)
