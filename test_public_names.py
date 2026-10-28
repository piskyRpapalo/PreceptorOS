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
        saboteado = dict(esperado, names=esperado["names"] + ["Unreviewed label"])
        self.assertFalse(auditor.coincide(esperado, saboteado))

    def test_sabotaje_de_ruta_nueva_se_detecta(self):
        import json
        esperado = json.loads(auditor.CATALOGO.read_text(encoding="utf-8"))
        saboteado = dict(esperado, routes=esperado["routes"] + [{"route": "/new", "source": "new.html", "mime": "text/html"}])
        self.assertFalse(auditor.coincide(esperado, saboteado))


if __name__ == "__main__":
    if "--sabotaje" in sys.argv:
        import json
        original = json.loads(auditor.CATALOGO.read_text(encoding="utf-8"))
        altered_name = dict(original, names=original["names"] + ["Injected label"])
        altered_route = dict(original, routes=original["routes"] + [{"route": "/injected", "source": "injected.html", "mime": "text/html"}])
        detected = sum(not auditor.coincide(original, sample) for sample in (altered_name, altered_route))
        print(f"RESULTADO SABOTAJE: {detected}/2 detectadas")
        raise SystemExit(0 if detected == 2 else 1)
    unittest.main()
