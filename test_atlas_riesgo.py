import json
import unittest

from atlas_riesgo import ESQUEMA_RIESGO, RiesgoRechazado, SELLOS_RIESGO, validar_riesgo


class PruebasAtlasRiesgo(unittest.TestCase):
    def paquete(self, **cambios):
        valor = {
            "threat": "forged state field",
            "vector": "extra JSON property",
            "fence": "closed shape validation",
            "evidence": "fixture sha256 recorded",
            "status": "SIMULATED",
        }
        valor.update(cambios)
        return json.dumps(valor, separators=(",", ":")).encode("utf-8")

    def test_acepta_paquete_canonico(self):
        crudo = self.paquete()
        self.assertEqual(validar_riesgo(crudo)["status"], "SIMULATED")
        self.assertLess(len(crudo), 1024)

    def test_rechaza_paquete_al_limite_sin_recortar(self):
        with self.assertRaisesRegex(RiesgoRechazado, "rechazo íntegro"):
            validar_riesgo(b" " * 1024)
        crudo = self.paquete(threat="x" * 1100)
        with self.assertRaisesRegex(RiesgoRechazado, "rechazo íntegro"):
            validar_riesgo(crudo)

    def test_rechaza_campo_extra(self):
        valor = json.loads(self.paquete())
        valor["extra"] = "reject"
        with self.assertRaisesRegex(RiesgoRechazado, "forma"):
            validar_riesgo(json.dumps(valor).encode("utf-8"))

    def test_rechaza_enteros_y_booleanos(self):
        for valor in (0, 1, True):
            with self.subTest(valor=valor):
                with self.assertRaisesRegex(RiesgoRechazado, "debe ser texto"):
                    validar_riesgo(self.paquete(threat=valor))

    def test_rechaza_sello_desconocido(self):
        with self.assertRaisesRegex(RiesgoRechazado, "desconocido"):
            validar_riesgo(self.paquete(status="UNKNOWN"))

    def test_rechaza_claves_duplicadas(self):
        crudo = self.paquete().replace(b'"status":"SIMULATED"', b'"status":"LIVE","status":"SIMULATED"')
        with self.assertRaisesRegex(RiesgoRechazado, "duplicada"):
            validar_riesgo(crudo)

    def test_esquema_y_sellos_son_cerrados(self):
        self.assertEqual(ESQUEMA_RIESGO, "atlas.riesgo/1")
        self.assertEqual(SELLOS_RIESGO, {"LIVE", "STALE", "STATIC", "SIMULATED", "NO_DATA", "ERROR"})


if __name__ == "__main__":
    unittest.main()
