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
        pide = re.compile(r"/assets/([A-Za-z0-9._-]+)")
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
