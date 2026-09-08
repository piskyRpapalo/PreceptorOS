#!/usr/bin/env python3
"""El par completo, y el consentimiento que no se presume.

La que importa es la 4: capturar no es consentir. El dia que un turno entre al
dataset sin que nadie lo haya subido a 1, este producto habra dejado de cumplir
su primera promesa.
"""
from __future__ import annotations

import os
import sys
import shutil
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import captura
import memory


class TestCaptura(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.tmp.name, "memory.db")
        memory.crear(self.ruta)

    def tearDown(self):
        self.tmp.cleanup()

    def test_1_guarda_el_par_entero(self):
        """Lo que fallaba antes: la respuesta se guardaba sin su pregunta."""
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "hola, que es esto?", "Hablas conmigo.",
                                    modelo="qwen3-4b", idioma="es")
            self.assertIsNotNone(tid)
            fila = c.execute("select prompt, respuesta from turnos "
                             "where id = ?", (tid,)).fetchone()
        self.assertEqual(fila[0], "hola, que es esto?")
        self.assertEqual(fila[1], "Hablas conmigo.")

    def test_2_nace_sin_consentimiento(self):
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "p", "r")
            valor = c.execute("select consent from turnos where id = ?",
                              (tid,)).fetchone()[0]
        self.assertEqual(valor, 0)

    def test_3_solo_el_carbono_lo_sube(self):
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "p", "r")
            self.assertEqual(captura.pares(c), [])
            captura.consentir(c, tid, True, motivo="firmado")
            self.assertEqual(len(captura.pares(c)), 1)

    def test_4_capturar_no_es_consentir(self):
        """Diez turnos capturados no dan ni un solo par entrenable."""
        with memory.abrir(self.ruta) as c:
            for i in range(10):
                captura.registrar(c, f"p{i}", f"r{i}")
            self.assertEqual(captura.recuento(c)["turnos"], 10)
            self.assertEqual(captura.recuento(c)["consentidos"], 0)
            self.assertEqual(captura.pares(c), [])

    def test_5_el_consentimiento_se_puede_retirar(self):
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "p", "r")
            captura.consentir(c, tid, True)
            captura.consentir(c, tid, False, motivo="me arrepenti")
            self.assertEqual(captura.pares(c), [])

    def test_6_corregir_conserva_las_dos(self):
        """Borrar el original destruiria el par de preferencia."""
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "que recuerdas?", "Recuerdo muchas cosas.",
                                    idioma="es")
            captura.corregir(c, tid, "No tengo eso en tu memoria.",
                             motivo="relleno")
            captura.consentir(c, tid, True)
            par = captura.pares(c)[0]
        self.assertEqual(par["clase"], "preferencia")
        self.assertEqual(par["rechazado"], "Recuerdo muchas cosas.")
        self.assertEqual(par["elegido"], "No tengo eso en tu memoria.")
        self.assertEqual(par["motivo"], "relleno")

    def test_7_corregir_no_consiente(self):
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "p", "r")
            captura.corregir(c, tid, "otra cosa")
            self.assertEqual(captura.pares(c), [])

    def test_8_un_fallo_no_tumba_el_turno(self):
        """Se llama con la respuesta ya entregada: aqui no se puede levantar."""
        class Rota:
            def executescript(self, *a): raise RuntimeError("disco lleno")
            def execute(self, *a): raise RuntimeError("disco lleno")
        self.assertIsNone(captura.registrar(Rota(), "p", "r"))

    def test_9_se_puede_apagar(self):
        self.assertTrue(captura.activa({}))
        self.assertTrue(captura.activa({"captura": "si"}))
        self.assertFalse(captura.activa({"captura": "no"}))

    def test_10_memoria_vieja_recibe_la_tabla(self):
        """Migracion aditiva: una memoria anterior a esto no puede reventar."""
        with memory.abrir(self.ruta) as c:
            c.execute("drop table if exists turnos")
            self.assertIsNotNone(captura.registrar(c, "p", "r"))



# --- EL RASTRO DEL CONTEXTO -----------------------------------------------
# Sin el, «alucino» y «la busqueda no lo trajo» son la misma fila. Y piden
# arreglos opuestos: uno se cura con datos, el otro con recuperacion.


