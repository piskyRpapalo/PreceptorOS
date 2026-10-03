#!/usr/bin/env python3
"""test_consola.py · la consola soberana. Solo biblioteca estandar.

Lo que se defiende, en el orden en que importa:
  1. consola.py NO abre red (D68): ni socket, ni urllib, ni http.client, ni un
     proceso hijo que la abra por el.
  2. consola.py NO escribe: ni open en escritura, ni write_text, ni unlink, ni
     touch. La orden de parada se describe; no se ejecuta.
  3. Un tag `latest` sale SIEMPRE con riesgo.
  4. Una ficha de companero con un campo de decision se rechaza.
  5. Ninguna ruta de la salida lleva la casa de la persona.
  6. Una instantanea del rack ausente, rancia, sin zona o rota es NO_DATA
     entera: no se pinta ni un nodo.

Y el sabotaje: `python3 test_consola.py --sabotaje` copia consola.py, le mete
cada uno de esos fallos a proposito y exige que esta misma suite se ponga roja.
Una prueba que no se ha visto fallar no ha probado nada.
"""
from __future__ import annotations

import ast
import datetime as dt
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

# El modulo bajo prueba se carga por RUTA: el sabotaje apunta aqui una copia
# rota y esta misma suite tiene que cazarla.
RUTA = os.environ.get("CONSOLA_RUTA") or os.path.join(AQUI, "consola.py")
_spec = importlib.util.spec_from_file_location("consola_bajo_prueba", RUTA)
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)
FUENTE = open(RUTA, encoding="utf-8").read()

_pspec = importlib.util.spec_from_loader(
    "preceptoros_pwa_consola",
    SourceFileLoader("preceptoros_pwa_consola", os.path.join(AQUI, "bin", "preceptoros-pwa")))
PWA = importlib.util.module_from_spec(_pspec)
_pspec.loader.exec_module(PWA)

RED = {"socket", "urllib", "http", "ssl", "subprocess", "asyncio", "ftplib",
       "smtplib", "telnetlib", "xmlrpc", "socketserver", "requests"}
ESCRIBE = {"write", "write_text", "write_bytes", "unlink", "touch", "rename",
           "rmdir", "mkdir", "makedirs", "remove", "rmtree", "chmod", "symlink_to",
           "truncate"}


def _manifiesto(raiz, registro, nombre, tag, tam=1000, familia="llama",
                adaptador=False, blob=True, sin_config=False):
    """Un manifiesto de Ollama de mentira, con el formato real medido."""
    d = pathlib.Path(raiz) / "manifests" / registro / nombre
    d.mkdir(parents=True, exist_ok=True)
    blobs = pathlib.Path(raiz) / "blobs"
    blobs.mkdir(parents=True, exist_ok=True)
    hx = (nombre.replace("/", "") + tag).encode().hex().ljust(64, "0")[:64]
    if blob:
        (blobs / f"sha256-{hx}").write_bytes(b"m" * tam)
    cfg_hx = ("c" + hx)[:64]
    if not sin_config:
        (blobs / f"sha256-{cfg_hx}").write_text(json.dumps(
            {"model_family": familia, "model_type": "7B", "file_type": "Q4_K_M"}))
    capas = [{"mediaType": "application/vnd.ollama.image.model",
              "digest": f"sha256:{hx}", "size": tam}]
    if adaptador:
        capas.append({"mediaType": "application/vnd.ollama.image.adapter",
                      "digest": "sha256:" + "a" * 64, "size": 55})
    (d / tag).write_text(json.dumps({
        "schemaVersion": 2, "config": {"digest": f"sha256:{cfg_hx}", "size": 10},
        "layers": capas}))


def _rack(casa, generado, **extra):
    d = pathlib.Path(casa) / "laboratorio"
    d.mkdir(parents=True, exist_ok=True)
    datos = {"esquema": "hexelion.rack-instantanea/1", "generado": generado,
             "fuente": "nexo+ollama, loopback",
             "nodos": [{"nodo": "soberano", "estado": "ONLINE", "nota": ""},
                       {"nodo": "la-fragua", "estado": "NO_DATA", "nota": "el nexo no contesta"}],
             "ollama": {"residentes": [{"modelo": "qwen3:1.7b", "backend": "GPU"}],
                        "backend": "GPU"},
             "nivel": {"n": 0, "nombre": "SANTUARIO", "maximo": 3},
             "no_data": [{"campo": "sensores.adsb", "causa": "sin dato"}]}
    datos.update(extra)
    (d / "rack.json").write_text(json.dumps(datos, ensure_ascii=False))


