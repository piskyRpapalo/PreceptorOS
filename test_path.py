#!/usr/bin/env python3
"""D2 · los paths de aprendizaje. Solo biblioteca estandar."""
from __future__ import annotations

import ast
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import path as P  # noqa: E402


def escribir(carpeta, nombre, datos):
    ruta = Path(carpeta) / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    return ruta


PATH_MINIMO = {
    "id": "uno-de-prueba",
    "titulo": "Un path de prueba",
    "idioma": "es",
    "pasos": [{"id": "primero", "titulo": "El primer paso"}],
}


class TestCatalogo(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_los_de_fabrica_se_listan(self):
        """Los dos que vienen con el producto tienen que salir."""
        ids = {p["id"] for p in P.listar(base=self.base)}
        self.assertIn("terminal-sin-miedo", ids)
        self.assertIn("python-primeros-pasos", ids)
        for p in P.listar(base=self.base):
            self.assertGreater(p["pasos"], 0, f"{p['id']} no tiene pasos")

    def test_los_de_fabrica_son_validos(self):
        """Si el producto envia un path roto, que lo cace la suite y no la persona."""
        cat = P.catalogo(base=self.base)
        de_fabrica = [r for r in cat["rotos"] if r["fuente"] == "producto"]
        self.assertEqual(de_fabrica, [], f"paths de fabrica rotos: {de_fabrica}")

    def test_el_de_la_persona_pisa_al_del_producto(self):
        """Si se molesto en escribir uno con el mismo id, quiere el suyo."""
        suyo = dict(PATH_MINIMO, id="terminal-sin-miedo", titulo="El mio")
        escribir(P.carpeta_persona(self.base), "terminal-sin-miedo.json", suyo)
        leido = P.leer("terminal-sin-miedo", base=self.base)
        self.assertEqual(leido["titulo"], "El mio")
        self.assertEqual(leido["fuente_carpeta"], "tuyo")

    def test_un_path_roto_se_nombra_y_no_desaparece(self):
        """Un catalogo que esconde lo roto ensena menos de lo que hay."""
        carpeta = P.carpeta_persona(self.base)
        carpeta.mkdir(parents=True, exist_ok=True)
        with open(carpeta / "roto.json", "w", encoding="utf-8") as f:
            f.write("{esto no es json,,,")
        cat = P.catalogo(base=self.base)
        self.assertEqual(len(cat["rotos"]), 1, "el roto no se reporto")
        self.assertIn("roto.json", cat["rotos"][0]["motivo"])
        self.assertIn("ROTO", P.vista(base=self.base),
                      "la vista no ensena que hay algo roto")

    def test_un_path_roto_no_tumba_a_los_sanos(self):
        carpeta = P.carpeta_persona(self.base)
        carpeta.mkdir(parents=True, exist_ok=True)
        with open(carpeta / "roto.json", "w", encoding="utf-8") as f:
            f.write("[[[")
        escribir(carpeta, "sano.json", PATH_MINIMO)
        ids = {p["id"] for p in P.listar(base=self.base)}
        self.assertIn("uno-de-prueba", ids, "un roto se llevo por delante a un sano")

    def test_filtrar_por_idioma(self):
        escribir(P.carpeta_persona(self.base), "en.json",
                 dict(PATH_MINIMO, id="one-in-english", idioma="en"))
        self.assertEqual([p["id"] for p in P.listar(base=self.base, idioma="en")],
                         ["one-in-english"])


class TestSeguridadDelId(unittest.TestCase):
    """El `id` se usa para encontrar un fichero, y llega desde la interfaz."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_un_id_con_ruta_no_lee_nada(self):
        for veneno in ("../../etc/passwd", "/etc/passwd", "..",
                       "a/b", "a\\b", "con espacio", "", None,
                       "TERMINAL-SIN-MIEDO/../../x"):
            self.assertIsNone(P.leer(veneno, base=self.base),
                              f"`{veneno}` no deberia devolver nada")

    def test_mayusculas_no_son_una_puerta_distinta(self):
        """Un id se normaliza a minusculas; no crea un segundo path fantasma."""
        self.assertIsNotNone(P.leer("TERMINAL-SIN-MIEDO", base=self.base))


class TestValidacion(unittest.TestCase):

    def test_devuelve_todos_los_problemas_de_una_vez(self):
        """Quien escribe un path quiere ver TODO lo que le falta, no de uno en uno."""
        problemas = P.validar({"pasos": [{"titulo": "sin id"}, "ni siquiera un objeto"]})
        self.assertGreaterEqual(len(problemas), 3, problemas)
        junto = " ".join(problemas)
        self.assertIn("`id`", junto)
        self.assertIn("`titulo`", junto)

    def test_un_path_sin_pasos_no_es_un_path(self):
        self.assertTrue(P.validar(dict(PATH_MINIMO, pasos=[])))
        self.assertTrue(P.validar({"id": "x", "titulo": "y"}))

    def test_ids_de_paso_repetidos_se_cazan(self):
        datos = dict(PATH_MINIMO, pasos=[
            {"id": "mismo", "titulo": "uno"},
            {"id": "mismo", "titulo": "dos"}])
        self.assertTrue(any("repetido" in p for p in P.validar(datos)))

    def test_el_minimo_valido_lo_es(self):
        self.assertEqual(P.validar(PATH_MINIMO), [])

    def test_lo_opcional_ausente_queda_NO_DATA(self):
        """Lo que falta se ve. No se disimula con una cadena vacia."""
        tmp = tempfile.TemporaryDirectory()
        try:
            base = Path(tmp.name)
            escribir(P.carpeta_persona(base), "m.json", PATH_MINIMO)
            leido = P.leer("uno-de-prueba", base=base)
            self.assertEqual(leido["fuente"], "NO_DATA")
            for campo in P.CAMPOS_PASO:
                self.assertEqual(leido["pasos"][0][campo], "NO_DATA",
                                 f"`{campo}` deberia declararse ausente")
        finally:
            tmp.cleanup()


class TestCasa(unittest.TestCase):

    def test_asegurar_crea_la_carpeta_y_no_escribe_dentro(self):
        """No se copian los de fabrica a su casa: es una escritura que no pidio."""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            destino = P.asegurar(base)
            self.assertTrue(destino.is_dir())
            self.assertEqual(list(destino.iterdir()), [],
                             "asegurar() escribio algo en la carpeta de la persona")

    def test_sin_carpeta_de_persona_los_de_fabrica_siguen_saliendo(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertGreaterEqual(len(P.listar(base=Path(d))), 2)


class TestSinModeloYSinRed(unittest.TestCase):
    """El criterio de D2: un path se lee sin LLM y sin red.

    Se comprueba sobre el ARBOL DE SINTAXIS y no ejecutando: una prueba que
    solo mira lo que pasa en una ejecucion no ve el `import` que alguien anada
    manana en la rama que hoy no se toma.
    """

    PROHIBIDOS = {
        "socket", "ssl", "urllib", "http", "ftplib", "smtplib", "telnetlib",
        "asyncio", "requests", "subprocess", "conversacion", "afinado",
    }

    def test_path_py_no_importa_ni_red_ni_motor(self):
        fuente = Path(__file__).parent / "path.py"
        arbol = ast.parse(fuente.read_text(encoding="utf-8"))
        importados = set()
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                importados.update(a.name.split(".")[0] for a in nodo.names)
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                importados.add(nodo.module.split(".")[0])
        intrusos = importados & self.PROHIBIDOS
        self.assertEqual(intrusos, set(),
                         f"path.py importa {intrusos}: un path tiene que poder "
                         f"leerse sin modelo y sin red")

    def test_solo_biblioteca_estandar(self):
        """Ni una dependencia fuera de la stdlib, ni siquiera indirecta."""
        fuente = Path(__file__).parent / "path.py"
        arbol = ast.parse(fuente.read_text(encoding="utf-8"))
        propios = {"casa"}
        estandar = set(sys.stdlib_module_names)
        for nodo in ast.walk(arbol):
            nombres = []
            if isinstance(nodo, ast.Import):
                nombres = [a.name.split(".")[0] for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                nombres = [nodo.module.split(".")[0]]
            for n in nombres:
                self.assertTrue(n in estandar or n in propios,
                                f"`{n}` no es stdlib ni un modulo de este arbol")


class TestEnchufadoEnElArranque(unittest.TestCase):
    """La carpeta nace con la casa, y nace VACIA."""

    def test_arranque_llama_a_asegurar(self):
        import aurelius
        fuente = Path(aurelius.__file__).read_text(encoding="utf-8")
        self.assertIn("_path.asegurar()", fuente,
                      "arranque() no crea la carpeta de paths")

    def test_un_fallo_creando_la_carpeta_no_tumba_el_arranque(self):
        """Perder los paths propios no vale una sesion entera: los de fabrica
        se leen igual desde el directorio del programa."""
        import aurelius
        fuente = Path(aurelius.__file__).read_text(encoding="utf-8")
        trozo = fuente.split("_path.asegurar()")[1][:600]
        self.assertIn("except OSError", trozo,
                      "un OSError al crear la carpeta tumbaria el arranque")


if __name__ == "__main__":
    unittest.main(verbosity=2)