class TestRastroDelContexto(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="rastro_")
        self.db = os.path.join(self.dir, "m.db")
        memory.crear(self.db)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_guarda_que_engramas_viajaron(self):
        with memory.abrir(self.db) as c:
            for i in range(4):
                memory.escribir_engrama(c, what=f"rastro {i} " + "z" * 80)
            r = memory.recuperar(c, "rastro", presupuesto=100000)
            tid = captura.registrar(c, "una pregunta", "una respuesta",
                                    modelo="m", idioma="es", rastro=r)
            fila = c.execute("select ctx_ids, ctx_tokens, ctx_fuera, "
                             "ctx_completo from turnos where id=?",
                             (tid,)).fetchone()
        esperado = ",".join(str(e["id"]) for e in r["engramas"])
        self.assertEqual(fila[0], esperado, "no se anoto que engramas viajaron")
        self.assertEqual(fila[1], r["tokens"])
        self.assertEqual(fila[2], 0)
        self.assertEqual(fila[3], 1, "no se anoto que cabia todo")

    def test_un_turno_parcial_queda_marcado_como_parcial(self):
        """La fila tiene que poder decir «esto se contesto con la mitad»."""
        with memory.abrir(self.db) as c:
            for i in range(8):
                memory.escribir_engrama(c, what=f"parcial {i} " + "z" * 400)
            r = memory.recuperar(c, "parcial", presupuesto=300)
            tid = captura.registrar(c, "p", "r", rastro=r)
            fuera, completo = c.execute(
                "select ctx_fuera, ctx_completo from turnos where id=?",
                (tid,)).fetchone()
        self.assertGreater(fuera, 0, "no anota cuantos se quedaron fuera")
        self.assertEqual(completo, 0, "un turno parcial figura como completo")

    def test_sin_rastro_dice_NO_DATA_y_no_finge_un_cero(self):
        """Quien llame sin rastro sigue funcionando, y la fila lo declara."""
        with memory.abrir(self.db) as c:
            tid = captura.registrar(c, "p", "r")
            ids, tok = c.execute(
                "select ctx_ids, ctx_tokens from turnos where id=?",
                (tid,)).fetchone()
        self.assertEqual(ids, "NO_DATA", "un turno sin anotar finge tener rastro")
        self.assertIsNone(tok, "un cero aqui se leeria como «no viajo nada»")

    def test_migracion_aditiva_sobre_una_tabla_vieja(self):
        """Una memoria con turnos de antes del rastro no se rompe ni se vacia."""
        with memory.abrir(self.db) as c:
            c.executescript(captura.ESQUEMA_TURNOS)
            c.execute("insert into turnos (prompt, respuesta) values ('v','v')")
            c.commit()
            cols = {d[1] for d in c.execute("pragma table_info(turnos)")}
            self.assertNotIn("ctx_ids", cols, "la tabla ya trae la columna: "
                                              "este caso no prueba nada")
            captura.asegurar(c)
            captura.asegurar(c)          # dos veces no puede duplicar
            cols = [d[1] for d in c.execute("pragma table_info(turnos)")]
            n, = c.execute("select count(*) from turnos").fetchone()
        self.assertEqual(cols.count("ctx_ids"), 1)
        self.assertEqual(n, 1, "la migracion se llevo por delante un turno viejo")



# --- PRECEPTOR DE LoRAs ----------------------------------------------------
# La base tiene que poder contestar «como le fue al modelo X en la tarea Y».
# Sin vocabulario cerrado esa pregunta no tiene respuesta: tiene un group by
# sobre cadenas que alguien escribio a mano en cuatro sitios.


