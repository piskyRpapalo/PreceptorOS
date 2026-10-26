"""Local-only coverage for prefixed synthetic node-account records."""

import hashlib
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import cuenta_cangrejo


class TestSyntheticNodeAccounts(unittest.TestCase):
    def test_prefixed_account_record_needs_no_key_generation_or_persistence(self):
        public_key_shape = hashlib.sha256(b"test-only-public-key").hexdigest()
        created_at = datetime(2026, 10, 25, tzinfo=timezone.utc)

        with (
            patch.object(
                cuenta_cangrejo,
                "generar_par",
                side_effect=AssertionError("test must not generate a key pair"),
            ),
            patch.object(
                cuenta_cangrejo,
                "firmar",
                side_effect=AssertionError("test must not sign"),
            ),
            patch.object(
                cuenta_cangrejo,
                "_run",
                side_effect=AssertionError("test must not persist an account"),
            ),
        ):
            record = cuenta_cangrejo.crear_cuenta(
                cuenta_cangrejo.PHASES[0],
                "nodo.0.test-account-001",
                [cuenta_cangrejo.SCOPES[0]],
                public_key_shape,
                created_at,
            )

        self.assertEqual(record["nodo"], "nodo.0.test-account-001")
        self.assertEqual(record["clave_publica"], public_key_shape)
        self.assertFalse(
            any("private" in key.lower() or "secret" in key.lower() for key in record)
        )


if __name__ == "__main__":
    unittest.main()