AHORA = dt.datetime(2026, 10, 3, 20, 0, tzinfo=dt.timezone.utc)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # La casa vive bajo un `home/<usuario>` de mentira: si una ruta se
        # escapa a la salida, lleva un nombre de usuario que se puede buscar.
        self.home = os.path.join(self.tmp.name, "home", "fulanita")
        self.casa = pathlib.Path(self.home) / ".preceptoros"
        self.casa.mkdir(parents=True)
        self.ollama = pathlib.Path(self.home) / ".ollama" / "models"
        self.env = mock.patch.dict(os.environ, {"HOME": self.home})
        self.env.start()
        os.environ.pop("OLLAMA_MODELS", None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def vista(self, **kw):
        return C.vista(None, self.casa, ahora=AHORA, **kw)


# --- 1 y 2 · lo que el fichero no puede contener -----------------------------
class TestSinRedNiEscritura(unittest.TestCase):

    def setUp(self):
        self.arbol = ast.parse(FUENTE)

    def test_no_importa_nada_que_abra_red(self):
        malos = []
        for n in ast.walk(self.arbol):
            if isinstance(n, ast.Import):
                malos += [a.name for a in n.names if a.name.split(".")[0] in RED]
            elif isinstance(n, ast.ImportFrom) and n.module:
                if n.module.split(".")[0] in RED:
                    malos.append(n.module)
            elif isinstance(n, ast.Call) and getattr(n.func, "id", None) == "__import__":
                malos.append("__import__")
        self.assertEqual(malos, [], "consola.py abre red o puede abrirla (D68)")

    def test_no_escribe_ni_borra(self):
        malos = []
        for n in ast.walk(self.arbol):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            if isinstance(f, ast.Name) and f.id == "open":
                modo = n.args[1] if len(n.args) > 1 else next(
                    (k.value for k in n.keywords if k.arg == "mode"), None)
                if modo is not None and not (isinstance(modo, ast.Constant)
                                             and set(str(modo.value)) <= set("rbt")):
                    malos.append(f"open(modo={ast.unparse(modo)})")
            elif isinstance(f, ast.Attribute):
                if f.attr in ESCRIBE:
                    malos.append(f".{f.attr}()")
                if isinstance(f.value, ast.Name) and f.value.id in ("os", "shutil") \
                        and f.attr in ("replace", "rename", "remove", "unlink",
                                       "rmtree", "move", "copy", "copyfile", "system"):
                    malos.append(f"{f.value.id}.{f.attr}()")
        self.assertEqual(malos, [], "consola.py escribe o borra: es solo lectura")


# --- 3 · modelos del PC ----------------------------------------------------------
class TestModelosPC(Base):

    def setUp(self):
        super().setUp()
        _manifiesto(self.ollama, "registry.ollama.ai", "library/nomic", "latest")
        _manifiesto(self.ollama, "registry.ollama.ai", "library/qwen2.5", "7b",
                    familia="qwen2", adaptador=True)
        _manifiesto(self.ollama, "registry.ollama.ai", "library/roto", "1b", blob=False,
                    sin_config=True)
        _manifiesto(self.ollama, "hf.co", "openbmb/Mini-GGUF", "Q4_K_M")
        self.pc = self.vista()["modelos"]["pc"]
        self.por_id = {m["id"]: m for m in self.pc["modelos"]}

    def test_los_ids_son_nombre_tag(self):
        self.assertEqual(sorted(self.por_id), ["hf.co/openbmb/Mini-GGUF:Q4_K_M",
                                               "nomic:latest", "qwen2.5:7b", "roto:1b"])
        self.assertEqual(self.pc["estado"], "MEDIDO")

    def test_latest_es_riesgo_siempre(self):
        self.assertIn("tag_latest", self.por_id["nomic:latest"]["riesgos"])
        self.assertEqual(self.por_id["qwen2.5:7b"]["riesgos"], [])
        self.assertEqual(self.pc["con_riesgo"], 1)

    def test_lo_que_exige_socket_es_no_data_con_causa(self):
        for m in self.pc["modelos"]:
            self.assertEqual(m["residente"]["estado"], "NO_DATA")
            self.assertIn("D68", m["residente"]["causa"])
            self.assertEqual(m["tok_s"]["estado"], "NO_DATA")
            self.assertIs(m["usable_en_chat"], False)
            self.assertIn("PROPUESTA", m["causa_usable"])
            self.assertTrue(m["sello_sha256"].startswith("DECLARADO"))

    def test_config_y_blob(self):
        q = self.por_id["qwen2.5:7b"]
        self.assertEqual((q["familia"], q["parametros"], q["cuantizacion"]),
                         ("qwen2", "7B", "Q4_K_M"))
        self.assertTrue(q["blob_presente"])
        self.assertEqual(q["bytes"], 1000)
        self.assertEqual(len(q["sha256"]), 64)
        self.assertEqual(q["adaptador"]["bytes"], 55)
        r = self.por_id["roto:1b"]
        self.assertFalse(r["blob_presente"])
        self.assertEqual(r["familia"]["estado"], "NO_DATA")

    def test_sin_ollama_es_no_data_no_cero(self):
        shutil.rmtree(self.ollama)
        pc = self.vista()["modelos"]["pc"]
        self.assertEqual(pc["estado"], "NO_DATA")
        self.assertTrue(pc["causa"])
        self.assertNotIn("total", pc)


# --- 4 · companeros --------------------------------------------------------------
class TestCompaneros(unittest.TestCase):

    def test_los_ocho_oficiales_sin_decision(self):
        c = C.companeros(AQUI)
        self.assertEqual(c["estado"], "PROPUESTA")
        self.assertEqual(c["rechazadas"], [])
        ids = {f["id"]: f["nombre"] for f in c["fichas"]}
        self.assertEqual(ids, {
            "instalador": "El Instalador", "privacidad": "El Aduanero",
            "escritor": "El Escritor", "traductor": "El Traductor",
            "coder": "El Artesano", "analista": "El Analista",
            "aprendiz": "El Aprendiz", "bibliotecario": "El Bibliotecario"})
        for f in c["fichas"]:
            self.assertLessEqual(set(f), set(C.CAMPOS_FICHA))
            self.assertEqual(f["modelo_base"]["estado"], "NO_DATA")
            self.assertIn("nunca encima", f["adaptador"]["causa"])
            self.assertEqual((f["permisos"], f["herramientas"]), ([], []))
            self.assertIs(f["requiere_firma"]["salida_externa"], True)

    def _con(self, ficha):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        base = json.load(open(os.path.join(AQUI, "companeros.json"), encoding="utf-8"))
        base["companeros"] = [ficha]
        with open(os.path.join(d, "companeros.json"), "w", encoding="utf-8") as fh:
            json.dump(base, fh)
        return C.companeros(d)

    def test_un_campo_de_decision_tumba_la_ficha(self):
        buena = json.load(open(os.path.join(AQUI, "companeros.json"),
                               encoding="utf-8"))["companeros"][0]
        for campo in ("decide", "aprueba", "autoriza", "ejecuta", "inventado_manana"):
            with self.subTest(campo=campo):
                c = self._con({**buena, campo: True})
                self.assertEqual(c["fichas"], [])
                self.assertIn(campo, c["rechazadas"][0]["causa"])

    def test_sin_firma_de_salida_se_rechaza(self):
        buena = json.load(open(os.path.join(AQUI, "companeros.json"),
                               encoding="utf-8"))["companeros"][0]
        c = self._con({**buena, "requiere_firma": {"salida_externa": False}})
        self.assertEqual(c["fichas"], [])


# --- 5 · rutas ---------------------------------------------------------------------
class TestRutas(Base):

    def test_la_salida_no_lleva_la_casa(self):
        _manifiesto(self.ollama, "registry.ollama.ai", "library/a", "1b")
        _rack(self.casa, AHORA.isoformat(),
              nodos=[{"nodo": "soberano", "estado": "ONLINE",
                      "nota": f"log en {self.home}/.preceptoros/x.log"}],
              fuente=f"leido de {self.home}/p0x")
        crudo = json.dumps(self.vista(), ensure_ascii=False)
        self.assertNotIn(self.home, crudo)
        self.assertNotIn("fulanita", crudo)

    def test_la_regla_es_la_de_la_pwa(self):
        for r in (os.path.join(self.home, ".preceptoros", "laboratorio", "rack.json"),
                  "/opt/modelos/x/base.gguf", "/srv/a", "", None):  # guardia:permitir rutas de mentira para cruzar la regla con la PWA
            self.assertEqual(C.ruta_visible(r), PWA._ruta_visible(r), r)


# --- 6 · la instantanea del rack ------------------------------------------------
class TestInstantanea(Base):

    def inst(self):
        return C.instantanea(self.casa, ahora=AHORA)

    def test_ausente_es_no_data(self):
        i = self.inst()
        self.assertEqual(i["estado"], "NO_DATA")
        self.assertIn("no existe", i["causa"])
        self.assertNotIn("nodos", i)

    def test_fresca_es_dato(self):
        _rack(self.casa, (AHORA - dt.timedelta(minutes=4)).isoformat())
        i = self.inst()
        self.assertEqual(i["estado"], "MEDIDO")
        self.assertEqual([n["nodo"] for n in i["nodos"]], ["soberano", "la-fragua"])
        self.assertEqual(i["ollama"]["residentes"][0]["modelo"], "qwen3:1.7b")
        self.assertEqual(i["nivel"]["nombre"], "SANTUARIO")

    def test_offset_local_se_entiende(self):
        _rack(self.casa, "2026-10-03T20:55:00+01:00")       # = 19:55Z, 5 min
        self.assertEqual(self.inst()["estado"], "MEDIDO")

    def test_rancia_no_se_pinta(self):
        _rack(self.casa, (AHORA - dt.timedelta(minutes=16)).isoformat())
        i = self.inst()
        self.assertEqual(i["estado"], "NO_DATA")
        self.assertIn("rancia", i["causa"])
        self.assertNotIn("nodos", i)

    def test_sin_zona_no_se_pinta(self):
        _rack(self.casa, "2026-10-03T19:59:00")
        self.assertEqual(self.inst()["estado"], "NO_DATA")

    def test_del_futuro_no_se_pinta(self):
        _rack(self.casa, (AHORA + dt.timedelta(minutes=10)).isoformat())
        self.assertEqual(self.inst()["estado"], "NO_DATA")

    def test_otro_esquema_o_basura(self):
        _rack(self.casa, AHORA.isoformat(), esquema="otro/1")
        self.assertEqual(self.inst()["estado"], "NO_DATA")
        (self.casa / "laboratorio" / "rack.json").write_text("{a medias")
        self.assertEqual(self.inst()["estado"], "NO_DATA")

    def test_estado_y_backend_fuera_de_vocabulario_no_pasan(self):
        _rack(self.casa, AHORA.isoformat(),
              nodos=[{"nodo": "x", "estado": "VERDE", "nota": ""}],
              ollama={"residentes": [{"modelo": "m", "backend": "TPU"}], "backend": 0})
        i = self.inst()
        self.assertEqual(i["nodos"][0]["estado"], "NO_DATA")
        self.assertIsNone(i["ollama"]["residentes"][0]["backend"])
        self.assertIsNone(i["ollama"]["backend"])


# --- el rack y la casa -------------------------------------------------------------
class TestRackSoloLectura(Base):

    def _foto(self):
        return sorted((str(p.relative_to(self.tmp.name)), p.stat().st_size)
                      for p in pathlib.Path(self.tmp.name).rglob("*"))

    def test_la_vista_no_toca_el_disco(self):
        _rack(self.casa, AHORA.isoformat())
        # La UNICA escritura del camino no es de la consola: `guardrails`
        # siembra `policies.json` la primera vez que redacta (su diseno, el
        # mismo que ya dispara `_ruta_visible` del tablero). Se siembra antes
        # de la foto para que la foto mida lo que hace la consola, no eso.
        import guardrails
        guardrails.ruta_politicas()
        antes = self._foto()
        v = self.vista()
        self.assertEqual(self._foto(), antes)
        p = v["rack"]["orden_de_parada"]
        self.assertIs(p["la_consola_lo_hace"], False)
        self.assertIn("MODO_SANTUARIO", p["que"])
        self.assertFalse((self.casa / "MODO_SANTUARIO").exists())

    def test_centinela_manda(self):
        (self.casa / "estado.json").write_text(json.dumps({"nivel_soberania": 2}))
        n = self.vista()["rack"]["nivel_instalacion"]
        self.assertEqual((n["en_vigor"], n["declarado"], n["centinela_puesto"]), (2, 2, False))
        (self.casa / "MODO_SANTUARIO").write_text("")
        n = self.vista()["rack"]["nivel_instalacion"]
        self.assertEqual((n["en_vigor"], n["centinela_puesto"]), (0, True))

    def test_sin_plan_ni_interruptores_es_no_data(self):
        r = self.vista()["rack"]
        self.assertEqual(r["plan_vigente"]["estado"], "NO_DATA")
        self.assertEqual(r["interruptores"]["estado"], "NO_DATA")


# --- el resto de secciones ---------------------------------------------------------
class TestSecciones(Base):

    def test_esquema_y_secciones(self):
        v = self.vista()
        self.assertEqual(v["esquema"], "preceptoros.consola/1")
        self.assertIs(v["solo_lectura"], True)
        for s in ("modelos", "companeros", "thegame", "juez_media", "rack", "loras"):
            self.assertIn(s, v)

    def test_thegame_mide_y_casa_con_el_manifiesto(self):
        g = C.thegame(AQUI)
        self.assertEqual(g["estado"], "MEDIDO")
        nombres = {f["fichero"] for f in g["motor"]}
        self.assertLessEqual({"atlas-motor.js", "atlas-partida.js", "atlas-piloto.js",
                              "juez.js"}, nombres)
        for f in g["motor"]:
            if f["fichero"] != "corre.mjs":
                self.assertEqual(f["integridad"], "CUADRA", f["fichero"])
        self.assertEqual(g["idiomas"]["resto"]["estado"], "NO_DATA")
        self.assertIn("D68", g["servidor_local"]["causa"])

    def test_juez_y_loras_son_propuesta(self):
        v = self.vista()
        self.assertEqual(v["juez_media"]["estado"], "NO_DATA")
        self.assertEqual(v["juez_media"]["contrato"]["sello"], "PROPUESTA")
        self.assertEqual(set(v["juez_media"]["contrato"]["campos"]["origen"]),
                         {"local", "rack", "externa", "EMULADO"})
        self.assertEqual(v["loras"]["ciclo"], ["PROPUESTA", "EN_CANARIO", "ACTIVO",
                                               "CUARENTENA", "REVERTIDO"])
        self.assertEqual(set(v["loras"]["procedencias"]),
                         {"humano", "piloto_base", "denso", "lora", "sintetico", "emulado"})

    def test_producto_copia_el_paquete(self):
        paquete = {"en_uso": {"cual": "base"}, "opciones": [
            {"cual": "base", "disponible": True}, {"cual": "afinado", "disponible": False,
                                                    "causa": "no hay cerebro afinado declarado"}]}
        v = C.vista(paquete, self.casa, ahora=AHORA)
        ops = v["modelos"]["producto"]["opciones"]
        self.assertEqual([o["usable_en_chat"] for o in ops], [True, False])
        self.assertEqual(v["loras"]["afinado_actual"]["cual"], "afinado")


# --- la puerta y la cara -------------------------------------------------------------
class Fingida:
    def __init__(self):
        self.server = mock.Mock(ruta_db=None, modelo=None)
        self.codigo = self.cuerpo = None

    def _json(self, codigo, cuerpo):
        self.codigo, self.cuerpo = codigo, cuerpo


class TestPuerta(Base):

    def test_get_api_consola(self):
        h = Fingida()
        with mock.patch.object(PWA._casa, "raiz", return_value=self.casa):
            PWA.PWA._consola(h)
        self.assertEqual(h.codigo, 200)
        self.assertEqual(h.cuerpo["esquema"], "preceptoros.consola/1")
        self.assertNotIn(self.home, json.dumps(h.cuerpo, ensure_ascii=False))

    def test_estaticos_html_y_service_worker(self):
        for r in ("/consola.js", "/consola.css"):
            self.assertIn(r, PWA.ESTATICOS)
            self.assertTrue(os.path.isfile(os.path.join(AQUI, "interface", PWA.ESTATICOS[r][0])))
        html = open(os.path.join(AQUI, "interface", "dashboard.html"), encoding="utf-8").read()
        self.assertIn('src="/consola.js?v=', html)
        self.assertIn('href="/consola.css?v=', html)
        self.assertIn('id="consola"', html)
        # La barra va ANTES del chat: encima, no debajo.
        self.assertLess(html.index('id="consola"'), html.index('id="dice"'))
        sw = open(os.path.join(AQUI, "interface", "sw.js"), encoding="utf-8").read()
        for r in ("/consola.js?v=", "/consola.css?v="):
            self.assertIn(r, sw)

    def test_la_cara_no_manda_ni_guarda_nada(self):
        js = open(os.path.join(AQUI, "interface", "consola.js"), encoding="utf-8").read()
        for prohibido in ("innerHTML", "outerHTML", "insertAdjacentHTML", "localStorage",
                          "sessionStorage", "XMLHttpRequest", "WebSocket", "method:",
                          "eval(", "document.write"):
            self.assertNotIn(prohibido, js, prohibido)
        self.assertEqual(js.count("fetch("), 1)
        self.assertIn('fetch("/api/consola"', js)
        self.assertIn('aria-disabled', js)


@unittest.skipUnless(shutil.which("node"), "NO_DATA · sin node no se prueba la pintura")
class TestPintura(unittest.TestCase):
    """La regla de pintura, corrida en el mismo JS que ve la persona."""

    def test_no_data_se_pinta_con_causa_nunca_cero(self):
        prog = ("const c=require(%s);console.log(JSON.stringify(["
                "c.valor({estado:'NO_DATA',causa:'sin socket'}),c.valor(null),c.valor(undefined),"
                "c.valor(0),c.bytes(1536),c.bytes(null),c.valor([])]))"
                % json.dumps(os.path.join(AQUI, "interface", "consola.js")))
        sal = json.loads(subprocess.run(["node", "-e", prog], capture_output=True,
                                        text=True, timeout=30, check=True).stdout)
        self.assertEqual(sal[0], "NO_DATA · sin socket")
        self.assertTrue(sal[1].startswith("NO_DATA"))
        self.assertTrue(sal[2].startswith("NO_DATA"))
        self.assertEqual(sal[3], "0")                # un cero MEDIDO sí es un cero
        self.assertEqual(sal[4], "1,5 KB")
        self.assertTrue(sal[5].startswith("NO_DATA"))
        self.assertEqual(sal[6], "ninguno")


# --- el sabotaje ---------------------------------------------------------------------
SABOTAJES = (
    ("importa socket", "import json\n", "import json\nimport socket\n"),
    ("importa urllib", "import json\n", "import json\nimport urllib.request\n"),
    ("importa http.client", "import json\n", "import json\nimport http.client\n"),
    ("escribe un fichero", "def nd(causa):",
     "def _apunta(r):\n    open(r, 'a').close()\n\n\ndef nd(causa):"),
    ("pone el centinela", '"la_consola_lo_hace": False,',
     '"la_consola_lo_hace": bool(_estado.ruta_centinela(base).touch() or True),'),
    ("latest sin riesgo", '(["tag_latest"] if tag == "latest" else [])', "[]"),
    ("ficha que decide pasa", "sobran = sorted(set(ficha) - set(CAMPOS_FICHA))", "sobran = []"),
    ("salida sin sanear", 'return _sanear(salida, os.path.expanduser("~"))', "return salida"),
    ("ruta_visible distinta", "    if ruta.startswith(casa):\n        visible",
     "    if False:\n        visible"),
    ("rancia como dato", "if edad > RACK_RANCIA_S:", "if False:"),
    ("ausente como dato", 'return {**nd(f"rack.json {causa}"), "fichero": donde}',
     'return {"estado": "MEDIDO", "nodos": [], "fichero": donde}'),
)


def sabotaje():
    fuente = open(os.path.join(AQUI, "consola.py"), encoding="utf-8").read()
    tmp = tempfile.mkdtemp(prefix="consola-sabotaje-")
    detectadas = 0

    def corre(texto):
        ruta = os.path.join(tmp, "consola.py")
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write(texto)
        env = dict(os.environ, CONSOLA_RUTA=ruta)
        return subprocess.run([sys.executable, "-m", "unittest", "test_consola"],
                              cwd=AQUI, env=env, capture_output=True, text=True,
                              timeout=600).returncode

    try:
        if corre(fuente) != 0:
            print("AVISO · la copia SIN sabotear ya sale roja: el sabotaje no mide nada")
            print(f"RESULTADO SABOTAJE: 0/{len(SABOTAJES)}")
            return 1
        print("VERDE · copia intacta")
        for nombre, antes, despues in SABOTAJES:
            if antes not in fuente:
                print(f"  CRITICO · {nombre}: el ancla ya no existe en consola.py")
                continue
            codigo = corre(fuente.replace(antes, despues, 1))
            if codigo != 0:
                detectadas += 1
                print(f"  ROJO  · {nombre} · detectado")
            else:
                print(f"  VERDE · {nombre} · NO detectado")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"RESULTADO SABOTAJE: {detectadas}/{len(SABOTAJES)}")
    return 0 if detectadas == len(SABOTAJES) else 1


if __name__ == "__main__":
    if "--sabotaje" in sys.argv:
        sys.exit(sabotaje())
    unittest.main()