class TestPreceptorDeLoras(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="preceptor_")
        self.db = os.path.join(self.dir, "m.db")
        memory.crear(self.db)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_la_tarea_sale_de_los_comandos_de_la_web(self):
        """Los atajos de la web y las tareas de la app comparten vocabulario.

        Si divergen, un turno de una cara y otro de la otra dejan de ser
        comparables y nadie se entera: el `group by` sigue devolviendo filas.
        """
        import json
        ruta = os.path.expanduser(
            "~/p0x/preceptoros-web/public/servicios.json")
        if not os.path.exists(ruta):
            self.skipTest("la web no esta en este arbol")
        with open(ruta, encoding="utf-8") as f:
            comandos = {s["comando"].lstrip("/")
                        for s in json.load(f)["servicios"]}
        faltan = comandos - set(captura.TAREAS)
        self.assertEqual(faltan, set(),
                         f"la web tiene atajos que la app no sabe etiquetar: {faltan}")

    def test_una_etiqueta_de_fuera_del_vocabulario_cae_a_NO_DATA(self):
        """No se levanta --se perderia el turno-- y no se acepta tal cual."""
        with memory.abrir(self.db) as c:
            tid = captura.registrar(c, "p", "r", tarea="INSTALAR  ", arnes="movil")
            tarea, arnes = c.execute(
                "select tarea, arnes from turnos where id=?", (tid,)).fetchone()
        self.assertEqual(tarea, "instalar", "no normaliza mayusculas ni espacios")
        self.assertEqual(arnes, "NO_DATA", "cuela un arnes inventado")

    def test_callarse_bien_CUENTA_COMO_ACIERTO(self):
        """La doctrina, dentro del esquema.

        Un banco que puntue `no_data` y `traspaso` como fallo entrena al modelo
        a inventar antes que a callarse -- justo el comportamiento que esta casa
        combate. Si este caso cae, el vocabulario dejo de defender la doctrina.
        """
        self.assertIn("no_data", captura.ACIERTOS)
        self.assertIn("traspaso", captura.ACIERTOS)
        self.assertNotIn("mudo", captura.ACIERTOS,
                         "rendirse teniendo el dato delante no es acertar")
        self.assertNotIn("alucinacion", captura.ACIERTOS)

    def test_sin_juzgar_NO_es_fallado(self):
        """Un modelo nuevo no puede sacar mala nota por ser nuevo."""
        with memory.abrir(self.db) as c:
            for _ in range(9):
                captura.registrar(c, "p", "r", modelo="nuevo:v1", tarea="libre")
            filas = captura.rendimiento(c)
        f = filas[0]
        self.assertEqual(f["turnos"], 9)
        self.assertEqual(f["juzgados"], 0)
        self.assertIsNone(f["tasa"],
                          "sin un solo juicio la tasa no puede ser un numero: "
                          "un cero se leeria como «fallo todo»")

    def test_la_tasa_se_calcula_sobre_los_JUZGADOS(self):
        with memory.abrir(self.db) as c:
            ids = [captura.registrar(c, f"p{i}", "r", modelo="m:v1",
                                     tarea="instalar") for i in range(10)]
            captura.juzgar(c, ids[0], "acierto", juez="carbono")
            captura.juzgar(c, ids[1], "no_data", juez="carbono")
            captura.juzgar(c, ids[2], "traspaso", juez="carbono")
            captura.juzgar(c, ids[3], "alucinacion", juez="carbono")
            filas = captura.rendimiento(c)
        f = filas[0]
        self.assertEqual(f["juzgados"], 4)
        self.assertEqual(f["aciertos"], 3, "no cuenta callarse bien como acierto")
        self.assertAlmostEqual(f["tasa"], 0.75)
        self.assertEqual(f["alucinaciones"], 1)

    def test_un_veredicto_inventado_no_borra_uno_bueno(self):
        with memory.abrir(self.db) as c:
            tid = captura.registrar(c, "p", "r")
            self.assertTrue(captura.juzgar(c, tid, "acierto", juez="carbono"))
            self.assertFalse(captura.juzgar(c, tid, "regular", juez="carbono"),
                             "acepto un veredicto fuera del vocabulario")
            v, = c.execute("select veredicto from turnos where id=?",
                           (tid,)).fetchone()
        self.assertEqual(v, "acierto", "un veredicto invalido piso al bueno")

    def test_el_juez_viaja_con_el_veredicto(self):
        """Un veredicto sin juez es una opinion con cara de medida."""
        with memory.abrir(self.db) as c:
            tid = captura.registrar(c, "p", "r")
            captura.juzgar(c, tid, "fallo", juez="qwen3-coder:30b", motivo="cifra")
            v, j, m, cuando = c.execute(
                "select veredicto, juez, motivo, juzgado from turnos where id=?",
                (tid,)).fetchone()
        self.assertEqual((v, j, m), ("fallo", "qwen3-coder:30b", "cifra"))
        self.assertIsNotNone(cuando, "no anota cuando se juzgo")

    def test_el_contexto_va_al_lado_de_la_nota(self):
        """Tasa baja + mucho fuera = la busqueda, no el modelo.

        Es la diferencia entre entrenar un LoRA y arreglar una consulta, y
        separadas esas dos columnas no se ve.
        """
        with memory.abrir(self.db) as c:
            for i in range(6):
                memory.escribir_engrama(c, what=f"ancho {i} " + "z" * 400)
            r = memory.recuperar(c, "ancho", presupuesto=300)
            tid = captura.registrar(c, "p", "r", modelo="m:v1", tarea="libre",
                                    rastro=r)
            captura.juzgar(c, tid, "mudo", juez="carbono")
            f = captura.rendimiento(c)[0]
        self.assertGreater(f["ctx_fuera_medio"], 0,
                           "no se ve que la busqueda dejo cosas fuera")
        self.assertEqual(f["parciales"], 1)
        self.assertEqual(f["mudos"], 1)



