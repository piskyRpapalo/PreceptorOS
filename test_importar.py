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
import re
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

    def test_un_paquete_viejo_sin_tarea_entra_NO_DATA_y_no_libre(self):
        """`libre` es una afirmacion --«no vino por un atajo»--, no un hueco.

        Desde este lado solo se ve el paquete, asi que si no trae la tarea no
        hay forma de saber si hubo atajo. Ponerle `libre` seria comodo y falso,
        y envenenaria justo la consulta para la que se creo la columna.
        """
        with M.abrir(self.db) as c:
            I.importar(c, paquete(firmada(par())))
            self.assertEqual(self.filas(c)[0]["tarea"], "NO_DATA")

    def test_la_tarea_que_manda_la_web_se_conserva(self):
        with M.abrir(self.db) as c:
            I.importar(c, paquete(firmada(par(tarea="dataset"))))
            self.assertEqual(self.filas(c)[0]["tarea"], "dataset")

    def test_una_tarea_que_no_esta_en_el_vocabulario_cae_a_NO_DATA(self):
        """El navegador no puede meter una tarea nueva por la puerta de atras.

        Aceptarla dejaria entrar `Dataset`, `dataset ` y `DATASET` como tres
        tareas distintas, y entonces el `group by` vuelve a no significar nada.
        """
        with M.abrir(self.db) as c:
            I.importar(c, paquete(firmada(par(tarea="lo que sea"))))
            self.assertEqual(self.filas(c)[0]["tarea"], "NO_DATA")

    def test_los_ocho_atajos_de_la_web_son_los_de_captura(self):
        """El paralelo que hace comparables los dos arneses.

        Si las dos listas se separan, un turno de la web y otro de la app dejan
        de poder compararse -- y nadie lo notaria, porque cada lado seguiria
        siendo coherente consigo mismo.
        """
        import json
        f = os.path.normpath(os.path.join(WEB, "..", "servicios.json"))
        if not os.path.isfile(f):
            self.skipTest("el repo de la web no esta a mano")
        d = json.loads(open(f, encoding="utf-8").read())
        web = {s["comando"].lstrip("/") for s in d["servicios"]}
        self.assertEqual(web, set(captura.TAREAS) - {"libre"})

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

    # --- las dos clases de par (2026-09-13) ---------------------------------

    def test_una_reescritura_no_acaba_en_la_columna_de_entrenamiento(self):
        """El prompt bueno de una reescritura JAMAS sale por `elegido`.

        Es la prueba que sujeta la unica linea que de verdad importa de todo
        esto: en una reescritura `correccion` es un PROMPT mejor, y meterlo
        donde va una respuesta entrena al modelo a contestar una pregunta con
        otra pregunta. Se comprueban los DOS cerrojos, porque tener dos y
        probar uno es tener uno.
        """
        bueno = "/instalar que pasos sigo para el nodo"
        p = par(prompt="como configuro esto", respuesta="no me sirvio",
                correccion=bueno, consent=1,
                tipo="reescritura", autoridad=1, turnos_antes=3)
        with M.abrir(self.db) as c:
            inf = I.importar(c, I.leer(json.dumps(paquete(firmada(p)))))
            self.assertEqual(inf["nuevas"], 1, "la reescritura tiene que ENTRAR: "
                                               "se guarda, lo que no se hace es "
                                               "entrenar con ella")
            fila = self.filas(c)[0]
            self.assertEqual(fila["tipo"], "reescritura")
            # Cerrojo 1: la columna de la que sale `elegido` se queda vacia.
            self.assertIsNone(fila["correccion"])
            # Y el texto bueno no se pierde: vive donde no entrena.
            senal = json.loads(fila["senal"])
            self.assertEqual(senal["reescrito_a"], bueno)
            self.assertEqual(senal["autoridad"], 1)
            self.assertEqual(senal["turnos_antes"], 3)
            # Las dos cosas malas se guardan juntas a proposito: son el caso.
            self.assertEqual(fila["prompt"], "como configuro esto")
            self.assertEqual(fila["respuesta"], "no me sirvio")

            # Cerrojo 2: el constructor del dataset no la ve.
            salida = captura.pares(c)
            self.assertEqual(salida, [], "una reescritura no es material de "
                                         "entrenamiento")
            self.assertNotIn(bueno, json.dumps(salida, ensure_ascii=False))

    def test_una_correccion_normal_sigue_entrando_al_dataset(self):
        """El reverso, y hace falta: un filtro que lo deja todo fuera «pasa»
        esta prueba a medias. Lo de siempre tiene que seguir funcionando."""
        p = par(consent=1, tipo="correccion", autoridad=1)
        with M.abrir(self.db) as c:
            I.importar(c, I.leer(json.dumps(paquete(firmada(p)))))
            fila = self.filas(c)[0]
            self.assertEqual(fila["tipo"], "correccion")
            self.assertEqual(fila["correccion"], "bien")
            salida = captura.pares(c)
            self.assertEqual(len(salida), 1)
            self.assertEqual(salida[0]["clase"], "preferencia")
            self.assertEqual(salida[0]["elegido"], "bien")

    def test_un_paquete_sin_tipo_es_una_correccion(self):
        """Lo unico que podian ser los paquetes anteriores al 2026-09-13.

        No es optimismo: la otra clase no existia. Y el defecto importa, porque
        el filtro de `pares()` es POSITIVO -- un NO_DATA aqui habria dejado
        fuera del dataset a todo lo importado antes de hoy, callando.
        """
        p = par(consent=1)
        self.assertNotIn("tipo", p)
        with M.abrir(self.db) as c:
            I.importar(c, I.leer(json.dumps(paquete(firmada(p)))))
            self.assertEqual(self.filas(c)[0]["tipo"], "correccion")
            self.assertEqual(len(captura.pares(c)), 1)

    def test_una_clase_desconocida_no_entra_y_se_dice_cual(self):
        """Fallar CERRADO. Degradar a «correccion» lo que no se sabe leer es
        exactamente como una clase nueva acabaria en el dataset sin que nadie
        lo decidiera."""
        p = par(consent=1, tipo="resumen")
        with M.abrir(self.db) as c:
            inf = I.importar(c, I.leer(json.dumps(paquete(firmada(p)))))
            self.assertEqual(inf["nuevas"], 0)
            self.assertEqual(self.filas(c), [])
            self.assertIn("resumen", inf["saltadas"][0]["motivo"])

    def test_los_turnos_viejos_ganan_la_clase_sin_perderse(self):
        """Una memoria de antes de hoy no tiene la columna, y al ganarla sus
        turnos quedan como CORRECCIONES -- no como huecos. Si quedaran en
        NO_DATA, el filtro positivo los borraria del dataset en silencio, que
        es la peor forma de perder datos: sin error y sin aviso."""
        with M.abrir(self.db) as c:
            captura.asegurar(c)
            c.execute("insert into turnos (prompt, respuesta, correccion, "
                      "consent) values ('de antes', 'mala', 'buena', 1)")
            # Se simula la base vieja quitandole la columna recien creada.
            c.execute("alter table turnos drop column tipo")
            self.assertNotIn("tipo", {d[1] for d in
                                      c.execute("pragma table_info(turnos)")})
            I.asegurar(c)
            self.assertEqual(self.filas(c)[0]["tipo"], "correccion")
            self.assertEqual(len(captura.pares(c)), 1,
                             "el turno viejo sigue entrenando")

    # --- el cruce con la web -----------------------------------------------

    def test_los_campos_son_LOS_MISMOS_que_escribe_el_navegador(self):
        """La prueba que solo puede fallar cuando alguien toca el otro repo.

        Se salta si la web no esta a mano --no todo el mundo la tiene clonada--
        pero cuando esta, cruza los dos lados. Un campo que el navegador
        empiece a escribir y aqui no se lea no da error en ningun sitio: se
        pierde, y se pierde callando.
        """
        # DOS FICHEROS, PORQUE DESDE EL 2026-09-13 HAY DOS ESCRITORES.
        # `corregir.js` firma correcciones y `aprender.js` firma reescrituras,
        # por el mismo esquema y hacia esta misma puerta. Vigilar solo el
        # primero dejaba al segundo libre para anadir un campo que aqui se
        # perdiera callando -- que es justo lo que esta prueba existe para
        # impedir, y la razon por la que se escribio.
        for nombre in ("corregir.js", "aprender.js"):
            with self.subTest(fichero=nombre):
                self._campos_de(nombre)

    def _campos_de(self, nombre):
        js = os.path.join(WEB, nombre)
        if not os.path.isfile(js):
            self.skipTest("el repo de la web no esta a mano")
        texto = open(js, encoding="utf-8").read()
        # El objeto que la web firma y guarda.
        cuerpo = texto.split("var reg = {", 1)[1].split("};", 1)[0]
        # SE QUITAN LOS COMENTARIOS ANTES DE PARTIR, y no es limpieza de
        # estilo. Aqui solo se saltaban las lineas que empiezan por `//`; un
        # bloque `/* ... */` dentro del objeto entraba como si fuera un campo, y
        # el gate acusaba a la web de escribir un campo llamado «boton vive
        # tambien en el Benchmark eso ya no identifica nada». Paso el
        # 2026-09-13 y costo un rato entender que el acusado era el parser.
        #
        # Un guardian que se equivoca de culpable es peor que uno ausente:
        # manda a arreglar el sitio que no era.
        cuerpo = re.sub(r"/\*.*?\*/", "", cuerpo, flags=re.S)
        campos = {l.split(":", 1)[0].strip()
                  for l in cuerpo.splitlines() if ":" in l
                  and not l.strip().startswith("//")}
        # `tarea` entro el 2026-09-08, y esta prueba salto con ella un commit
        # despues de escribirse -- que es exactamente su trabajo. Se anade aqui
        # DESPUES de enseñarle al importador a leerla, nunca antes: ampliar la
        # lista para callar el rojo seria convertir el guardian en un tramite.
        #
        # `tipo`, `autoridad` y `turnos_antes` entraron el 2026-09-13 con las
        # reescrituras, y se anaden aqui DESPUES de que `_clase()` los lea y
        # los reparta: `tipo` a su columna, los otros dos a `senal`. El orden
        # de las dos cosas es la prueba misma.
        leidos = {"prompt", "respuesta", "correccion", "corregido", "modelo",
                  "idioma", "motivo", "tarea", "consent", "origen",
                  "tipo", "autoridad", "turnos_antes"}
        sin_leer = campos - leidos
        self.assertFalse(
            sin_leer,
            # EL MENSAJE NOMBRA EL FICHERO QUE SE LEYO, no uno fijo. Decia
            # siempre «corregir.js» y desde que son dos, eso mandaria a abrir
            # el fichero equivocado -- la misma trampa del guardian que se
            # equivoca de culpable que ya mordio una vez mas arriba.
            f"{nombre} escribe {sorted(sin_leer)} y este importador no los "
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



class LaPuerta(unittest.TestCase):
    """`importar()` estaba escrita, probada y llamada por NADIE.

    El unico sitio del arbol que la invocaba era este fichero de pruebas: la app
    sabia leer lo que la web exporta, y una persona no tenia como pedirselo. Una
    funcion sin puerta pasa todas sus pruebas y no sirve a nadie, que es la peor
    forma de estar roto -- no da sintoma.

    Se prueba la puerta, no la funcion: que un fichero que no es un paquete se
    rechaza con su motivo, que el SECO no escribe, y que lo que el seco cuenta
    es lo que el --ejecutar escribe. Ese ultimo punto es el que importa: el seco
    corre el MISMO `importar()` dentro de una transaccion y la deshace, asi que
    no puede divergir del camino de verdad por mucho que pase el tiempo.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db = os.path.join(self.dir, "memory.db")
        with M.abrir(self.db):          # crea el fichero y sus tablas
            pass
        self.json = os.path.join(self.dir, "paquete.json")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def escribir(self, datos):
        with open(self.json, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)

    def cuantos(self):
        with M.abrir(self.db) as c:
            I.asegurar(c)
            return c.execute("select count(*) from turnos").fetchone()[0]

    def test_un_fichero_que_no_esta_no_se_inventa(self):
        self.assertEqual(I.main([os.path.join(self.dir, "no-existe.json"),
                                 "--db", self.db]), 2)

    def test_lo_que_no_es_un_paquete_se_dice(self):
        self.escribir({"esquema": "otra-cosa", "pares": []})
        self.assertEqual(I.main([self.json, "--db", self.db]), 2)

    def test_el_seco_no_escribe_y_el_ejecutar_si(self):
        self.escribir(paquete(firmada(par())))
        antes = self.cuantos()
        self.assertEqual(I.main([self.json, "--db", self.db]), 0)
        self.assertEqual(self.cuantos(), antes,
                         "el seco escribio: deja de ser seco")
        self.assertEqual(I.main([self.json, "--db", self.db, "--ejecutar"]), 0)
        self.assertEqual(self.cuantos(), antes + 1,
                         "el --ejecutar no escribio lo que el seco conto")


if __name__ == "__main__":
    unittest.main()
