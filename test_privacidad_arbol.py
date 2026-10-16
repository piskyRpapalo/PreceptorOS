"""Guardian opcional: los tokens privados llegan solo desde el entorno del CI."""
import json
import os
from pathlib import Path
import re
import subprocess
import unittest


RAIZ = Path(__file__).resolve().parent
VARIABLE = "PRECEPTOROS_PRIVATE_SCAN_TOKENS"


def tokens_privados():
    bruto = os.environ.get(VARIABLE, "").strip()
    if not bruto:
        return None
    try:
        valor = json.loads(bruto)
    except json.JSONDecodeError as exc:
        raise ValueError("el secreto de privacidad debe ser una lista JSON") from exc
    if (not isinstance(valor, list) or not valor
            or any(not isinstance(x, str) or not x for x in valor)):
        raise ValueError("el secreto de privacidad debe ser una lista de textos")
    return tuple(dict.fromkeys(valor))


def archivos_arbol():
    listado = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=RAIZ,
    )
    for nombre in listado.decode("utf-8").split("\0"):
        if nombre:
            ruta = RAIZ / nombre
            if ruta.is_file():
                yield ruta


def resumen_coincidencias(tokens):
    conteo = 0
    rutas = set()
    for ruta in archivos_arbol():
        relativo = ruta.relative_to(RAIZ).as_posix()
        datos = relativo.casefold().encode("utf-8")
        try:
            contenido = ruta.read_bytes()
        except OSError:
            continue
        datos += b"\n" + contenido.lower()
        halladas = sum(datos.count(t.casefold().encode("utf-8")) for t in tokens)
        if halladas:
            conteo += halladas
            seguro = relativo
            for i, token in enumerate(tokens, 1):
                seguro = re.sub(re.escape(token), f"<PRIVADO_{i}>", seguro, flags=re.IGNORECASE)
            rutas.add(seguro)
    return conteo, sorted(rutas)


class TestGuardianPrivacidad(unittest.TestCase):
    def test_arbol_no_contiene_tokens_privados(self):
        try:
            tokens = tokens_privados()
        except ValueError as exc:
            self.fail(str(exc))
        if tokens is None:
            self.skipTest("NO_DATA · secreto de privacidad no montado")
        cantidad, rutas = resumen_coincidencias(tokens)
        self.assertEqual(cantidad, 0,
                         f"{cantidad} coincidencias en {len(rutas)} rutas")

    def test_cache_renovado_y_recurso_alineado(self):
        worker = (RAIZ / "interface" / "sw.js").read_text(encoding="utf-8")
        html = (RAIZ / "interface" / "app.html").read_text(encoding="utf-8")
        cache = re.search(r'const Cache = "preceptoros-armazon-v(\d+)"', worker)
        self.assertIsNotNone(cache, "nombre de caché canónico ausente")
        self.assertGreaterEqual(int(cache.group(1)), 101,
                                "la versión de caché no subió")
        precache = re.search(r'"(/app\.js\?v=(\d+))"', worker)
        pedido = re.search(r'<script src="(/app\.js\?v=(\d+))"></script>', html)
        self.assertIsNotNone(precache, "recurso de app ausente del precache")
        self.assertIsNotNone(pedido, "recurso de app ausente de app.html")
        self.assertEqual(precache.group(1), pedido.group(1),
                         "precache y app.html piden claves distintas")


if __name__ == "__main__":
    unittest.main(verbosity=2)
