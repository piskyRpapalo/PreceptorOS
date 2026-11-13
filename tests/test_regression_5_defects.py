#!/usr/bin/env python3
"""Regression tests for the 5 SentinelX defects (MULTI-LORA-01).

Each test reproduces one demonstrated defect and verifies the expected verdict.

Defects:
1. Matching malformed SHA strings produce COMPATIBLE.
2. Invented loader_capabilities produce COMPATIBLE.
3. Stale telemetry can be treated as current eligibility evidence.
4. Negative RAM measurements produce COMPATIBLE.
5. target_modules=42 raises an uncaught TypeError.

Principles applied:
- Static catalog compatibility is separate from operational eligibility.
- A caller-supplied capability list is NOT proof that an installed loader
  supports an adapter.
- Never infer authorization or measured activation.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest


import adaptador_registro as ar
from datetime import datetime, timezone, timedelta

def _recent_ts():
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

VALID_SHA = "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad"

BACKEND_REF = {
    "nombre": "ollama",
    "modelo": "qwen3-coder:30b",
    "sha256": VALID_SHA,
    "formato": "gguf",
    "ram_disponible_mb": 58000,
    "loader_capabilities": ["gguf"],
}


class TestDefect1_MalformedSHA(unittest.TestCase):
    """Defect 1: Matching malformed SHA strings must NOT produce COMPATIBLE.

    When both adapter and backend declare the same malformed SHA (too short,
    non-hex, etc.), the SHA cannot be trusted as identity evidence.
    The verdict must be NO_DATA, not COMPATIBLE.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_malformed_sha_short_produces_no_data(self):
        """Both sides declare sha256='abc' → NO_DATA, not COMPATIBLE."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "abc",  # 3 chars, not SHA-256
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        backend = dict(BACKEND_REF)
        backend["sha256"] = "abc"  # same malformed SHA
        resultado = self.reg.es_compatible("x-v1", backend)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Defect 1: matching malformed short SHA produced COMPATIBLE: {resultado}",
        )
        self.assertEqual(
            resultado["estado"],
            "NO_DATA",
            f"Defect 1: expected NO_DATA for malformed SHA: {resultado}",
        )

    def test_malformed_sha_non_hex_produces_no_data(self):
        """Both sides declare non-hex SHA → NO_DATA, not COMPATIBLE."""
        bad_sha = "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": bad_sha,
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        backend = dict(BACKEND_REF)
        backend["sha256"] = bad_sha
        resultado = self.reg.es_compatible("x-v1", backend)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Defect 1: matching non-hex SHA produced COMPATIBLE: {resultado}",
        )

    def test_malformed_sha_32_chars_produces_no_data(self):
        """Both sides declare 32-char SHA (MD5 length) → NO_DATA."""
        bad_sha = "a" * 32  # MD5 length, not SHA-256
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": bad_sha,
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        backend = dict(BACKEND_REF)
        backend["sha256"] = bad_sha
        resultado = self.reg.es_compatible("x-v1", backend)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Defect 1: matching 32-char SHA produced COMPATIBLE: {resultado}",
        )

    def test_valid_sha_still_compatible(self):
        """A proper 64-char hex SHA that matches → still COMPATIBLE."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"timestamp": _recent_ts()},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Valid SHA should still be COMPATIBLE: {resultado}",
        )