class TestElCableConduce(unittest.TestCase):
    """De punta a punta: la conversacion compone, y el turno queda anotado.

    Las piezas ya tenian su caso cada una y aun asi el rastro no llegaba: nadie
    pasaba `rastro=`. Una cadena probada por tramos y nunca entera es como se
    construye un instrumento que devuelve NO_DATA para siempre sin que nada
    falle.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="cable_")
        self.db = os.path.join(self.dir, "m.db")
        memory.crear(self.db)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_lo_que_compuso_el_contexto_es_lo_que_queda_anotado(self):
        import herramientas as H
        with memory.abrir(self.db) as c:
            # CUATRO y no seis: los candidatos los acota `herramientas.LIMITE`
            # (5), asi que con seis engramas uno no llega ni a competir y la
            # cuenta de `fuera` --que es «de lo que la busqueda trajo, esto no
            # cupo»-- dejaria de ser exacta. La prueba se ajusta a la
            # invariante real en vez de doblar el codigo para que cuadre.
            for i in range(4):
                memory.escribir_engrama(c, what=f"melocoton {i} " + "z" * 200,
                                        why="para probar el cable")
            bloque, rastro = H.recuperar(c, "melocoton", con_rastro=True)
            self.assertTrue(bloque, "el compositor no puso nada delante")
            tid = captura.registrar(c, "melocoton?", "una respuesta",
                                    rastro=rastro, arnes="app", tarea="libre")
            ids, fuera, completo = c.execute(
                "select ctx_ids, ctx_fuera, ctx_completo from turnos where id=?",
                (tid,)).fetchone()

        anotados = [x for x in ids.split(",") if x.isdigit()]
        self.assertTrue(anotados, "el turno quedo sin rastro pese a haber contexto")
        # Y los anotados son EXACTAMENTE los que sobrevivieron al recorte: cada
        # uno tiene que asomar en el bloque que se mando.
        with memory.abrir(self.db) as c:
            for sid in anotados:
                que = memory.leer_engrama(c, int(sid))["what"]
                self.assertIn(que[:24], bloque,
                              f"el engrama {sid} figura como enviado y no esta "
                              "en el bloque que viajo")
        self.assertEqual(fuera, 4 - len(anotados),
                         "la cuenta de los que no cupieron no cuadra")
        self.assertEqual(completo, 1 if fuera == 0 else 0)

    def test_sin_personalizada_el_rastro_es_None_y_no_un_cero(self):
        """Apagar el interruptor no es «la memoria no encontro nada»."""
        with memory.abrir(self.db) as c:
            memory.escribir_engrama(c, what="algo que si estaba ahi")
            tid = captura.registrar(c, "p", "r", rastro=None)
            ids, tok = c.execute(
                "select ctx_ids, ctx_tokens from turnos where id=?",
                (tid,)).fetchone()
        self.assertEqual(ids, "NO_DATA")
        self.assertIsNone(tok, "un cero se leeria como «no viajo nada»")


if __name__ == "__main__":
    unittest.main(verbosity=2)
