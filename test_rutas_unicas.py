#!/usr/bin/env python3
"""test_rutas_unicas.py · cada metodo y cada ruta de la PWA aparecen una sola vez.

Sin red. Solo biblioteca estandar. Lee bin/preceptoros-pwa con ast.
En Python una segunda definicion del mismo metodo gana en silencio, y un
`if ruta == "x"` repetido dentro de do_GET/do_POST nunca se alcanza: ambos
son codigo muerto que no da error en ningun sitio.
"""
from __future__ import annotations

import ast
import collections
import os
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
PWA = os.path.join(AQUI, "bin", "preceptoros-pwa")


def _arbol():
    with open(PWA, encoding="utf-8") as f:
        return ast.parse(f.read(), filename=PWA)


def _duplicados(valores):
    cuenta = collections.Counter(valores)
    return sorted(k for k, n in cuenta.items() if n > 1)


class TestRutasUnicas(unittest.TestCase):

    def test_ninguna_clase_define_un_metodo_dos_veces(self):
        malos = []
        for clase in [n for n in ast.walk(_arbol()) if isinstance(n, ast.ClassDef)]:
            metodos = [n.name for n in clase.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            for nombre in _duplicados(metodos):
                malos.append(f"{clase.name}.{nombre}")
        self.assertEqual(malos, [], "metodo definido dos veces en la misma clase")

    def test_ningun_literal_de_ruta_se_repite_en_do_get_ni_do_post(self):
        malos = []
        for fn in [n for n in ast.walk(_arbol()) if isinstance(n, ast.FunctionDef) and n.name in ("do_GET", "do_POST")]:
            rutas = []
            for nodo in ast.walk(fn):
                if (isinstance(nodo, ast.Compare) and len(nodo.ops) == 1
                        and isinstance(nodo.ops[0], ast.Eq)
                        and isinstance(nodo.left, ast.Name) and nodo.left.id == "ruta"
                        and isinstance(nodo.comparators[0], ast.Constant)
                        and isinstance(nodo.comparators[0].value, str)):
                    rutas.append(nodo.comparators[0].value)
            for r in _duplicados(rutas):
                malos.append(f"{fn.name}: {r}")
        self.assertEqual(malos, [], "literal de ruta repetido en do_GET/do_POST")


if __name__ == "__main__":
    unittest.main()
