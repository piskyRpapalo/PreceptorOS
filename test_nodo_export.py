import hashlib
import json
import unittest
from unittest.mock import patch

import nodo_export


def cedula():
    c = {
        "esquema": "preceptoros.cedula-nodo/1",
        "nodo": "nodo.1.prueba",
        "admin": "a1" * 32,
        "dispositivos": [{"clave": "b2" * 32, "estado": "solicitado"}],
        "firma_ssh": "firma-de-prueba",
        "autenticidad": "NO_DATA · pendiente de verificación local",
    }
    c["sha256"] = hashlib.sha256(json.dumps(c, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return c


class ExportacionNodo(unittest.TestCase):
    def test_forma_invalida_se_rechaza_sin_red(self):
        llamada = []
        r = nodo_export.enviar({"cedula": {"esquema": "otro"}}, transport=lambda *a: llamada.append(a))
        self.assertEqual((r["estado"], r["codigo"], r["http"]), ("bloqueado", "cedula_rechazada", 422))
        self.assertEqual(llamada, [])

    def test_firma_ausente_no_abre_la_red(self):
        llamada = []
        with patch("nodo_export.nodo_app.autenticidad", return_value=("NO_DATA", "firma no disponible")):
            r = nodo_export.enviar({"cedula": cedula()}, transport=lambda *a: llamada.append(a))
        self.assertEqual(r["codigo"], "firma_no_disponible")
        self.assertEqual(r["http"], 503)
        self.assertEqual(llamada, [])

    def test_envio_solo_con_firma_validada_y_paquete_sin_firma_de_silicio(self):
        recibida = []
        paquete = {"esquema": "preceptoros/cedula-nodo/1", "pares": [cedula()], "firma": None}
        def transport(url, body):
            recibida.append((url, json.loads(body)))
            return {"estado": "encolado", "recibidos": 1, "paquete": paquete}
        with patch("nodo_export.nodo_app.autenticidad", return_value=("OK", "verificada")):
            r = nodo_export.enviar({"cedula": cedula()}, transport=transport)
        self.assertEqual(r, {"estado": "encolado", "codigo": "recibido", "recibidos": 1})
        self.assertEqual(recibida[0][0], nodo_export.ENDPOINT)
        self.assertEqual(recibida[0][1], {"cedula": cedula()})

    def test_silicio_no_puede_devolver_paquete_firmado(self):
        with patch("nodo_export.nodo_app.autenticidad", return_value=("OK", "verificada")):
            r = nodo_export.enviar({"cedula": cedula()}, transport=lambda *_: {
                "recibidos": 1, "paquete": {"esquema": "preceptoros/cedula-nodo/1", "pares": [cedula()], "firma": "inventada"}})
        self.assertEqual(r["codigo"], "paquete_invalido")


if __name__ == "__main__":
    unittest.main()
