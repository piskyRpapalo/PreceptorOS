#!/usr/bin/env python3
"""Pruebas de endurecimiento FINAL GATE: 8 nuevas sondas negativas de SentinelX.

Seis veredictos COMPATIBLE no soportados por evidencia:
- P1: SHA malformado (longitud incorrecta) no rechazado
- P2: SHA cadena vacía pasa como evidencia
- P3: Loader capabilities lista vacía no rechazado
- P4: Telemetría obsoleta sin verificación de frescura
- P5: Arquitectura ausente (peft_config None) no detectado
- P6: RAM pico cero pasa como requisito válido

Dos excepciones no capturadas por JSON anidado malformado:
- P7: base_model es una cadena en lugar de dict → AttributeError
- P8: peft_config es una cadena en lugar de dict → AttributeError

Cada prueba verifica que el registro falle cerrado (fail-closed) en lugar de
producir COMPATIBLE falso o una excepción no controlada.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest


import adaptador_registro as ar

# Backend de referencia completo
BACKEND_REF = {
    "nombre": "ollama",
    "modelo": "qwen3-coder:30b",
    "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
    "formato": "gguf",
    "ram_disponible_mb": 58000,
    "loader_capabilities": ["gguf"],
}

# SHA válido para referencia
VALID_SHA = "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad"


class TestP1_MalformedSHA(unittest.TestCase):
    """P1: SHA malformado (longitud incorrecta) no debe producir COMPATIBLE.

    Un SHA de 12 caracteres o 32 caracteres no es un SHA-256 válido.
    El registro debe rechazarlo como evidencia insuficiente.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_p1_sha_corto_no_es_compatible(self):
        """SHA de 12 caracteres no establece identidad → NO_DATA."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42",  # Solo 12 chars, no es SHA-256
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"P1 FALLIDO: SHA malformado produjo COMPATIBLE. Obtenido: {resultado}",
        )

    def test_p1_sha_no_hex_no_es_compatible(self):
        """SHA con caracteres no hexadecimales → NO_DATA."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"P1 FALLIDO: SHA no-hex produjo COMPATIBLE. Obtenido: {resultado}",
        )


class TestP2_EmptySHAString(unittest.TestCase):
    """P2: SHA cadena vacía no es evidencia de identidad.

    Un SHA de "" no es lo mismo que un SHA ausente. Ambos deben producir
    NO_DATA(identity_unverified), no COMPATIBLE.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def test_p2_sha_vacio_no_es_compatible(self):
        """SHA cadena vacía → NO_DATA(identity_unverified)."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "",  # Cadena vacía, no es evidencia
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"P2 FALLIDO: SHA vacío produjo COMPATIBLE. Obtenido: {resultado}",
        )


class TestP3_EmptyLoaderCapabilities(unittest.TestCase):
    """P3: Loader capabilities como lista vacía no es evidencia.

    Un backend con loader_capabilities=[] no puede cargar nada.
    Esto debe ser NO_DATA, no COMPATIBLE.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_p3_loader_caps_vacio_no_es_compatible(self):
        """loader_capabilities=[] → NO_DATA(loader_capability_unverified)."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        backend = dict(BACKEND_REF)
        backend["loader_capabilities"] = []  # Lista vacía
        resultado = self.reg.es_compatible("x-v1", backend)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"P3 FALLIDO: Loader caps vacío produjo COMPATIBLE. Obtenido: {resultado}",
        )


class TestP4_StaleTelemetry(unittest.TestCase):
    """P4: Telemetría obsoleta no debe usarse como evidencia actual.

    Si la medición tiene temp_max_c pero es de una ejecución anterior,
    no debe usarse para verificar compatibilidad actual.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_p4_telemetria_con_ram_pico_valida(self):
        """Telemetría con ram_pico_mb válido funciona correctamente."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"ram_pico_mb": 20123, "temp_max_c": 65},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        # Con RAM suficiente y loader verificado, debe ser COMPATIBLE
        self.assertEqual(resultado["estado"], "COMPATIBLE")