class TestDefect2_InventedLoaderCapabilities(unittest.TestCase):
    """Defect 2: Invented loader_capabilities must NOT produce COMPATIBLE.

    A caller-supplied capability list is NOT proof that an installed loader
    supports an adapter. Only known formats (peft, gguf) are accepted.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_invented_loader_caps_produces_no_data(self):
        """loader_capabilities=['magic', 'telepathy'] → NO_DATA."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        backend = dict(BACKEND_REF)
        backend["loader_capabilities"] = ["magic_format", "telepathy"]
        resultado = self.reg.es_compatible("x-v1", backend)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Defect 2: invented loader caps produced COMPATIBLE: {resultado}",
        )

    def test_single_invented_cap_produces_no_data(self):
        """loader_capabilities=['custom_v2'] → NO_DATA."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        backend = dict(BACKEND_REF)
        backend["loader_capabilities"] = ["custom_v2"]
        resultado = self.reg.es_compatible("x-v1", backend)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Defect 2: single invented cap produced COMPATIBLE: {resultado}",
        )

    def test_known_loader_caps_still_compatible(self):
        """loader_capabilities=['gguf'] → still COMPATIBLE."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"timestamp": _recent_ts()},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Known loader caps should still be COMPATIBLE: {resultado}",
        )

    def test_mixed_known_and_invented_caps(self):
        """loader_capabilities=['gguf', 'magic'] → at least one known → OK."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"timestamp": _recent_ts()},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        backend = dict(BACKEND_REF)
        backend["loader_capabilities"] = ["gguf", "magic_format"]
        resultado = self.reg.es_compatible("x-v1", backend)
        # At least one known format is present, so it can be COMPATIBLE
        self.assertEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Mixed caps with known format should be COMPATIBLE: {resultado}",
        )


class TestDefect3_StaleTelemetry(unittest.TestCase):
    """Defect 3: Stale telemetry must not be treated as current evidence.

    If a measurement has a timestamp that is clearly stale (years old),
    it should not be used as current eligibility evidence.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_stale_telemetry_produces_no_data(self):
        """Telemetry from 2020 with timestamp → NO_DATA(stale_telemetry)."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {
                "ram_pico_mb": 20123,
                "temp_max_c": 65,
                "timestamp": "2020-01-01T00:00:00Z",  # clearly stale
            },
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Defect 3: stale telemetry produced COMPATIBLE: {resultado}",
        )

    def test_recent_telemetry_still_compatible(self):
        """Telemetry with recent timestamp → still COMPATIBLE."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {
                "ram_pico_mb": 20123,
                "temp_max_c": 65,
                "timestamp": "2026-11-13T12:00:00Z",  # recent
            },
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Recent telemetry should be COMPATIBLE: {resultado}",
        )

    def test_telemetry_without_timestamp_is_ok(self):
        """Telemetry without timestamp → NO_DATA(measurement_timestamp_missing).

        A measurement dict without a timestamp cannot prove the data is current.
        This is NO_DATA, not COMPATIBLE.
        """
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {
                "ram_pico_mb": 20123,
                "temp_max_c": 65,
                # No timestamp — cannot verify freshness
            },
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(
            resultado["estado"],
            "NO_DATA",
            f"Telemetry without timestamp should be NO_DATA: {resultado}",
        )
        self.assertIn("timestamp", resultado.get("causa", "").lower())


class TestDefect4_NegativeRAM(unittest.TestCase):
    """Defect 4: Negative RAM measurements must NOT produce COMPATIBLE.

    A negative ram_pico_mb is physically impossible and indicates corrupted
    or fabricated data. It must be rejected.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_negative_ram_pico_produces_no_data(self):
        """ram_pico_mb=-100 → NO_DATA, not COMPATIBLE."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"ram_pico_mb": -100, "timestamp": _recent_ts()},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Defect 4: negative RAM produced COMPATIBLE: {resultado}",
        )

    def test_negative_ram_disponible_produces_no_data(self):
        """ram_disponible_mb=-5000 → NO_DATA, not COMPATIBLE."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"ram_pico_mb": 20123, "timestamp": _recent_ts()},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        backend = dict(BACKEND_REF)
        backend["ram_disponible_mb"] = -5000
        resultado = self.reg.es_compatible("x-v1", backend)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Defect 4: negative available RAM produced COMPATIBLE: {resultado}",
        )

    def test_valid_positive_ram_still_compatible(self):
        """Normal positive RAM values → still COMPATIBLE."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"ram_pico_mb": 20123, "timestamp": _recent_ts()},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"Valid positive RAM should be COMPATIBLE: {resultado}",
        )


