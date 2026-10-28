"""Cerrojo de alta cerrada para rutas y nombres visibles del App."""
import unittest
import sys

import bin.auditar_nombres_publicos as auditor


class TestInventarioPublico(unittest.TestCase):
    def test_el_catalogo_cubre_la_superficie_actual(self):
        import json
        esperado = json.loads(auditor.CATALOGO.read_text(encoding="utf-8"))
        self.assertTrue(auditor.coincide(esperado, auditor.observado()))

    def test_sabotaje_de_nombre_nuevo_se_detecta(self):
        import json
        esperado = json.loads(auditor.CATALOGO.read_text(encoding="utf-8"))
        nombres = {ruta: list(filas) for ruta, filas in esperado["names_by_source"].items()}
        nombres.setdefault("interface/app.html", []).append("Unreviewed label")
        saboteado = dict(esperado, names_by_source=nombres)
        self.assertFalse(auditor.coincide(esperado, saboteado))

    def test_sabotaje_de_ruta_nueva_se_detecta(self):
        import json
        esperado = json.loads(auditor.CATALOGO.read_text(encoding="utf-8"))
        routes = dict(esperado["routes"])
        routes["/new"] = "new.html"
        saboteado = dict(esperado, routes=routes)
        self.assertFalse(auditor.coincide(esperado, saboteado))


if __name__ == "__main__":
    if "--sabotaje" in sys.argv:
        import json
        original = json.loads(auditor.CATALOGO.read_text(encoding="utf-8"))
        names = {path: list(rows) for path, rows in original["names_by_source"].items()}
        names.setdefault("interface/app.html", []).append("Injected label")
        altered_name = dict(original, names_by_source=names)
        routes = dict(original["routes"])
        routes["/injected"] = "injected.html"
        altered_route = dict(original, routes=routes)
        detected = sum(not auditor.coincide(original, sample) for sample in (altered_name, altered_route))
        print(f"RESULTADO SABOTAJE: {detected}/2 detectadas")
        raise SystemExit(0 if detected == 2 else 1)
    unittest.main()
