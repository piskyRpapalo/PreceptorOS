#!/usr/bin/env python3
"""El puente de vuelta: lo que la web da, la app lo lee.

Y una prueba que no es de esta app: se lee `corregir.js` y `taller.js` del repo
de la WEB, si estan a mano, y se comprueba que los campos que escriben son los
que aqui se leen. Dos esquemas para el mismo hecho se separan en silencio --
nadie ve el momento en que el navegador anade un campo que aqui se tira--, y el
sitio donde eso se nota es el consentimiento.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import captura                                   # noqa: E402
import importar as I                             # noqa: E402
import memory as M                               # noqa: E402

WEB = os.path.expanduser("~/p0x/preceptoros-web/public/assets")


def par(prompt="que es un LoRA", respuesta="mal", correccion="bien",
        **extra):
    d = {"prompt": prompt, "respuesta": respuesta, "correccion": correccion,
         "corregido": "2026-09-08T10:00:00.000Z", "modelo": "Llama-3.2-3B",
         "idioma": "es", "motivo": "se invento una cifra", "consent": 0,
         "origen": "preceptoros.org"}
    d.update(extra)
    return d


def paquete(*correcciones, esquema=1):
    return {"esquema": esquema, "fecha": "2026-09-08T10:00:00.000Z",
            "maquina": {"ram": "NO_DATA"},
            "correcciones": list(correcciones)}


def firmada(p, firma="aa11", autor="TESTER-0747"):
    return {"par": p, "firma": firma, "autor": autor,
            "algoritmo": "Ed25519", "publica": "3d4f" * 16}


class TestImportar(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="imp_")
        self.db = os.path.join(self.dir, "m.db")
        M.crear(self.db)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def filas(self, c):
        return [dict(f) for f in c.execute("select * from turnos order by id")]

    # --- lo que entra -----------------------------------------------------

    def test_una_correccion_de_la_web_acaba_en_turnos(self):
        with M.abrir(self.db) as c:
            inf = I.importar(c, paquete(firmada(par())))
            self.assertEqual(inf["nuevas"], 1)
            f = self.filas(c)[0]
            self.assertEqual(f["prompt"], "que es un LoRA")
            self.assertEqual(f["respuesta"], "mal")
            self.assertEqual(f["correccion"], "bien")
            self.assertEqual(f["modelo"], "Llama-3.2-3B")
            self.assertEqual(f["idioma"], "es")
            self.assertEqual(f["motivo"], "se invento una cifra")

    def test_el_arnes_dice_web_y_es_lo_unico_que_se_afirma(self):
        """La columna que hace comparable un turno del navegador con uno de aqui.

        Sin ella los dos caen en la misma media, y la media de un modelo del
        navegador con la de uno del rack no describe a ninguno de los dos.
        """
        with M.abrir(self.db) as c:
            I.importar(c, paquete(firmada(par())))
            self.assertEqual(self.filas(c)[0]["arnes"], "web")

    def test_la_tarea_entra_como_NO_DATA_y_no_como_libre(self):
        """`libre` es una afirmacion --«no vino por un atajo»--, no un hueco.

        El paquete de la web no dice con que atajo se hizo el turno. Ponerle
        `libre` seria comodo y falso, y ademas envenenaria justo la consulta
        para la que se creo la columna: cuantos turnos vienen de cada atajo.
        """
        with M.abrir(self.db) as c:
            I.importar(c, paquete(firmada(par())))
            self.assertEqual(self.filas(c)[0]["tarea"], "NO_DATA")

    # --- la firma ---------------------------------------------------------

    def test_la_firma_se_guarda_y_NO_se_da_por_buena(self):
        """Ni 0 ni 1: nadie lo ha comprobado.

        La biblioteca estandar no trae Ed25519. Un `firma_ok = 0` diria «se
        comprobo y fallo»; un 1 mentiria. El unico valor cierto es el tercero.
        """
        with M.abrir(self.db) as c:
            inf = I.importar(c, paquete(firmada(par(), firma="beef")))
            f = self.filas(c)[0]
            self.assertEqual(f["firma"], "beef")
            self.assertEqual(f["autor"], "TESTER-0747")
            self.assertEqual(f["firma_ok"], "NO_DATA")
            self.assertEqual(inf["firmas_sin_verificar"], 1)

    def test_sin_firma_entra_pero_se_dice(self):
        with M.abrir(self.db) as c:
            inf = I.importar(c, paquete({"par": par()}))
            self.assertEqual(inf["nuevas"], 1)
            self.assertEqual(self.filas(c)[0]["firma"], "NO_DATA")
            self.assertTrue(any("sin firma" in s["motivo"]
                                for s in inf["saltadas"]))

    # --- el consentimiento ------------------------------------------------

    def test_el_consentimiento_se_copia_y_jamas_se_sube(self):
        """El sitio exacto donde un traductor en medio pierde un permiso."""
        with M.abrir(self.db) as c:
            I.importar(c, paquete(firmada(par(consent=0)),
                                  firmada(par(prompt="otro", consent=1),
                                          firma="bb22")))
            self.assertEqual([f["consent"] for f in self.filas(c)], [0, 1])

    # --- importar dos veces ------------------------------------------------

    def test_el_mismo_paquete_dos_veces_no_duplica(self):
        with M.abrir(self.db) as c:
            p = paquete(firmada(par()))
            I.importar(c, p)
            inf = I.importar(c, p)
            self.assertEqual(inf["nuevas"], 0)
            self.assertEqual(inf["repetidas"], 1)
            self.assertEqual(len(self.filas(c)), 1)

    def test_un_paquete_que_crecio_solo_mete_lo_nuevo(self):
        """El caso real: se corrigen dos respuestas mas y se pega otra vez."""
        with M.abrir(self.db) as c:
            I.importar(c, paquete(firmada(par())))
            inf = I.importar(c, paquete(
                firmada(par()),
                firmada(par(prompt="y esto?"), firma="cc33")))
            self.assertEqual((inf["nuevas"], inf["repetidas"]), (1, 1))
            self.assertEqual(len(self.filas(c)), 2)

    def test_sin_firma_la_llave_es_el_par_y_tampoco_duplica(self):
        with M.abrir(self.db) as c:
            p = paquete({"par": par()})
            I.importar(c, p)
            I.importar(c, p)
            self.assertEqual(len(self.filas(c)), 1)

    # --- lo que no entiende ------------------------------------------------

    def test_una_entrada_rota_se_salta_y_se_dice_cual(self):
        with M.abrir(self.db) as c:
            inf = I.importar(c, paquete(
                firmada(par()),
                {"par": par(prompt="")},
                "esto no es un objeto",
                {"sin_par": 1}))
            self.assertEqual(inf["nuevas"], 1)
            self.assertEqual(len(inf["saltadas"]), 3)
            self.assertEqual([s["n"] for s in inf["saltadas"]], [1, 2, 3])

    def test_un_texto_que_no_es_json_no_revienta(self):
        self.assertIsNone(I.leer("{roto"))
        self.assertIsNone(I.leer(""))
        self.assertIsNone(I.leer("[1,2,3]"))

    def test_un_esquema_que_no_se_conoce_se_rechaza(self):
        """Un paquete futuro puede tener los mismos nombres y otro significado.

        Eso es peor que uno que no se parezca en nada: entra sin ruido.
        """
        self.assertIsNone(I.leer(json.dumps(paquete(esquema=99))))

    def test_importar_None_devuelve_informe_vacio_sin_tocar_nada(self):
        """«Sin tocar nada» incluye no crear la tabla.

        La primera version de esta prueba leia `turnos` para comprobar que
        estaba vacia, y sqlite contesto que no existe. Tenia razon: un paquete
        ilegible no debe dejar rastro en la memoria, ni siquiera una tabla
        vacia. La prueba estaba mal, no el codigo.
        """
        with M.abrir(self.db) as c:
            inf = I.importar(c, None)
            self.assertEqual(inf["entradas"], 0)
            hay = c.execute("select name from sqlite_master where type='table' "
                            "and name='turnos'").fetchone()
            self.assertIsNone(hay, "un paquete ilegible creo la tabla")

    # --- la migracion ------------------------------------------------------

    def test_una_memoria_vieja_gana_las_columnas_sin_perder_sus_turnos(self):
        """Nadie empieza de cero porque el producto se actualice."""
        with M.abrir(self.db) as c:
            captura.asegurar(c)
            viejo = captura.registrar(c, "de antes", "respuesta de antes")
            self.assertIsNotNone(viejo)
        with M.abrir(self.db) as c:
            I.importar(c, paquete(firmada(par())))
            filas = self.filas(c)
            self.assertEqual(len(filas), 2)
            self.assertEqual(filas[0]["prompt"], "de antes")
            # El turno viejo no tenia procedencia y sigue sin tenerla: la
            # migracion declara el hueco, no lo rellena.
            self.assertEqual(filas[0]["origen"], "NO_DATA")
            self.assertEqual(filas[0]["firma_ok"], "NO_DATA")

    # --- el cruce con la web -----------------------------------------------

    def test_los_campos_son_LOS_MISMOS_que_escribe_el_navegador(self):
        """La prueba que solo puede fallar cuando alguien toca el otro repo.

        Se salta si la web no esta a mano --no todo el mundo la tiene clonada--
        pero cuando esta, cruza los dos lados. Un campo que el navegador
        empiece a escribir y aqui no se lea no da error en ningun sitio: se
        pierde, y se pierde callando.
        """
        js = os.path.join(WEB, "corregir.js")
        if not os.path.isfile(js):
            self.skipTest("el repo de la web no esta a mano")
        texto = open(js, encoding="utf-8").read()
        # El objeto que la web firma y guarda.
        cuerpo = texto.split("var reg = {", 1)[1].split("};", 1)[0]
        campos = {l.split(":", 1)[0].strip()
                  for l in cuerpo.splitlines() if ":" in l
                  and not l.strip().startswith("//")}
        leidos = {"prompt", "respuesta", "correccion", "corregido", "modelo",
                  "idioma", "motivo", "consent", "origen"}
        sin_leer = campos - leidos
        self.assertFalse(
            sin_leer,
            f"corregir.js escribe {sorted(sin_leer)} y este importador no los "
            "lee. Un campo que se pierde callando es como se separan dos "
            "esquemas que decian ser el mismo")

    def test_el_paquete_de_la_web_declara_el_esquema_que_aqui_se_acepta(self):
        js = os.path.join(WEB, "taller.js")
        if not os.path.isfile(js):
            self.skipTest("el repo de la web no esta a mano")
        texto = open(js, encoding="utf-8").read()
        self.assertIn("esquema: ap.esquema_paquete || 1", texto,
                      "el paquete de la web ya no declara esquema 1; revisar "
                      "ESQUEMAS en importar.py antes de que entre callando")
        self.assertIn("correcciones: pares", texto)


if __name__ == "__main__":
    unittest.main()