class TestDefect5_TargetModulesTypeError(unittest.TestCase):
    """Defect 5: target_modules=42 must NOT raise TypeError.

    When peft_config.target_modules is an integer (42) instead of a list,
    the code must handle it gracefully and return NO_DATA, not crash.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_target_modules_integer_no_crash(self):
        """target_modules=42 → NO_DATA, not TypeError."""
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
                    "peft_config": {"target_modules": 42},  # integer, not list
                }
            },
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f)

        try:
            resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
            self.assertNotEqual(
                resultado["estado"],
                "COMPATIBLE",
                f"Defect 5: target_modules=42 produced COMPATIBLE: {resultado}",
            )
        except TypeError as e:
            self.fail(f"Defect 5: target_modules=42 raised TypeError: {e}")

    def test_target_modules_string_no_crash(self):
        """target_modules='q_proj' (string) → NO_DATA, not TypeError."""
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
                    "peft_config": {"target_modules": "q_proj"},  # string, not list
                }
            },
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f)

        try:
            resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
            # Should not crash
            self.assertIn(
                resultado["estado"],
                ["NO_DATA", "INCOMPATIBLE"],
                f"Defect 5: string target_modules produced {resultado}",
            )
        except TypeError as e:
            self.fail(f"Defect 5: string target_modules raised TypeError: {e}")

    def test_target_modules_dict_no_crash(self):
        """target_modules={'a':1} (dict) → NO_DATA, not TypeError."""
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
                    "peft_config": {"target_modules": {"a": 1}},  # dict, not list
                }
            },
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f)

        try:
            resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
            self.assertNotEqual(
                resultado["estado"],
                "COMPATIBLE",
                f"Defect 5: dict target_modules produced COMPATIBLE: {resultado}",
            )
        except TypeError as e:
            self.fail(f"Defect 5: dict target_modules raised TypeError: {e}")


class TestTelemetryGaps(unittest.TestCase):
    """Regression tests for the three telemetry validation gaps.

    These ensure that malformed timestamps, missing timestamps, and missing
    measurement objects all produce NO_DATA rather than COMPATIBLE.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_malformed_timestamp_produces_no_data(self):
        """Malformed timestamp string → NO_DATA(measurement_timestamp_malformed)."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {
                "ram_pico_mb": 20123,
                "timestamp": "not-a-real-timestamp",  # malformed
            },
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(
            resultado["estado"],
            "NO_DATA",
            f"Malformed timestamp should be NO_DATA: {resultado}",
        )
        self.assertIn("timestamp_malformed", resultado.get("causa", ""))

    def test_missing_timestamp_produces_no_data(self):
        """Measurement dict without timestamp → NO_DATA(measurement_timestamp_missing)."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {
                "ram_pico_mb": 20123,
                # No timestamp key
            },
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(
            resultado["estado"],
            "NO_DATA",
            f"Missing timestamp should be NO_DATA: {resultado}",
        )
        self.assertIn("timestamp_missing", resultado.get("causa", ""))

    def test_missing_medicion_produces_no_data(self):
        """No measurement object at all → NO_DATA(medicion_missing)."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": VALID_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
            # No medición at all
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(
            resultado["estado"],
            "NO_DATA",
            f"Missing medición should be NO_DATA: {resultado}",
        )
        self.assertIn("medicion_missing", resultado.get("causa", ""))

    def test_non_dict_medicion_produces_no_data(self):
        """medicion as a string → NO_DATA(medicion_malformed)."""
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
                    "peft_config": {"target_modules": ["q_proj"]},
                    "medicion": "some_string",  # not a dict
                }
            },
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f)
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(
            resultado["estado"],
            "NO_DATA",
            f"Non-dict medición should be NO_DATA: {resultado}",
        )
        self.assertIn("medicion_malformed", resultado.get("causa", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