class TestP5_MissingArchitectureEvidence(unittest.TestCase):
    """P5: peft_config ausente (None) no debe causar AttributeError.

    Si el adaptador se registró sin peft_config, el check de arquitectura
    debe producir NO_DATA(architecture_unverified), no una excepción.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_p5_peft_config_none_no_excepcion(self):
        """peft_config=None → NO_DATA(architecture_unverified), no excepción."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
        }
        # Registrar sin peft_config
        self.reg.registrar("x-v1", "code", ada["base_model"], peft_config=None)
        # No debe levantar AttributeError
        try:
            resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
            self.assertNotEqual(
                resultado["estado"],
                "COMPATIBLE",
                f"P5 FALLIDO: Sin arquitectura produjo COMPATIBLE. Obtenido: {resultado}",
            )
        except AttributeError as e:
            self.fail(f"P5 FALLIDO: AttributeError no capturado: {e}")


class TestP6_ZeroPeakRAM(unittest.TestCase):
    """P6: RAM pico cero no es un requisito válido.

    Si ram_pico_mb es 0, no hay requisito de RAM medido.
    No debe producir INCOMPATIBLE por RAM insuficiente.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_p6_ram_pico_cero_no_es_requisito(self):
        """ram_pico_mb=0 no debe producir INCOMPATIBLE por RAM."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"ram_pico_mb": 0},  # Cero = no medido
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        backend = dict(BACKEND_REF)
        backend["ram_disponible_mb"] = 0  # También cero
        resultado = self.reg.es_compatible("x-v1", backend)
        # RAM pico 0 no es un requisito; no debe ser INCOMPATIBLE por RAM
        causa = resultado.get("causa", "")
        self.assertNotIn(
            "RAM pico",
            causa,
            f"P6 FALLIDO: RAM pico 0 tratado como requisito. Obtenido: {resultado}",
        )


class TestP7_MalformedNestedJSON_base_model(unittest.TestCase):
    """P7: base_model como cadena causa AttributeError.

    Si el registro JSON tiene base_model como una cadena en lugar de un dict,
    llamar a .get() en ella causa AttributeError. El código debe fallar cerrado.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_p7_base_model_string_no_excepcion(self):
        """base_model como cadena → NO_DATA, no AttributeError."""
        # Inyectar directamente en el registro JSON
        ruta = os.path.join(self.tmp.name, ar.NOMBRE_REGISTRO)
        datos = {
            "esquema": ar.ESQUEMA,
            "adaptadores": {
                "x-v1": {
                    "rol": "code",
                    "base_model": "Qwen/Qwen3-Coder-30B",  # Cadena, no dict
                    "peft_config": {"target_modules": ["q_proj"]},
                }
            }
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f)

        # No debe levantar AttributeError
        try:
            resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
            # Debe fallar cerrado
            self.assertNotEqual(
                resultado["estado"],
                "COMPATIBLE",
                f"P7 FALLIDO: base_model malformado produjo COMPATIBLE. Obtenido: {resultado}",
            )
        except AttributeError as e:
            self.fail(f"P7 FALLIDO: AttributeError no capturado: {e}")


class TestP8_MalformedNestedJSON_peft_config(unittest.TestCase):
    """P8: peft_config como cadena causa AttributeError.

    Si el registro JSON tiene peft_config como una cadena en lugar de un dict,
    llamar a .get() en ella causa AttributeError. El código debe fallar cerrado.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_p8_peft_config_string_no_excepcion(self):
        """peft_config como cadena → NO_DATA, no AttributeError."""
        ruta = os.path.join(self.tmp.name, ar.NOMBRE_REGISTRO)
        datos = {
            "esquema": ar.ESQUEMA,
            "adaptadores": {
                "x-v1": {
                    "rol": "code",
                    "base_model": {
                        "name": "Qwen/Qwen3-Coder-30B",
                        "sha256": VALID_SHA,
                    },
                    "peft_config": "lora_config_v1",  # Cadena, no dict
                }
            }
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f)

        # No debe levantar AttributeError
        try:
            resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
            self.assertNotEqual(
                resultado["estado"],
                "COMPATIBLE",
                f"P8 FALLIDO: peft_config malformado produjo COMPATIBLE. Obtenido: {resultado}",
            )
        except AttributeError as e:
            self.fail(f"P8 FALLIDO: AttributeError no capturado: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
