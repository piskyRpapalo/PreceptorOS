"""prueba_edificio.py · signed receipt of a proof taken in a building chat.

Loops 8 and 9 of the F0 plan (odd/tasks/f0-one-loop-20261107.md): a local brain answers a
question in a building chat; the proof becomes a receipt `preceptoros.building-proof/1`
signed by an ephemeral crab account. Without a verified signature there is no datum.

Cryptography is not reimplemented: accounts and signatures are checked by
`cuenta_cangrejo` (Ed25519 through ssh-keygen). This module fixes the receipt shape,
its canonical bytes (< 1,024 B), and the verdict. `verificar` never raises: every
failure, including an unmeasurable one, is REJECTED with its cause, because a proof
that cannot be verified must not feed a benchmark or a dataset.
"""
from __future__ import annotations

import json
import re

import cuenta_cangrejo as _cangrejo

SCHEMA = "preceptoros.building-proof/1"
KEYS = ("esquema", "id", "edificio", "pregunta_sha256", "respuesta_sha256", "bytes", "fecha", "maquina")
SCOPE = "aportar_datos"
LIMIT = 1024
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_HEX = re.compile(r"^[0-9a-f]{64}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
# decision mia (sin firma): the public-names allowlist has no machine-alias list
# (keys: routes, api_routes, commands, names_by_source), so the alias is checked by shape
# only. Private names never belong here; the rack writer maps machines to public aliases.
_ALIAS = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")


def _no(causa):
    return {"estado": "RECHAZADA", "causa": causa}


def canonico(carga):
    """Canonical UTF-8 JSON bytes of the receipt; ValueError at or above 1,024 B."""
    raw = json.dumps(carga, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(raw) >= LIMIT:
        raise ValueError("receipt reaches the 1024-byte ceiling")
    return raw


def validar(carga):
    """Shape check with one concrete cause per field."""
    if not isinstance(carga, dict):
        return _no("receipt_not_object")
    if set(carga) != set(KEYS):
        return _no("receipt_keys_invalid")
    if carga["esquema"] != SCHEMA:
        return _no("esquema_invalid")
    for k in ("id", "edificio"):
        if not isinstance(carga[k], str) or not _SLUG.fullmatch(carga[k]):
            return _no(f"{k}_invalid")
    for k in ("pregunta_sha256", "respuesta_sha256"):
        if not isinstance(carga[k], str) or not _HEX.fullmatch(carga[k]):
            return _no(f"{k}_invalid")
    if type(carga["bytes"]) is not int or carga["bytes"] <= 0:
        return _no("bytes_invalid")
    if not isinstance(carga["fecha"], str) or not _DATE.fullmatch(carga["fecha"]):
        return _no("fecha_invalid")
    if not isinstance(carga["maquina"], str) or not _ALIAS.fullmatch(carga["maquina"]):
        return _no("maquina_invalid")
    try:
        canonico(carga)
    except ValueError:
        return _no("receipt_too_large")
    return {"estado": "VALIDA"}


def _verificar(sobre, signers, public_path):
    if not isinstance(sobre, dict):
        return _no("envelope_not_object")
    carga, cuenta, firma = sobre.get("recibo"), sobre.get("cuenta"), sobre.get("firma")
    forma = validar(carga)
    if forma["estado"] != "VALIDA":
        return forma
    if not isinstance(firma, str) or not firma.strip():
        return _no("signature_missing")
    if not isinstance(cuenta, dict):
        return _no("account_missing")
    estado = _cangrejo.verificar_cuenta(cuenta, signers=signers)
    if estado.get("estado") != "OK":
        return _no("account_" + str(estado.get("causa") or "unverified").replace(" ", "_"))
    if SCOPE not in cuenta.get("ambito", []):
        return _no("account_scope_missing_" + SCOPE)
    if not public_path:
        return _no("public_key_missing")
    firma_ok = _cangrejo.verificar_firma(cuenta, firma, canonico(carga), public_path)
    if firma_ok.get("estado") != "OK":
        return _no("signature_" + str(firma_ok.get("causa") or "unverified").replace(" ", "_"))
    return {"estado": "VERIFICADA", "id": carga["id"]}


def verificar(sobre, signers=None, public_path=None):
    """{"recibo","cuenta","firma"} -> VERIFICADA or RECHAZADA with cause. Never raises.

    decision mia (sin firma): `signers` (the Sovereign's allowed_signers file) and
    `public_path` (the account's public key file) are explicit, because cuenta_cangrejo
    needs both and this module must not guess house paths.
    """
    try:
        return _verificar(sobre, signers, public_path)
    except Exception as exc:  # any failure is a rejection with its cause, never a pass
        return _no("verification_error_" + type(exc).__name__)
