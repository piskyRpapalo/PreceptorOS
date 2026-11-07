"""Verify a visit record signed by the web page's ephemeral Ed25519 key.

Measured web format (public/game/visitor_account.js): the signed bytes are the
UTF-8 of JSON.stringify(record), the public key is raw Ed25519 as 64 hex chars,
the signature is "ed25519:" + 128 hex chars (raw 64 bytes). The check runs the
OpenSSL CLI, bounded by a timeout, with no network and no persistent key.
"""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

LIMIT = 1024
SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")
KEY = re.compile(r"^[0-9a-f]{64}$")
SIG = re.compile(r"^ed25519:([0-9a-f]{128})$")


def _out(state, cause):
    return {"estado": state, "causa": cause}


def _message(record):
    if isinstance(record, dict):
        record = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
    if isinstance(record, str):
        record = record.encode("utf-8")
    return record if isinstance(record, bytes) else None


def verificar(registro, clave_publica, firma):
    try:
        data = _message(registro)
        if data is None:
            return _out("RECHAZADA", "record must be text, bytes or an object")
        if len(data) >= LIMIT:
            return _out("RECHAZADA", "record exceeds the 1024 byte frame budget")
        if not isinstance(clave_publica, str) or not KEY.match(clave_publica):
            return _out("RECHAZADA", "public key must be 64 lowercase hex chars")
        match = SIG.match(firma) if isinstance(firma, str) else None
        if not match:
            return _out("RECHAZADA", "signature must be ed25519: plus 128 hex chars")
        try:
            parsed = json.loads(data.decode("utf-8"))
        except ValueError:
            return _out("RECHAZADA", "record is not valid JSON")
        if not isinstance(parsed, dict) or parsed.get("clave_publica") != clave_publica:
            return _out("RECHAZADA", "record does not name the signing key")
        openssl = shutil.which("openssl")
        if not openssl:
            return _out("NO_DATA", "openssl is unavailable")
        with tempfile.TemporaryDirectory(prefix="visita-web-") as folder:
            base = Path(folder)
            (base / "key.der").write_bytes(SPKI_PREFIX + bytes.fromhex(clave_publica))
            (base / "message").write_bytes(data)
            (base / "signature").write_bytes(bytes.fromhex(match.group(1)))
            done = subprocess.run(
                [openssl, "pkeyutl", "-verify", "-pubin", "-keyform", "DER",
                 "-inkey", str(base / "key.der"), "-rawin",
                 "-in", str(base / "message"), "-sigfile", str(base / "signature")],
                capture_output=True, timeout=10, check=False)
        if done.returncode == 0:
            return _out("VERIFICADA", "Ed25519 signature verifies against the stated key")
        return _out("RECHAZADA", "signature does not verify")
    except subprocess.TimeoutExpired:
        return _out("NO_DATA", "openssl timed out")
    except Exception as error:
        return _out("NO_DATA", "verification could not run: " + type(error).__name__)
