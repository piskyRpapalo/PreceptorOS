"""Pruebas del contrato de superficie, separado del vector binario S_t."""
import copy
import json
import re
import unittest
from pathlib import Path

from estado_app import (ESQUEMA, FUENTE_SEMANTICA, MAX_BYTES, ZONAS,
                        deserializar, serializar, validar)
from herencia_web import verificar as verificar_herencia


def estado_base():
    return {
        "esquema": ESQUEMA,
        "fuente_semantica": dict(FUENTE_SEMANTICA),
        "zona": "mando",
        "transicion": {"origen": "mando", "destino": "mando", "tau": 1_000_000},
        "tick": None,
        "frescura": {"estado": "NO_DATA", "edad_tics": None, "causa": "proof_of_tick_unavailable"},
        "guion": {"titulo": "Mando", "orden": ["titulo", "estado", "contenido"], "edad_tics": None},
        "semantica": {
            "hue": None, "saturacion": None, "luminosidad": None,
            "niebla": True, "borde": "normal", "halo": "normal",
        },
    }


class ContratoSuperficie(unittest.TestCase):
    def test_serializacion_canonica_determinista_y_bajo_1024(self):
        estado = estado_base()
        a = serializar(estado)
        b = serializar(copy.deepcopy(estado))
        self.assertEqual(a, b)
        self.assertLess(len(a), MAX_BYTES)
        self.assertEqual(deserializar(a), estado)
        self.assertTrue(validar(estado))

    def test_solo_acepta_zonas_del_catalogo_y_destino_coincidente(self):
        self.assertEqual(set(ZONAS), {"mando", "conversacion", "gobierno", "cuaderno",
                                     "lab", "harness", "puerta", "modelos", "ajustes"})
        estado = estado_base()
        estado["zona"] = "externa"
        with self.assertRaises(ValueError):
            serializar(estado)

    def test_catalogo_de_app_y_contrato_comparten_las_nueve_zonas(self):
        ruta = Path(__file__).parent / "interface" / "zonas.js"
        fuente = ruta.read_text(encoding="utf-8")
        ids = re.findall(r'\bid: "([a-z]+)"', fuente)
        self.assertEqual(set(ids), set(ZONAS))
        self.assertEqual(len(ids), len(ZONAS))

    def test_fuente_hsl_es_semilla_fijada_por_el_manifiesto_de_herencia(self):
        raiz = Path(__file__).parent
        manifiesto_path = raiz / FUENTE_SEMANTICA["manifiesto"]
        manifiesto = json.loads(manifiesto_path.read_text(encoding="utf-8"))
        descriptor = json.loads((manifiesto_path.parent / "tabla" / "semilla.json").read_text(encoding="utf-8"))
        pin = (raiz / FUENTE_SEMANTICA["pin"]).read_text(encoding="ascii").strip()
        self.assertIn(FUENTE_SEMANTICA["semilla"], manifiesto["semillas"])
        self.assertEqual(descriptor["origen"], "public/game/tabla_semantica.js")
        self.assertEqual(verificar_herencia(manifiesto_path.parent, pin)["estado"], "MEDIDO")
        with self.assertRaises(TypeError):
            FUENTE_SEMANTICA["semilla"] = "gacha"
        estado = estado_base()
        estado["transicion"]["destino"] = "lab"
        with self.assertRaises(ValueError):
            serializar(estado)

    def test_tau_y_tics_rechazan_booleanos_y_flotantes(self):
        for campo, valor in (("tau", True), ("tau", 1.5), ("tick", True), ("tick", -1)):
            estado = estado_base()
            if campo == "tau":
                estado["transicion"][campo] = valor
            else:
                estado[campo] = valor
            with self.subTest(campo=campo, valor=valor), self.assertRaises(ValueError):
                serializar(estado)

    def test_live_stale_y_expired_son_tics_logicos_y_no_se_mezclan(self):
        estado = estado_base()
        estado.update(tick=900, frescura={"estado": "LIVE", "edad_tics": 0, "causa": None})
        estado["guion"]["edad_tics"] = 0
        estado["semantica"].update(hue=120, saturacion=20, luminosidad=60, niebla=False)
        self.assertTrue(validar(estado))
        estado["frescura"] = {"estado": "STALE", "edad_tics": 3, "causa": None}
        estado["guion"]["edad_tics"] = 3
        estado["semantica"]["halo"] = "STALE"
        self.assertTrue(validar(estado))
        estado["frescura"] = {"estado": "STALE", "edad_tics": 99, "causa": "expired"}
        with self.assertRaises(ValueError):
            serializar(estado)
        estado["frescura"] = {"estado": "NO_DATA", "edad_tics": 99, "causa": "expired"}
        estado["guion"]["edad_tics"] = 99
        estado["semantica"].update(hue=None, saturacion=None, luminosidad=None,
                                   niebla=True, halo="normal")
        self.assertTrue(validar(estado))

    def test_semantica_hsl_es_dato_y_estados_tienen_canales_consistentes(self):
        estado = estado_base()
        estado["tick"] = 900
        estado["frescura"] = {"estado": "STALE", "edad_tics": 2, "causa": None}
        estado["guion"]["edad_tics"] = 2
        estado["semantica"].update(hue=361, saturacion=20, luminosidad=60,
                                   niebla=False, halo="STALE")
        with self.assertRaises(ValueError):
            serializar(estado)
        estado["semantica"]["hue"] = 120
        estado["semantica"]["borde"] = "ERROR"
        self.assertTrue(validar(estado))

    def test_rechaza_claves_extra_guion_fuera_de_orden_y_mas_de_1024(self):
        estado = estado_base()
        estado["firma_agente"] = True
        with self.assertRaises(ValueError):
            serializar(estado)
        estado = estado_base()
        estado["guion"]["orden"] = ["contenido", "contenido"]
        with self.assertRaises(ValueError):
            serializar(estado)
        estado = estado_base()
        estado["guion"]["titulo"] = "á" * 1025
        with self.assertRaises(ValueError):
            serializar(estado)

    def test_deserializar_exige_bytes_canonicos_y_rechaza_clave_duplicada(self):
        valido = serializar(estado_base())
        with self.assertRaises(ValueError):
            deserializar(valido + b" ")
        with self.assertRaises(ValueError):
            deserializar(b'{"esquema":"x","esquema":"y"}')


if __name__ == "__main__":
    unittest.main()
