#!/usr/bin/env python3
"""El registro que no se puede reescribir sin que se note.

La prueba que importa es la del SABOTEADOR: se escribe una linea legitima, se
manipula una fila por debajo --como haria quien quiere arreglar un registro
incomodo-- y se exige que `verificar` lo cace y diga donde. Sin esa prueba,
«registro a prueba de manipulacion» es una frase.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import linea as L                                # noqa: E402
import memory as M                               # noqa: E402


class TestLinea(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="linea_")
        self.db = os.path.join(self.dir, "m.db")
        M.crear(self.db)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def llenar(self, c, n=3):
        return [L.anotar(c, "turno", f"turno:{i}", {"n": i}, "carbono")
                for i in range(n)]

    # --- la cadena ---------------------------------------------------------

    def test_el_primero_engancha_con_GENESIS(self):
        with M.abrir(self.db) as c:
            L.anotar(c, "turno", "turno:1")
            f = c.execute("select anterior from eventos").fetchone()
            self.assertEqual(f[0], L.GENESIS)

    def test_cada_evento_lleva_dentro_la_huella_del_anterior(self):
        with M.abrir(self.db) as c:
            self.llenar(c, 3)
            filas = list(c.execute(
                "select anterior, huella from eventos order by id"))
            for i in range(1, len(filas)):
                self.assertEqual(filas[i][0], filas[i - 1][1],
                                 "un eslabon no engancha con el anterior")

    def test_una_linea_recien_escrita_verifica(self):
        with M.abrir(self.db) as c:
            self.llenar(c, 5)
            ok, roto, n = L.verificar(c)
            self.assertTrue(ok)
            self.assertIsNone(roto)
            self.assertEqual(n, 5)

    def test_una_linea_vacia_verifica_y_no_es_un_fallo(self):
        """Cero eventos no es una linea rota: es una linea que no ha empezado."""
        with M.abrir(self.db) as c:
            self.assertEqual(L.verificar(c), (True, None, 0))

    # --- el saboteador -----------------------------------------------------

    def test_cambiar_un_evento_viejo_se_CAZA_y_se_dice_donde(self):
        """El caso real: alguien arregla la fila incomoda por debajo."""
        with M.abrir(self.db) as c:
            self.llenar(c, 5)
        with M.abrir(self.db) as c:
            c.execute("update eventos set datos = ? where id = 3",
                      (json.dumps({"n": 999}),))
        with M.abrir(self.db) as c:
            ok, roto, n = L.verificar(c)
            self.assertFalse(ok, "se manipulo un evento y la linea dio por buena")
            self.assertEqual(roto, 3, "no senala el evento manipulado")

    def test_cambiar_el_ACTOR_tambien_se_caza(self):
        """Reetiquetar quien hizo algo es la manipulacion mas barata y util.

        Pasar un evento de «modelo» a «carbono» convierte una propuesta en una
        decision humana. Si el actor no entrara en la huella, ese cambio seria
        invisible -- y es exactamente el que un auditor busca.
        """
        with M.abrir(self.db) as c:
            self.llenar(c, 3)
        with M.abrir(self.db) as c:
            # A «modelo», no a «carbono»: `llenar` ya escribe carbono, asi que
            # la primera version de esta prueba hacia un update que no cambiaba
            # nada y luego se sorprendia de que la cadena cuadrara. Una prueba
            # que no altera lo que dice alterar pasa siempre, y por el motivo
            # equivocado -- que es la unica forma de fallo que una prueba de
            # manipulacion no puede permitirse.
            c.execute("update eventos set actor='modelo' where id = 2")
        with M.abrir(self.db) as c:
            ok, roto, _ = L.verificar(c)
            self.assertFalse(ok)
            self.assertEqual(roto, 2)

    def test_cambiar_la_FECHA_tambien_se_caza(self):
        with M.abrir(self.db) as c:
            self.llenar(c, 3)
        with M.abrir(self.db) as c:
            c.execute("update eventos set cuando='2020-01-01T00:00:00.000Z' "
                      "where id = 2")
        with M.abrir(self.db) as c:
            self.assertFalse(L.verificar(c)[0])

    def test_borrar_un_evento_del_medio_se_caza(self):
        with M.abrir(self.db) as c:
            self.llenar(c, 5)
        with M.abrir(self.db) as c:
            c.execute("delete from eventos where id = 3")
        with M.abrir(self.db) as c:
            ok, roto, _ = L.verificar(c)
            self.assertFalse(ok, "se borro un eslabon y la linea dio por buena")
            self.assertEqual(roto, 4, "senala el que quedo colgando")

    def test_el_LIMITE_es_real_reescribir_la_cadena_entera_cuadra(self):
        """La prueba que demuestra lo que esto NO garantiza.

        Quien pueda escribir en el fichero puede rehacer la cadena entera y
        volver a encadenarla, y entonces verifica. Esto se prueba a proposito:
        una suite que solo ensena lo que la pieza detecta deja creer que
        detecta todo, y el modulo tendria una promesa mas ancha que su codigo.

        Contra esto no hay hash que valga -- hace falta un ancla externa o una
        firma con clave, y las dos estan declaradas como hueco.
        """
        with M.abrir(self.db) as c:
            self.llenar(c, 3)
        with M.abrir(self.db) as c:
            # El saboteador cuidadoso: cambia el dato Y rehace lo que sigue.
            filas = [dict(zip(
                ("id", "cuando", "tipo", "sujeto", "datos", "actor",
                 "anterior", "huella"), f))
                for f in c.execute("select id,cuando,tipo,sujeto,datos,actor,"
                                   "anterior,huella from eventos order by id")]
            filas[1]["datos"] = json.dumps({"n": 999})
            anterior = L.GENESIS
            for f in filas:
                h = L._huella(f["tipo"], f["sujeto"], f["datos"], f["actor"],
                              f["cuando"], anterior)
                c.execute("update eventos set datos=?, anterior=?, huella=? "
                          "where id=?", (f["datos"], anterior, h, f["id"]))
                anterior = h
        with M.abrir(self.db) as c:
            self.assertTrue(L.verificar(c)[0],
                            "la prueba esta mal montada: deberia cuadrar")
            self.assertIn("999", c.execute(
                "select datos from eventos where id=2").fetchone()[0])

    # --- el vocabulario ----------------------------------------------------

    def test_un_tipo_que_no_existe_no_entra_y_lo_dice(self):
        """Con tipo libre, «que paso con el consentimiento» no tiene respuesta."""
        with M.abrir(self.db) as c:
            with self.assertRaises(L.NoSePudoAnotar):
                L.anotar(c, "loquesea", "x")

    def test_un_evento_sin_sujeto_no_entra(self):
        with M.abrir(self.db) as c:
            with self.assertRaises(L.NoSePudoAnotar):
                L.anotar(c, "turno", "  ")

    def test_un_actor_desconocido_cae_a_NO_DATA_en_vez_de_tumbar(self):
        """El actor es una etiqueta; el tipo es la estructura.

        Una etiqueta mal puesta no puede costar el evento entero -- perder el
        registro es peor que registrarlo con el actor sin declarar.
        """
        with M.abrir(self.db) as c:
            L.anotar(c, "turno", "t:1", None, "el vecino")
            self.assertEqual(
                c.execute("select actor from eventos").fetchone()[0], "NO_DATA")

    def test_anotar_LEVANTA_y_no_devuelve_None(self):
        """La diferencia deliberada con `captura.registrar`.

        Alli no levantar es correcto: se la llama con la respuesta ya en
        pantalla. Aqui, un evento de auditoria que falla en silencio deja al
        sistema funcionando COMO SI hubiera quedado registro.
        """
        with M.abrir(self.db) as c:
            self.assertTrue(issubclass(L.NoSePudoAnotar, Exception))
            with self.assertRaises(L.NoSePudoAnotar):
                L.anotar(c, "no_existe", "x")

    # --- el pliegue --------------------------------------------------------

    def test_el_estado_es_el_pliegue_y_el_pasado_sigue_ahi(self):
        """Rectificar no pisa: escribe encima en la linea, no en la celda."""
        with M.abrir(self.db) as c:
            L.anotar(c, "consentimiento", "perfil:consent",
                     {"valor": 1}, "carbono")
            L.anotar(c, "revocacion", "perfil:consent",
                     {"valor": 0, "motivo": "me lo pense mejor"}, "carbono")
            p = L.pliegue(c, "perfil:consent")
            self.assertEqual(p["estado"]["valor"], 0)
            self.assertEqual(p["estado"]["motivo"], "me lo pense mejor")
            # Y el consentimiento viejo NO desaparecio: sigue en la linea.
            self.assertEqual(len(L.tramo(c, sujeto="perfil:consent")), 2)

    def test_el_pliegue_dice_DE_DONDE_sale_cada_valor(self):
        """Sin procedencia, el pliegue seria otra celda mas."""
        with M.abrir(self.db) as c:
            L.anotar(c, "veredicto", "turno:7", {"v": "acierto"}, "modelo")
            p = L.pliegue(c, "turno:7")
            self.assertEqual(p["origen"]["v"]["actor"], "modelo")
            self.assertEqual(p["origen"]["v"]["tipo"], "veredicto")

    # --- el tramo, que es lo que dibujara la barra --------------------------

    def test_el_tramo_recorta_por_fecha(self):
        """Sin contar filas: tres eventos seguidos caen en el mismo milisegundo.

        La primera version exigia «dos de tres» y salio 3, porque `strftime`
        da milisegundos y tres `insert` seguidos comparten el mismo. No es un
        defecto: el orden lo garantiza el `id`, que es monotono, y la cadena de
        huellas lo sella. Lo que estaba mal era la prueba, que contaba filas en
        vez de comprobar la propiedad -- que todo lo devuelto cae dentro.
        """
        with M.abrir(self.db) as c:
            self.llenar(c, 3)
            corte = L.tramo(c)[1]["cuando"]
            desde = L.tramo(c, desde=corte)
            self.assertTrue(desde)
            for e in desde:
                self.assertGreaterEqual(e["cuando"], corte)
            hasta = L.tramo(c, hasta=corte)
            self.assertTrue(hasta)
            for e in hasta:
                self.assertLessEqual(e["cuando"], corte)

    def test_la_fecha_se_ordena_como_texto_porque_es_ISO(self):
        """Por eso `cuando` no es un epoch: un auditor consulta a mano."""
        with M.abrir(self.db) as c:
            self.llenar(c, 4)
            fechas = [e["cuando"] for e in L.tramo(c)]
            self.assertEqual(fechas, sorted(fechas))
            for f in fechas:
                self.assertRegex(f, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


class TestElCirculoCerrado(unittest.TestCase):
    """El recorrido entero de un dato, y su rastro.

    Esto no prueba una funcion: prueba que el producto DEJA LINEA. Una pieza de
    registro que existe y que nadie llama es una capacidad, no un control -- y
    la diferencia es justo la que un auditor viene a comprobar.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="circulo_")
        self.db = os.path.join(self.dir, "m.db")
        M.crear(self.db)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_la_vida_entera_de_un_turno_queda_en_la_linea(self):
        import captura
        with M.abrir(self.db) as c:
            tid = captura.registrar(c, "que ocupa el modelo", "unos 200 gigas",
                                    modelo="qwen3:4b", idioma="es")
            captura.juzgar(c, tid, "alucinacion", juez="carbono",
                           motivo="se invento la cifra")
            captura.corregir(c, tid, "4,4 GB, del catalogo firmado",
                             motivo="cifra sin respaldo")
            captura.consentir(c, tid, True, motivo="puede entrenar")
            captura.consentir(c, tid, False, motivo="me lo pense mejor")

        with M.abrir(self.db) as c:
            eventos = L.tramo(c, sujeto=f"turno:{tid}")
            tipos = [e["tipo"] for e in eventos]
            self.assertEqual(
                tipos, ["veredicto", "correccion", "consentimiento",
                        "revocacion"],
                "el recorrido no dejo los cuatro eventos, en orden")
            ok, roto, n = L.verificar(c)
            self.assertTrue(ok, f"la linea no verifica, roto en {roto}")
            self.assertEqual(n, 4)

    def test_el_estado_final_sale_de_plegar_y_el_camino_sigue_ahi(self):
        """Consentir y luego revocar deja 0 -- y las dos cosas siguen escritas.

        Es la propiedad entera: la celda diria «0», que es verdad y no es toda
        la verdad. La linea dice ademas que hubo un si antes, cuando, y por que
        se retiro. Ante el art. 12 eso es la diferencia entre un dato y un
        registro.
        """
        import captura
        with M.abrir(self.db) as c:
            tid = captura.registrar(c, "hola", "que tal")
            captura.consentir(c, tid, True, motivo="adelante")
            captura.consentir(c, tid, False, motivo="mejor no")
        with M.abrir(self.db) as c:
            p = L.pliegue(c, f"turno:{tid}")
            self.assertEqual(p["estado"]["consent"], 0)
            self.assertEqual(p["estado"]["motivo"], "mejor no")
            self.assertEqual(len(L.tramo(c, sujeto=f"turno:{tid}")), 2)
            self.assertEqual(
                c.execute("select consent from turnos where id=?",
                          (tid,)).fetchone()[0], 0,
                "la tabla y la linea tienen que decir lo mismo")

    def test_el_juez_se_traduce_a_su_CLASE_de_evidencia(self):
        """Un script que compara contra el dato real no vale lo que un modelo.

        La columna guarda el juez tal cual --tag completo del modelo-- y la
        linea guarda su clase, que es lo que hace comparables dos veredictos.
        """
        import captura
        casos = [("carbono", "carbono"), ("qwen3-coder:30b", "modelo"),
                 ("determinista:hash", "determinista"), ("NO_DATA", "NO_DATA")]
        with M.abrir(self.db) as c:
            for juez, esperado in casos:
                tid = captura.registrar(c, f"p{juez}", "r")
                captura.juzgar(c, tid, "acierto", juez=juez)
                e = L.tramo(c, sujeto=f"turno:{tid}")[0]
                self.assertEqual(e["actor"], esperado, f"juez {juez}")

    def test_una_importacion_deja_su_procedencia(self):
        import importar
        paquete = {"esquema": 1, "correcciones": [{
            "par": {"prompt": "p", "respuesta": "r", "origen": "preceptoros.org"},
            "firma": "abc123", "autor": "TESTER-0747"}]}
        with M.abrir(self.db) as c:
            inf = importar.importar(c, paquete)
            self.assertEqual(inf["nuevas"], 1)
            e = L.tramo(c)[0]
            self.assertEqual(e["tipo"], "importacion")
            d = json.loads(e["datos"])
            self.assertEqual(d["firma"], "abc123")
            self.assertEqual(d["autor"], "TESTER-0747")
            # Y la firma NO se da por buena aqui tampoco: si el registro dijera
            # que si y la tabla que no se sabe, el registro seria el que miente.
            self.assertEqual(d["firma_ok"], "NO_DATA")

    def test_el_texto_corregido_NO_se_duplica_en_la_linea(self):
        """La linea registra QUE PASO, no es una segunda copia de la memoria.

        Si el texto viviera aqui, borrar una correccion de la memoria dejaria
        su contenido vivo para siempre en un sitio que no se puede rectificar.
        """
        import captura
        secreto = "esto no debe acabar en la linea"
        with M.abrir(self.db) as c:
            tid = captura.registrar(c, "p", "r")
            captura.corregir(c, tid, secreto)
            e = L.tramo(c, sujeto=f"turno:{tid}")[0]
            self.assertNotIn(secreto, e["datos"])
            self.assertEqual(json.loads(e["datos"])["largo"], len(secreto))


if __name__ == "__main__":
    unittest.main()
