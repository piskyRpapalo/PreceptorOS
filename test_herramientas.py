#!/usr/bin/env python3
"""Las herramientas · lo que la base sabe, puesto delante del modelo.

Escritas ANTES de `herramientas.py`. Deben fallar todas antes de la
implementación.

QUÉ SE PRUEBA AQUÍ, Y POR QUÉ ES ESTO Y NO TOOL-CALLING
-------------------------------------------------------
El motor de esta app es `texto -> texto`: un binario de completación, sin API
de herramientas. Pedirle a un modelo de 3B que emita una sintaxis de llamada
fiable, a 5 tok/s y pagando un turno entero por cada intento, es gastar el
recurso caro en lo que el determinista resuelve gratis. Así que la app busca en
la base ANTES de preguntar y le pone delante lo que viene a cuento. El modelo
no elige qué mirar: lee.

Lo que estas pruebas fijan es el contrato de esa lectura, y sobre todo sus
AUSENCIAS -- que es donde un recuperador miente sin que nadie lo note:

* sin nada que recuperar no se inyecta nada, ni un encabezado vacío;
* lo archivado no reaparece por la puerta de atrás;
* un proyecto pausado no se cuenta como lo que la persona tiene entre manos;
* sin índice de búsqueda el turno sigue vivo, y lo que se pueda dar se da;
* y con la personalización apagada no viaja NADA -- ni harness ni memoria --
  porque ese interruptor existe para poder comparar, y una comparación con la
  mitad del contexto todavía puesta no compara nada.

sistema: MVP · solo biblioteca estándar. Sin red, sin dependencias.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cara                                              # noqa: E402
import conversacion as C                                 # noqa: E402
import herramientas as H                                 # noqa: E402
import memory as M                                       # noqa: E402
import proyectos as PR                                   # noqa: E402


def motor_espia(respuesta="lo que sea"):
    """Guarda el prompt que se le mandó. Es la única forma de ver qué viajó."""
    visto = {}

    def hablar(prompt):
        visto["prompt"] = prompt
        return respuesta

    hablar.visto = visto
    return hablar


class TestRecuperar(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmpdir.name, "memory.db")
        M.crear(self.db)

    def tearDown(self):
        self.tmpdir.cleanup()

    # --- las ausencias, que es donde esto se rompe en silencio -------------

    def test_sin_nada_no_inyecta_nada(self):
        """Una base vacía devuelve cadena vacía, no un encabezado sin contenido.

        Inyectar «Lo que recuerdo de ti: (nada)» le enseña al modelo a hablar de
        su propio vacío, y en el primer turno de alguien que acaba de entrar eso
        es exactamente lo que no hay que hacer.
        """
        with M.abrir(self.db) as c:
            self.assertEqual(H.recuperar(c, "cualquier cosa"), "")

    def test_lo_archivado_no_reaparece(self):
        with M.abrir(self.db) as c:
            fila = M.escribir_engrama(c, what="el pino de la entrada")
            M.archivar(c, fila["id"])
            self.assertNotIn("pino", H.recuperar(c, "pino"))

    def test_el_proyecto_pausado_no_es_lo_que_tiene_entre_manos(self):
        with M.abrir(self.db) as c:
            PR.anadir(c, "cocina nueva", estado="activo")
            PR.anadir(c, "el garaje", estado="pausado")
            bloque = H.recuperar(c, "obras")
            self.assertIn("cocina nueva", bloque)
            self.assertNotIn("garaje", bloque)

    # --- lo que sí tiene que llegar ---------------------------------------

    def test_el_recuerdo_que_casa_aparece(self):
        with M.abrir(self.db) as c:
            M.escribir_engrama(c, what="mi hija se llama Vera")
            self.assertIn("Vera", H.recuperar(c, "cómo se llama mi hija"))

    def test_el_recuerdo_que_no_casa_no_aparece(self):
        """Recuperar de más es tan malo como no recuperar: gasta la ventana."""
        with M.abrir(self.db) as c:
            M.escribir_engrama(c, what="la caldera se revisa en octubre")
            self.assertNotIn("caldera", H.recuperar(c, "recetas de pan"))

    # --- el presupuesto ----------------------------------------------------

    def test_respeta_el_techo_de_caracteres(self):
        """Se manda entero en CADA turno: sin techo, la memoria se come la charla."""
        with M.abrir(self.db) as c:
            for i in range(40):
                M.escribir_engrama(c, what=f"melocoton numero {i} " + "x" * 200)
            bloque = H.recuperar(c, "melocoton", techo=600)
            self.assertLessEqual(len(bloque), 600)

    def test_no_corta_un_recuerdo_por_la_mitad(self):
        """Se dejan fuera recuerdos ENTEROS, nunca se parte uno.

        Media frase suelta se lee como algo que la persona dijo a medias, y no
        hay forma de que el modelo sepa que el corte lo puso el presupuesto.
        Cabe menos: se recorta la lista, no el recuerdo.
        """
        with M.abrir(self.db) as c:
            for i in range(10):
                M.escribir_engrama(c, what=f"pera {i} " + "y" * 150)
            bloque = H.recuperar(c, "pera", techo=400)
            self.assertLessEqual(len(bloque), 400)
            # Todo «pera N» que asome tiene que traer su carga completa detras.
            for i in range(10):
                if f"pera {i}" in bloque:
                    self.assertIn(f"pera {i} " + "y" * 150, bloque,
                                  f"«pera {i}» entro cortada")
            self.assertTrue(any(f"pera {i}" in bloque for i in range(10)),
                            "con 400 de techo cabe al menos uno")

    # --- degradar sin mentir ----------------------------------------------

    def test_sin_indice_de_busqueda_el_turno_sigue_vivo(self):
        """Que falte FTS5 no puede dejar sin contexto a quien sí tiene proyectos.

        `memory.buscar` levanta `BusquedaNoDisponible` a propósito -- cero
        resultados por avería no se puede confundir con cero por no haber. Aquí
        se comprueba que esa excepción no se lleva por delante el turno entero.
        """
        with M.abrir(self.db) as c:
            PR.anadir(c, "el huerto", estado="activo")
            c.execute("drop table if exists engrams_fts")
            bloque = H.recuperar(c, "huerto")
            self.assertIn("huerto", bloque)


class TestLasPerillas(unittest.TestCase):
    """La Profundidad y el Foco. La interfaz no existe todavía; el contrato sí.

    Se prueban HOY porque el punto de inyección es uno solo. El día que lleguen
    los deslizadores, lo que tengan que mover ya estará fijado por prueba en vez
    de decidirse entonces contra un backend que no lo esperaba.
    """

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmpdir.name, "memory.db")
        M.crear(self.db)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _poblar(self, c):
        M.guardar_perfil(c, {"nombre": "Marta", "intereses": "la apicultura"})
        M.escribir_engrama(c, what="las abejas enjambran en mayo")
        PR.anadir(c, "el colmenar", estado="activo")

    def test_sin_perillas_se_comporta_como_el_dia_que_nacio(self):
        """El defecto no cambia. Las perillas se añaden, no reemplazan."""
        with M.abrir(self.db) as c:
            self._poblar(c)
            bloque = H.recuperar(c, "abejas")
            self.assertIn("abejas", bloque)
            self.assertIn("colmenar", bloque)

    def test_profundidad_cero_es_turno_aislado(self):
        with M.abrir(self.db) as c:
            self._poblar(c)
            self.assertEqual(H.recuperar(c, "abejas", profundidad=0), "")

    def test_profundidad_veinticinco_es_solo_perfil(self):
        with M.abrir(self.db) as c:
            self._poblar(c)
            bloque = H.recuperar(c, "abejas", profundidad=25)
            self.assertIn("Marta", bloque)
            self.assertNotIn("enjambran", bloque)
            self.assertNotIn("colmenar", bloque)

    def test_profundidad_setenta_y_cinco_trae_los_proyectos(self):
        with M.abrir(self.db) as c:
            self._poblar(c)
            bloque = H.recuperar(c, "abejas", profundidad=75)
            self.assertIn("Marta", bloque)
            self.assertIn("enjambran", bloque)
            self.assertIn("colmenar", bloque)

    def test_un_valor_intermedio_no_se_cae_al_suelo(self):
        """El deslizador es continuo: un 63 cae en su banda, no en la de 0."""
        with M.abrir(self.db) as c:
            self._poblar(c)
            self.assertNotEqual(H.recuperar(c, "abejas", profundidad=63), "")

    def test_foco_libre_no_inyecta_nada(self):
        with M.abrir(self.db) as c:
            self._poblar(c)
            self.assertEqual(H.recuperar(c, "abejas", foco="libre"), "")

    def test_foco_perfil_no_toca_la_busqueda(self):
        with M.abrir(self.db) as c:
            self._poblar(c)
            bloque = H.recuperar(c, "abejas", foco="perfil")
            self.assertIn("Marta", bloque)
            self.assertNotIn("enjambran", bloque)

    def test_foco_memoria_deja_fuera_los_proyectos(self):
        with M.abrir(self.db) as c:
            self._poblar(c)
            bloque = H.recuperar(c, "abejas", foco="memoria")
            self.assertIn("enjambran", bloque)
            self.assertNotIn("colmenar", bloque)

    def test_foco_proyecto_esta_declarado_y_no_implementado(self):
        """No hay dato que filtrar: `engrams` y `proyectos` no se conocen.

        Se fija la caída a `memoria` a propósito. El día que alguien añada el
        enlace en el esquema, esta prueba se pondrá roja y le dirá que había un
        contrato esperándole -- que es exactamente lo que no pasó con las trece
        suites de la deuda S4.
        """
        with M.abrir(self.db) as c:
            self._poblar(c)
            self.assertEqual(H.recuperar(c, "abejas", foco="proyecto"),
                             H.recuperar(c, "abejas", foco="memoria"))

    def test_un_foco_con_errata_no_deja_a_nadie_sin_contexto(self):
        with M.abrir(self.db) as c:
            self._poblar(c)
            self.assertNotEqual(H.recuperar(c, "abejas", foco="memroia"), "")


class TestElTurnoLasLleva(unittest.TestCase):
    """La integración: lo recuperado tiene que VIAJAR, no solo existir."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmpdir.name, "memory.db")
        M.crear(self.db)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _camino(self, c):
        return cara.progreso_camino(c, self.db)

    def test_lo_recuperado_llega_al_prompt(self):
        motor = motor_espia()
        with M.abrir(self.db) as c:
            M.escribir_engrama(c, what="mi hija se llama Vera")
            C.turno(c, "cómo se llama mi hija", self._camino(c),
                    motor=motor, idioma="es")
        self.assertIn("Vera", motor.visto["prompt"])

    def test_sin_personalizar_no_viaja_ni_la_memoria(self):
        """El interruptor apaga TODO el contexto, no solo el carácter.

        Si la memoria siguiera viajando con la personalización apagada, los dos
        lados de la comparación tendrían contexto y la diferencia que el
        producto quiere hacer notar se quedaría en el tono.
        """
        motor = motor_espia()
        with M.abrir(self.db) as c:
            M.escribir_engrama(c, what="mi hija se llama Vera")
            C.turno(c, "cómo se llama mi hija", self._camino(c),
                    motor=motor, idioma="es", personalizada=False)
        self.assertNotIn("Vera", motor.visto["prompt"])
        self.assertEqual(motor.visto["prompt"].strip(), "cómo se llama mi hija")


if __name__ == "__main__":
    unittest.main()
