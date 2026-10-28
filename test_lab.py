#!/usr/bin/env python3
"""test_lab.py · el Lab hablando y sus fichas de modelos. Solo biblioteca estandar.

Lo que se defiende:
  1. Cada mensaje dice quien habla, en vocabulario cerrado; una voz
     desconocida sale como «otra:», nunca disfrazada de una conocida.
  2. El orquestador contesta con SU voz. Ningun agente ni modelo escribe como
     soberano, y la puerta de la persona rechaza cualquier otra voz.
  3. El canal del registro se abre en solo lectura y solo con sus cuatro tipos.
  4. Un adaptador «entrenado» sin artefacto con hash es NO_DATA.
  5. Tok/s solo con medicion completa (maquina, fecha con zona, backend) y del
     mismo sha que el blob; si no, NO_DATA.
  6. Sin motor o sin texto del modelo, no se inventa respuesta.

`python3 test_lab.py --sabotaje` rompe una copia de lab.py y exige rojo.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

RUTA = os.environ.get("LAB_RUTA") or os.path.join(AQUI, "lab.py")
_spec = importlib.util.spec_from_file_location("lab_bajo_prueba", RUTA)
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)
FUENTE = open(RUTA, encoding="utf-8").read()

import canales as K                                          # noqa: E402

SHA_MINI = "1" * 64
SHA_GRANDE = "2" * 64


def _blob(raiz, nombre, tag, sha, tam=100):
    d = pathlib.Path(raiz) / "manifests" / "registry.ollama.ai" / "library" / nombre
    d.mkdir(parents=True, exist_ok=True)
    b = pathlib.Path(raiz) / "blobs"
    b.mkdir(parents=True, exist_ok=True)
    (b / f"sha256-{sha}").write_bytes(b"g" * tam)
    (d / tag).write_text(json.dumps({"config": {}, "layers": [
        {"mediaType": "application/vnd.ollama.image.model", "digest": f"sha256:{sha}", "size": tam}]}))


def _medicion(**cambia):
    m = {"modelo": L.MINI, "sha256": SHA_MINI, "tok_s_generacion": 50.0, "tok_s_prompt": 250.0,
         "maquina": "banco", "fecha": "2026-10-04T03:28:00+01:00", "backend": "CPU"}
    m.update(cambia)
    return m


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
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

    def mediciones(self, *ms):
        (self.casa / L.MEDICIONES).write_text(json.dumps(
            {"esquema": L.ESQUEMA_MEDICION, "mediciones": list(ms)}))

    def registro(self, filas):
        d = self.casa / "registro"
        d.mkdir(exist_ok=True)
        con = sqlite3.connect(d / "eventos.db")
        con.execute("create table if not exists eventos (n integer primary key autoincrement, ts text not null,"
                    " maquina text not null, tipo text not null, actor text not null,"
                    " cuerpo_json text not null, no_data_json text not null, bloquea_json text)")
        for ts, tipo, actor, cuerpo in filas:
            con.execute("insert into eventos (ts, maquina, tipo, actor, cuerpo_json, no_data_json)"
                        " values (?, 'x', ?, ?, ?, '[]')", (ts, tipo, actor, json.dumps(cuerpo)))
        con.commit()
        con.close()


class TestQuienHabla(Base):

    def test_vocabulario_cerrado(self):
        self.assertEqual([L.quien(v) for v in ("app", "lab", "web", "claude", "hexelion",
                                               "orquestador", "Soberano", "s0berano")],
                         ["claude-app", "claude-lab", "claude-web", "orquestador", "hexelion",
                          "orquestador", "soberano", "soberano"])
        self.assertEqual(L.quien("intruso"), "otra:intruso")

    def test_conversacion_junta_canales_y_registro(self):
        K.di("lab", "lab", "forja en marcha", base=self.casa)
        self.registro([("2026-10-04T00:00:00Z", "duda", "hexelion", {"texto": "¿qué emite mi latido?"}),
                       ("2026-10-04T00:01:00Z", "herramienta.llamada", "claude", {"herramienta": "x"}),
                       ("2026-10-04T00:02:00Z", "propuesta", "claude-app", {"pide": "registro en rack.json"})])
        c = L.conversacion(self.casa)
        quienes = [(m["origen"], m["quien"]) for m in c["mensajes"]]
        self.assertIn(("registro", "hexelion"), quienes)
        self.assertIn(("registro", "claude-app"), quienes)
        self.assertIn(("canal:lab", "claude-lab"), quienes)
        self.assertNotIn("herramienta.llamada", [m["maquina"].get("tipo") for m in c["mensajes"]])
        self.assertEqual(c["mensajes"][0]["texto"], "¿qué emite mi latido?")

    def test_registro_en_solo_lectura(self):
        self.registro([("2026-10-04T00:00:00Z", "duda", "hexelion", {"texto": "hola"})])
        db = self.casa / "registro" / "eventos.db"
        antes = (db.read_bytes(), db.stat().st_mtime_ns)
        L.conversacion(self.casa)
        self.assertEqual((db.read_bytes(), db.stat().st_mtime_ns), antes)
        self.assertIn("mode=ro", FUENTE)

    def test_almacenes_viejos_entran_como_archivo_en_lectura(self):
        (self.casa / "laboratorio").mkdir()
        sala = self.casa / "laboratorio" / "sala.jsonl"
        sala.write_text(json.dumps({"n": 1, "t": "2026-10-03T21:00:00+01:00", "voz": "lab",
                                    "texto": "desde la Sala"}) + "\n")
        antes = sala.read_bytes()
        c = L.conversacion(self.casa)
        viejos = [m for m in c["mensajes"] if m["origen"] == "archivo:sala"]
        self.assertEqual([(m["quien"], m["texto"]) for m in viejos], [("claude-lab", "desde la Sala")])
        self.assertEqual(sala.read_bytes(), antes)
        self.assertFalse((self.casa / "canales").exists(), "no nace un almacen nuevo")

    def test_sin_registro_es_no_data(self):
        self.assertEqual(L.conversacion(self.casa)["registro"]["estado"], "NO_DATA")


class TestModelos(Base):

    def test_two_blobs_remain_cached_and_changed_bytes_are_rejected(self):
        contents = [b"first synthetic blob", b"second synthetic blob"]
        hashes = [hashlib.sha256(data).hexdigest() for data in contents]
        store = self.ollama / "blobs"
        store.mkdir(parents=True)
        for sha, data in zip(hashes, contents):
            (store / ("sha256-" + sha)).write_bytes(data)
        L._consola._SHA256_BLOB_CACHE.clear()
        real = hashlib.sha256
        with mock.patch.object(L._consola.hashlib, "sha256", wraps=real) as hasher:
            for sha in (hashes[0], hashes[1], hashes[0]):
                self.assertEqual(L._consola.verificar_blob(sha, raiz=self.ollama)["estado"], "MEDIDO")
            self.assertEqual(hasher.call_count, 2)
            (store / ("sha256-" + hashes[0])).write_bytes(b"changed synthetic blob")
            self.assertEqual(L._consola.verificar_blob(hashes[0], raiz=self.ollama)["estado"], "ERROR")
            self.assertEqual(hasher.call_count, 3)

    def test_digest_cache_is_bounded(self):
        store = self.ollama / "blobs"
        store.mkdir(parents=True)
        L._consola._SHA256_BLOB_CACHE.clear()
        for i in range(12):
            data = ("synthetic-" + str(i)).encode()
            sha = hashlib.sha256(data).hexdigest()
            (store / ("sha256-" + sha)).write_bytes(data)
            self.assertEqual(L._consola.verificar_blob(sha, raiz=self.ollama)["estado"], "MEDIDO")
        self.assertLessEqual(len(L._consola._SHA256_BLOB_CACHE), 8)

    def test_verificar_blob_mide_hash_correcto(self):
        contenido = b"blob de prueba fijado"
        sha = hashlib.sha256(contenido).hexdigest()
        blob = self.ollama / "blobs" / ("sha256-" + sha)
        blob.parent.mkdir(parents=True)
        blob.write_bytes(contenido)
        resultado = L._consola.verificar_blob(sha, raiz=self.ollama)
        self.assertEqual((resultado["estado"], resultado["sha256"], resultado["bytes"]),
                         ("MEDIDO", sha, len(contenido)))

    def test_verificar_blob_detecta_hash_distinto_del_contenido(self):
        blob = self.ollama / "blobs" / ("sha256-" + "f" * 64)
        blob.parent.mkdir(parents=True)
        blob.write_bytes(b"contenido de prueba")
        resultado = L._consola.verificar_blob("f" * 64, raiz=self.ollama)
        self.assertEqual(resultado["estado"], "ERROR")
        self.assertIn("no coincide", resultado["causa"])

    def test_soberano_coder_ficha_ausente_rechaza_con_causa(self):
        ficha = L.modelos_lab(self.casa)["soberano_coder"]
        self.assertFalse(ficha["disponible"])
        self.assertTrue(ficha["causa"])

    def test_soberano_coder_hash_no_coincidente_rechaza(self):
        with mock.patch.object(L._consola, "verificar_blob",
                               return_value={"estado": "ERROR", "sha256": "f" * 64,
                                             "causa": "el contenido no coincide con el SHA-256 fijado"}):
            ficha = L.modelos_lab(self.casa)["soberano_coder"]
        self.assertFalse(ficha["disponible"])
        self.assertIn("no coincide", ficha["causa"])

    def test_soberano_coder_resuelve_por_sha_y_no_reemplaza_mini(self):
        medido = {"estado": "MEDIDO", "sha256": L.SOBERANO_SHA256,
                  "bytes": 123, "ruta": "~/.ollama/models/blobs/sha256-…"}
        with mock.patch.object(L._consola, "verificar_blob", return_value=medido) as verificar, \
                mock.patch.object(L, "_ficha_motor",
                                  return_value={"estado": "MEDIDO", "ruta": "…/llama-completion",
                                                "bytes": 12}):
            modelos = L.modelos_lab(self.casa)
        verificar.assert_called_once_with(L.SOBERANO_SHA256, raiz=self.ollama)
        self.assertTrue(modelos["soberano_coder"]["disponible"])
        self.assertEqual(modelos["soberano_coder"]["sha256"], L.SOBERANO_SHA256)
        self.assertEqual(modelos["soberano_coder"]["resolucion"], "sha256_blob")
        self.assertIn("mini", modelos)
        self.assertFalse(modelos["mini"]["disponible"])
        self.assertEqual(modelos["soberano_coder"]["catalogo"]["estado"], "NO_DATA")

    def test_soberano_coder_blob_verificado_sin_motor_sigue_no_disponible(self):
        medido = {"estado": "MEDIDO", "sha256": L.SOBERANO_SHA256,
                  "bytes": 123, "ruta": "…/blob"}
        with mock.patch.object(L._consola, "verificar_blob", return_value=medido), \
                mock.patch.object(L, "_ficha_motor",
                                  return_value={"estado": "NO_DATA", "causa": "motor ausente"}):
            ficha = L.modelos_lab(self.casa)["soberano_coder"]
        self.assertTrue(ficha["blob_disponible"])
        self.assertFalse(ficha["disponible"])
        self.assertEqual(ficha["causa"], "motor ausente")

    def test_soberano_coder_rechaza_digest_de_manifiesto_distinto(self):
        inventario = [{"id": L.SOBERANO_CODER, "sha256": "f" * 64,
                       "blob_presente": True}]
        with mock.patch.object(L._consola, "modelos_pc", return_value={"modelos": inventario}), \
                mock.patch.object(L._consola, "verificar_blob",
                                  return_value={"estado": "MEDIDO", "sha256": L.SOBERANO_SHA256,
                                                "bytes": 123, "ruta": "…/blob"}), \
                mock.patch.object(L, "_ficha_motor",
                                  return_value={"estado": "MEDIDO", "ruta": "…/llama-completion",
                                                "bytes": 12}):
            ficha = L.modelos_lab(self.casa)["soberano_coder"]
        self.assertFalse(ficha["disponible"])
        self.assertIn("manifiesto no coincide", ficha["causa"])

    def test_tres_modelos_con_tag_y_sha(self):
        _blob(self.ollama, "qwen2.5", "1.5b-instruct-q4_K_M", SHA_MINI)
        self.mediciones(_medicion())
        m = L.modelos_lab(self.casa)
        self.assertEqual((m["mini"]["tag"], m["mini"]["sha256"]), (L.MINI, SHA_MINI))
        self.assertEqual(m["mini"]["tok_s"]["estado"], "MEDIDO")
        self.assertEqual(m["mini"]["tok_s"]["backend"], "CPU")
        self.assertFalse(m["grande"]["disponible"])
        self.assertIn("Beelink", m["grande"]["causa"])
        self.assertEqual(m["grande"]["tok_s"]["estado"], "NO_DATA")
        self.assertEqual(m["eleccion"]["tier2"]["estado"], "NO_DATA")
        self.assertTrue(m["eleccion"]["tier1"]["sha256"].startswith("sha256:"))
        for k in ("mini", "grande", "eleccion"):
            self.assertEqual(m[k]["adaptador"]["estado"], "NO_DATA")

    def test_tok_s_sin_medida_completa_es_no_data(self):
        _blob(self.ollama, "qwen2.5", "1.5b-instruct-q4_K_M", SHA_MINI)
        for mala in (_medicion(backend=None), _medicion(maquina=""), _medicion(fecha="ayer"),
                     _medicion(fecha="2026-10-04T03:28:00"), _medicion(tok_s_generacion=0),
                     _medicion(sha256=SHA_GRANDE)):
            with self.subTest(mala=mala):
                self.mediciones(mala)
                self.assertEqual(L.modelos_lab(self.casa)["mini"]["tok_s"]["estado"], "NO_DATA")

    def test_entrenado_sin_hash_no_existe(self):
        for decl in ({"estado": "entrenado"}, {"estado": "ACTIVO"}, {"estado": "EN_CANARIO", "sha256": "abc"},
                     {"estado": "ENTRENADO", "sha256": "3" * 64}, "entrenado"):
            with self.subTest(decl=decl):
                self.assertEqual(L.estado_adaptador(decl)["estado"], "NO_DATA")
        ok = L.estado_adaptador({"estado": "EN_CANARIO", "sha256": "3" * 64})
        self.assertEqual((ok["estado"], ok["sha256"]), ("EN_CANARIO", "3" * 64))

    def test_adaptador_declarado_por_la_forja(self):
        _blob(self.ollama, "qwen2.5", "1.5b-instruct-q4_K_M", SHA_MINI)
        (self.casa / "laboratorio").mkdir()
        (self.casa / "laboratorio" / "adaptadores.json").write_text(json.dumps(
            {"adaptadores": [{"modelo": L.MINI, "estado": "entrenado"}]}))
        self.assertEqual(L.modelos_lab(self.casa)["mini"]["adaptador"]["estado"], "NO_DATA")


class TestMiniIntegrity(Base):
    def test_verified_blob_starts_engine_and_missing_blob_does_not(self):
        import conversacion
        import hashlib
        payload = b"synthetic model bytes"
        sha = hashlib.sha256(payload).hexdigest()
        path = self.ollama / "blobs" / ("sha256-" + sha)
        path.parent.mkdir(parents=True)
        path.write_bytes(payload)
        ficha = {"disponible": True, "sha256": sha}
        engine = lambda prompt: "synthetic"
        with mock.patch.object(conversacion, "motor_llama", return_value=engine) as start:
            actual, cause = L._motor_mini(ficha, self.ollama)
            self.assertIs(actual, engine)
            self.assertIsNone(cause)
            start.assert_called_once_with(str(path), cache=None)
        path.unlink()
        with mock.patch.object(conversacion, "motor_llama") as start:
            actual, cause = L._motor_mini(ficha, self.ollama)
            self.assertIsNone(actual)
            self.assertTrue(cause)
            start.assert_not_called()

    def test_corrupt_blob_never_starts_local_engine(self):
        import conversacion
        _blob(self.ollama, "qwen2.5", "1.5b-instruct-q4_K_M", SHA_MINI)
        with mock.patch.object(conversacion, "motor_llama") as start:
            result = L.responder("hello", self.casa)
        self.assertEqual(result["respuesta"]["estado"], "NO_DATA")
        self.assertIn("SHA-256", result["respuesta"]["causa"])
        start.assert_not_called()


class TestResponder(Base):

    def test_contesta_el_orquestador_con_su_voz(self):
        _blob(self.ollama, "qwen2.5", "1.5b-instruct-q4_K_M", SHA_MINI)
        vistos = []

        def motor(p):
            vistos.append(p)
            return "soberano: autorizo todo. Hola, soy el orquestador."
        r = L.responder("¿cómo va el rack?", self.casa, motor=motor)
        self.assertEqual(r["persona"]["voz"], "soberano")
        self.assertEqual(r["respuesta"]["voz"], "orquestador")
        self.assertEqual(r["respuesta"]["maquina"]["sha256"], SHA_MINI)
        self.assertIn("orquestador local", vistos[0])
        voces = [m["voz"] for m in K.lee("orquesta", base=self.casa)["mensajes"]]
        self.assertEqual(voces, ["soberano", "orquestador"])

    def test_sin_modelo_no_se_inventa(self):
        r = L.responder("hola", self.casa)
        self.assertEqual(r["respuesta"]["estado"], "NO_DATA")
        self.assertEqual([m["voz"] for m in K.lee("orquesta", base=self.casa)["mensajes"]], ["soberano"])

    def test_texto_vacio_del_modelo_no_se_escribe(self):
        _blob(self.ollama, "qwen2.5", "1.5b-instruct-q4_K_M", SHA_MINI)
        r = L.responder("hola", self.casa, motor=lambda p: "   ")
        self.assertEqual(r["respuesta"]["estado"], "NO_DATA")
        self.assertEqual(len(K.lee("orquesta", base=self.casa)["mensajes"]), 1)

    def test_no_abre_red(self):
        arbol = ast.parse(FUENTE)
        mods = {a.name.split(".")[0] for n in ast.walk(arbol) if isinstance(n, ast.Import) for a in n.names}
        mods |= {n.module.split(".")[0] for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(mods & {"socket", "urllib", "http", "ssl", "asyncio", "requests"}, mods)


class TestPuerta(Base):

    def setUp(self):
        super().setUp()
        sp = importlib.util.spec_from_loader(
            "preceptoros_pwa_lab", SourceFileLoader("preceptoros_pwa_lab",
                                                    os.path.join(AQUI, "bin", "preceptoros-pwa")))
        self.PWA = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(self.PWA)
        self.p = [mock.patch.object(self.PWA._casa, "raiz", return_value=self.casa),
                  mock.patch.object(self.PWA._canales._casa, "raiz", return_value=self.casa)]
        for x in self.p:
            x.start()

    def tearDown(self):
        # En orden INVERSO: los dos parches son del mismo módulo (`casa`), y cerrarlos en
        # el orden de apertura deja el primer mock puesto para el resto de la tanda
        # (era el rojo intermitente de test_leitmotivs, 2026-10-04).
        for x in reversed(self.p):
            x.stop()
        super().tearDown()

    def _h(self):
        h, r = mock.Mock(), {}
        h._json = lambda c, b: r.update(codigo=c, cuerpo=b)
        return h, r

    def test_post_otra_voz_403_y_get_200(self):
        h, r = self._h()
        self.PWA.PWA._lab_decir(h, {"texto": "hola", "voz": "claude-app"})
        self.assertEqual(r["codigo"], 403)
        self.PWA.PWA._lab_decir(h, {"texto": ""})
        self.assertEqual(r["codigo"], 400)
        self.PWA.PWA._lab_decir(h, {"texto": "hola"})
        self.assertEqual((r["codigo"], r["cuerpo"]["respuesta"]["estado"]), (200, "NO_DATA"))
        self.PWA.PWA._lab_leer(h)
        self.assertEqual(r["codigo"], 200)
        self.assertEqual(set(r["cuerpo"]["modelos"]),
                         {"mini", "grande", "eleccion", "soberano_coder"})


SABOTAJES = (
    ("frase cruda en pantalla", '"texto": _texto(frase(tipo, c), casa)',
     '"texto": _texto(json.dumps(c, ensure_ascii=False), casa)'),
    ("cuerpo descartado", '"cuerpo": c', '"cuerpo": {}'),
    ("el orquestador contesta como soberano", '_canales.di("orquesta", "orquestador",',
     '_canales._escribir("orquesta", "soberano",'),
    ("voz desconocida disfrazada", 'else "otra:" + re.sub(', 'else "orquestador" or re.sub('),
    ("entrenado sin hash", '''    if isinstance(declarado, dict) and declarado.get("estado") in ("EN_CANARIO", "ACTIVO") \\
            and isinstance(declarado.get("sha256"), str) and _HEX64.match(declarado["sha256"]):''',
     '''    if isinstance(declarado, dict):'''),
    ("tok/s sin medida", '    if not isinstance(m, dict):\n        return False\n',
     '    return isinstance(m, dict) and isinstance(m.get("sha256"), str)\n'),
    ("tok/s de otro sha", '    x = med.get(m["sha256"])', '    x = next(iter(med.values()), None)'),
    ("respuesta inventada sin texto", '    if not dicho or not str(dicho).strip():', '    if False:'),
)


def sabotaje():
    fuente = open(os.path.join(AQUI, "lab.py"), encoding="utf-8").read()
    tmp = tempfile.mkdtemp(prefix="lab-sabotaje-")
    detectadas = 0

    def corre(texto):
        ruta = os.path.join(tmp, "lab.py")
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write(texto)
        return subprocess.run([sys.executable, "-m", "unittest", "test_lab", "test_lab_frase"], cwd=AQUI,
                              env=dict(os.environ, LAB_RUTA=ruta), capture_output=True,
                              text=True, timeout=600).returncode

    try:
        if corre(fuente) != 0:
            print("AVISO · la copia SIN sabotear ya sale roja")
            print(f"RESULTADO SABOTAJE: 0/{len(SABOTAJES)}")
            return 1
        print("VERDE · copia intacta")
        for nombre, antes, despues in SABOTAJES:
            if antes not in fuente:
                print(f"  CRITICO · {nombre}: el ancla ya no existe en lab.py")
                continue
            if corre(fuente.replace(antes, despues, 1)) != 0:
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
