"""Regresión P02: cuerpos de canal, sin bases vivas."""
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import canales

class ContratoCanal(unittest.TestCase):
    def test_superficie_rechaza_1024(self):
        import estado_app
        from unittest.mock import patch
        with patch.object(estado_app, 'validar', return_value=True):
            with self.assertRaises(ValueError):
                estado_app.serializar('x' * 1022)

    def test_canal_rechaza_1024_sin_escribir(self):
        cuerpo = {'hilo': 'app', 'texto': '', 'rol': '', 'sello': 'DECLARADO', 'maquina': {}}
        tamaño_base = len(json.dumps(cuerpo, ensure_ascii=False, sort_keys=True).encode('utf-8'))
        texto = 'x' * (1024 - tamaño_base)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / 'casa'
            with patch.object(canales, '_registro', return_value=None), patch.object(canales, '_limpio', side_effect=lambda texto, casa: texto):
                with self.assertRaises(canales.CanalRechazado):
                    canales.di('app', 'agente', texto, base=base)
            self.assertFalse((base / 'registro' / 'eventos.db').exists())

    def test_traduccion_no_concede_autoridad(self):
        import aiact_art12_canal as C
        for sello in ['MEDIDO', 'EMULADO', 'REQUIERE_FIRMA', 'DECLARADO']:
            resultado = C.traducir('canal', sello)
            self.assertEqual(resultado['sello'], 'NO_DATA')
            self.assertEqual(resultado['sello_original'], sello)
            self.assertIs(resultado['autoridad'], False)
            self.assertTrue(resultado['causa'])
        resultado = C.traducir('web', 'FIRMADO')
        self.assertEqual(resultado['sello'], 'FIRMADO')
        self.assertIs(resultado['autoridad'], False)
        with self.assertRaises(ValueError):
            C.traducir('canal', 'FIRMADO')

    def test_superficie_fronteras_completas(self):
        import estado_app
        from test_estado_app import estado_base
        for prefijo in ('x', 'é'):
            for tamaño in (1023, 1024, 1025):
                estado = estado_base()
                estado['guion']['titulo'] = prefijo
                actual = len(json.dumps(estado, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8'))
                q, r = divmod(tamaño - actual, 6)
                estado['guion']['titulo'] += chr(1) * q + 'a' * r
                bruto = json.dumps(estado, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
                assert len(bruto) == tamaño
                estado_app.validar(estado)
                if tamaño == 1023:
                    assert estado_app.serializar(estado) == bruto
                    assert estado_app.deserializar(bruto) == estado
                else:
                    with self.assertRaises(ValueError):
                        estado_app.serializar(estado)
                    with self.assertRaises(ValueError):
                        estado_app.deserializar(bruto)


    def test_cuerpo_cerrado_y_reproducible(self):
        import aiact_art12_canal as C
        cuerpo = dict(hilo="lab", texto="prueba", rol="", sello="DECLARADO", maquina={})
        esperado = json.dumps(cuerpo, ensure_ascii=False, sort_keys=True)
        self.assertEqual(C.serializar(cuerpo), esperado)
        self.assertEqual(C.serializar(json.loads(esperado)), esperado)
        malos = [dict(cuerpo, extra=1), {k: v for k, v in cuerpo.items() if k != "rol"},
                 dict(cuerpo, texto=" "), dict(cuerpo, texto="\ud800"),
                 dict(cuerpo, sello="FIRMADO"), dict(cuerpo, hilo="otro"),
                 dict(cuerpo, rol="r" * 121), dict(cuerpo, maquina=[])]
        malos += [dict(cuerpo, maquina={"valor": n}) for n in
                  (float("nan"), float("inf"), -float("inf"))]
        malos += [dict(cuerpo, maquina={1: "clave"}), dict(cuerpo, maquina={"v": (1, 2)})]
        for malo in malos:
            with self.subTest(caso=repr(malo)), self.assertRaises(ValueError):
                C.serializar(malo)

    def test_tabla_unica_cerrada_contra_matriz(self):
        import aiact_art12_canal as C
        esperado = {
            "canal": dict.fromkeys(("MEDIDO", "EMULADO", "REQUIERE_FIRMA", "DECLARADO")),
            "p02": {s: s for s in ("LIVE", "STALE", "STATIC", "SIMULATED", "NO_DATA", "ERROR")},
            "web": {s: s for s in ("LIVE", "PROPUESTA", "FIRMADO", "ERROR", "NO_DATA", "SIMULATED", "STALE")},
        }
        esperado["canal"].update(NO_DATA="NO_DATA", PROPUESTA="PROPUESTA")
        for origen, mapa in esperado.items():
            filas = C._filas(origen)
            self.assertEqual(len(filas), len(mapa))
            self.assertEqual({f["const"]: f["x-destino"] for f in filas}, mapa)
        self.assertEqual(set(esperado["canal"]), set(canales.SELLOS))
        esquema = json.loads((Path(__file__).parent / "data/aiact_art12_mensaje.schema.json").read_text())
        self.assertFalse(esquema["additionalProperties"])
        self.assertEqual(esquema["x-max-utf8-exclusive"], C.MAX_BYTES)
        self.assertEqual(esquema["properties"]["sello"], {"$ref": "aiact_art12_sellos.json#/$defs/canal"})
        self.assertEqual(set(esquema["required"]), {"hilo", "texto", "rol", "sello", "maquina"})

    def test_traduccion_causa_y_sin_color_ni_firma(self):
        import aiact_art12_canal as C
        for origen in ("canal", "p02", "web"):
            dato = C.traducir(origen, "NO_DATA", "sensor_ausente")
            self.assertEqual(dato["causa"], "sensor_ausente")
            self.assertIs(dato["autoridad"], False)
            with self.assertRaises(ValueError):
                C.traducir(origen, "NO_DATA")
        dato = C.traducir("p02", "STATIC")
        self.assertEqual(dato["causa"], "etiqueta_textual_sin_color")
        self.assertEqual(set(dato), {"origen", "sello_original", "sello", "causa", "autoridad"})
        for args in (("web", "STATIC"), ("otro", "LIVE"), ("p02", None),
                     ("p02", "LIVE", 3), ("p02", "LIVE", " "),
                     ("p02", "LIVE", "\ud800"), ("p02", "LIVE", "x" * 1024)):
            with self.subTest(args=repr(args)), self.assertRaises(ValueError):
                C.traducir(*args)

    def test_lectura_heredada_rechaza_sin_migrar(self):
        import sqlite3
        import hashlib
        with tempfile.TemporaryDirectory() as tmp, patch.object(canales, "_registro", return_value=None):
            base = Path(tmp)
            canales.di("app", "agente", "válido", base=base)
            db = canales.ruta_canal(base)
            cuerpo = dict(hilo="app", texto="x" * 1024, rol="", sello="DECLARADO", maquina={})
            malos = [json.dumps(cuerpo), "[]", "{}", "{truncado",
                     json.dumps(dict(cuerpo, texto="finito", maquina={"v": float("nan")}))]
            with sqlite3.connect(db) as con:
                for crudo in malos:
                    con.execute("insert into eventos (ts,maquina,tipo,actor,cuerpo_json,no_data_json) values (?,?,?,?,?,?)",
                                ("t", "fixture", "mensaje", "agente", crudo, "[]"))
            antes = hashlib.sha256(db.read_bytes()).hexdigest()
            leido = canales.lee("app", base=base)
            self.assertEqual(leido["corruptas"], len(malos))
            self.assertEqual([m["texto"] for m in leido["mensajes"]], ["válido"])
            self.assertTrue(leido["causa"])
            self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(), antes)


    def test_canal_fronteras_y_base_existente(self):
        import sqlite3
        for existente in (False, True):
            for prefijo in ("x", "é"):
                for tamaño in (1023, 1024, 1025):
                    with self.subTest(existente=existente, prefijo=prefijo, tamaño=tamaño):
                        with tempfile.TemporaryDirectory() as tmp, patch.object(canales, "_registro", return_value=None):
                            base = Path(tmp) / "casa"
                            if existente:
                                canales.di("app", "agente", "inicio", base=base)
                            db = canales.ruta_canal(base)
                            antes = db.read_bytes() if db.exists() else None
                            cuerpo = dict(hilo="app", texto=prefijo, rol="", sello="DECLARADO", maquina={})
                            crudo = json.dumps(cuerpo, ensure_ascii=False, sort_keys=True)
                            cuerpo["texto"] += "x" * (tamaño - len(crudo.encode("utf-8")))
                            with patch.object(canales, "_registro", return_value=None) as registro:
                                if tamaño < 1024:
                                    canales.di("app", "agente", cuerpo["texto"], base=base)
                                else:
                                    with self.assertRaises(canales.CanalRechazado):
                                        canales.di("app", "agente", cuerpo["texto"], base=base)
                                    registro.assert_not_called()
                            if tamaño < 1024:
                                with sqlite3.connect(db) as con:
                                    guardado = con.execute("select cuerpo_json from eventos order by n desc limit 1").fetchone()[0]
                                self.assertEqual(len(guardado.encode("utf-8")), tamaño)
                                self.assertEqual(canales.lee("app", base=base)["mensajes"][-1]["texto"], cuerpo["texto"])
                            elif existente:
                                self.assertEqual(db.read_bytes(), antes)
                            else:
                                self.assertFalse(base.exists())

if __name__ == "__main__":
    unittest.main()
