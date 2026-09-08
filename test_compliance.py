#!/usr/bin/env python3
"""El documento de cumplimiento, atado al codigo que dice describir.

POR QUE ESTA SUITE EXISTE
-------------------------
`docs/COMPLIANCE.md` mapea cada control normativo --AI Act, ISO 27001, ISO
42001-- contra la funcion de Python que lo implementa. Es material que va a
manos de un auditor externo.

Un documento asi tiene un modo de fallo peor que estar incompleto: **estar
desactualizado sin que nadie lo note**. El dia que alguien renombre
`cruzar_frontera` o borre `redactar_salida`, el documento sigue diciendo que
existen. Eso deja de ser documentacion vieja y pasa a ser una afirmacion falsa
sobre un sistema, hecha por escrito, ante quien vino a comprobarla.

Asi que aqui no se comprueba la prosa --eso lo lee una persona-- sino lo unico
que una maquina puede comprobar y que ademas es donde falla: que cada
`fichero.py::funcion` que el documento cita EXISTE.

Y EL REVERSO, que es la mitad que se olvida: que las piezas de control que si
existen esten CITADAS. Un documento que se queda corto no miente, pero deja al
auditor creyendo que un control no esta cuando si esta -- y eso se paga igual.
"""
from __future__ import annotations

import ast
import os
import re
import sys
import unittest

RAIZ = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(RAIZ, "docs", "COMPLIANCE.md")

# `fichero.py::funcion`, que es como el documento cita. Se exige esa forma y no
# se acepta el nombre suelto a proposito: «redactar_salida» sin su fichero
# obliga a buscarlo, y lo que no se puede localizar en un segundo no se
# comprueba en una auditoria.
# Se excluye la plantilla `<fichero>.py::<funcion>`, que el propio documento
# usa para explicar su formato: el patron la leia como una cita y exigia un
# fichero llamado «fichero.py». Un guardian que se dispara con la explicacion
# de su propia regla obliga a torcer la prosa para callarlo, y ahi es donde
# empieza a escribirse peor para que el gate no moleste.
CITA = re.compile(r"`(?!<)([a-z_]+\.py)::([a-zA-Z_][\w]*)`")

# Los ficheros cuyo contenido ES el control. Si uno gana una funcion publica
# nueva y el documento no la nombra, no falla nada -- pero si PIERDE una que el
# documento cita, si. La lista se declara para que el reverso pueda mirarla.
PIEZAS = ("guardrails.py", "output_guard.py", "soberania.py", "captura.py",
          "importar.py", "medidas.py", "cifras.py", "soberano.py",
          "huella.py", "traza.py")


def definidas(fichero):
    """Los nombres de nivel superior de un modulo, sin importarlo.

    Se lee con `ast` y no con `import` por dos razones que importan aqui: un
    import ejecuta el modulo --y algunos de estos hablan con el disco o con
    `ollama`-- y ademas ataria esta prueba a que el arbol entero importe. Un
    guardian que necesita que todo funcione para poder decir que algo falta es
    un guardian que se calla justo cuando hace falta.
    """
    ruta = os.path.join(RAIZ, fichero)
    if not os.path.isfile(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        arbol = ast.parse(f.read(), filename=fichero)
    nombres = set()
    for n in arbol.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nombres.add(n.name)
        elif isinstance(n, ast.Assign):
            for d in n.targets:
                if isinstance(d, ast.Name):
                    nombres.add(d.id)
    return nombres


class TestCompliance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(DOC, encoding="utf-8") as f:
            cls.texto = f.read()
        cls.citas = CITA.findall(cls.texto)

    def test_el_documento_existe_y_cita_codigo(self):
        """Si no cita nada, esta suite pasaria por vacia y no diria nada."""
        self.assertTrue(self.citas,
                        "COMPLIANCE.md no cita ni una funcion: o esta vacio o "
                        "cambio de formato, y en los dos casos este guardian "
                        "dejo de vigilar sin avisar")
        self.assertGreater(len(self.citas), 15,
                           "quedan menos de dieciseis citas: el documento se "
                           "quedo corto o alguien lo vacio")

    def test_cada_funcion_citada_existe_de_verdad(self):
        """El modo de fallo real: alguien renombra y el documento miente."""
        for fichero, funcion in self.citas:
            with self.subTest(cita=f"{fichero}::{funcion}"):
                nombres = definidas(fichero)
                self.assertIsNotNone(
                    nombres,
                    f"COMPLIANCE.md cita «{fichero}» y ese fichero no existe")
                self.assertIn(
                    funcion, nombres,
                    f"COMPLIANCE.md dice que «{funcion}» vive en {fichero} y "
                    "ahi no esta. Un auditor iria a mirar")

    def test_las_piezas_de_control_estan_citadas(self):
        """El reverso: un documento corto deja creer que falta un control.

        No se exige que se cite TODA funcion de cada pieza --la mayoria son
        detalle interno-- sino que ninguna pieza de control se quede sin
        aparecer. Un fichero entero ausente es un control que el auditor no
        sabra que tiene.
        """
        citados = {f for f, _ in self.citas}
        # `frontera.py` se nombra sin `::` porque lo que cumple es el modulo
        # entero --la celda--, no una funcion suya. Se comprueba aparte.
        for pieza in PIEZAS:
            with self.subTest(pieza=pieza):
                self.assertIn(pieza, citados,
                              f"{pieza} implementa control y COMPLIANCE.md no "
                              "lo cita: el auditor creera que no esta")
        self.assertIn("frontera.py", self.texto,
                      "la celda de aislamiento no aparece en el documento")

    def test_los_huecos_se_declaran_y_pesan_lo_mismo(self):
        """Un mapa de cumplimiento que solo ensena lo verde es material de venta.

        Se exige la seccion, y que nombre los huecos que hoy sabemos ciertos.
        Si alguien cierra uno, esta prueba se pone roja y le obliga a decirlo
        aqui -- que es exactamente cuando hay que decirlo.
        """
        self.assertIn("## 6 · Los huecos", self.texto,
                      "desaparecio la seccion de huecos")
        for hueco in ("Ed25519", "append-only", "no repudio"):
            with self.subTest(hueco=hueco):
                self.assertIn(hueco, self.texto,
                              f"el documento ya no declara el hueco «{hueco}». "
                              "Si se cerro, se dice; si no, se mantiene")

    def test_no_promete_conformidad(self):
        """La linea que separa un mapa honesto de una declaracion falsa.

        Este documento dice DONDE esta cada control. No dice que el sistema
        cumpla el AI Act -- eso lo dictamina un organismo, no un fichero de
        texto, y afirmarlo por escrito seria el mismo defecto que denuncia.
        """
        self.assertIn("No es un certificado", self.texto)
        bajo = self.texto.lower()
        for frase in ("cumple el ai act", "conforme al ai act",
                      "certificado de conformidad", "garantizamos el cumplimiento"):
            with self.subTest(frase=frase):
                # La unica aparicion permitida es la que NIEGA la promesa.
                if frase in bajo:
                    contexto = bajo[max(0, bajo.index(frase) - 60):
                                    bajo.index(frase) + len(frase)]
                    self.assertTrue(
                        any(n in contexto for n in ("no ", "ni ", "nunca")),
                        f"el documento promete conformidad: «{frase}»")


if __name__ == "__main__":
    unittest.main()
