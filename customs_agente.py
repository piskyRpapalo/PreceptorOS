import datetime
import hashlib
import json
import platform
import re
import sys
from pathlib import Path

import canales
import cuenta_cangrejo

LIMIT = 1024
SCHEMA = "atlas.accion/1"
ACTIONS = ("esperar", "recoger", "reparar", "aplazar", "bajar_a")
BANDS = ("arrecife", "ruinas", "bosque", "nucleo")


def rechazar(causa):
    return {"estado": "NO_DATA", "causa": str(causa)[:180]}


def validar_payload(payload):
    if not isinstance(payload, bytes):
        return {"estado": "RECHAZADA", "causa": "payload must be bytes"}
    if len(payload) >= LIMIT:
        return {"estado": "RECHAZADA", "causa": "payload reaches the 1024-byte ceiling"}
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return {"estado": "RECHAZADA", "causa": "payload is not UTF-8 JSON"}
    if not isinstance(value, dict) or value.get("esquema") != SCHEMA:
        return {"estado": "RECHAZADA", "causa": "payload schema is not atlas.accion/1"}
    action = value.get("accion")
    allowed = {"esquema", "accion", "origen"} | ({"banda"} if action == "bajar_a" else set())
    if set(value) != allowed or action not in ACTIONS or value.get("origen") not in ("piloto_base", "agente"):
        return {"estado": "RECHAZADA", "causa": "action shape is outside the closed contract"}
    if action == "bajar_a" and value.get("banda") not in BANDS:
        return {"estado": "RECHAZADA", "causa": "action band is invalid"}
    return {"estado": "ACEPTADO", "accion": action, "bytes": len(payload)}


def _key_path(fingerprint, key_dir=None):
    import hashlib
    import casa
    root = Path(key_dir) if key_dir else Path(casa.raiz()) / "agent-keys"
    for public in root.glob("*.pub") if root.is_dir() else ():
        if hashlib.sha256(public.read_bytes().strip()).hexdigest() == fingerprint:
            return public
    return None


def verificar_entrada(cuenta, firma, payload, signers=None, key_dir=None, ahora=None):
    if not isinstance(cuenta, dict):
        return {"estado": "NO_DATA", "causa": "no_account"}
    import casa
    signer_path = Path(signers) if signers else Path(casa.raiz()) / "allowed_signers_accounts"
    account = cuenta_cangrejo.verificar_cuenta(cuenta, signer_path)
    if account["estado"] != "OK" or cuenta.get("estado") != "linkeado":
        return {"estado": account["estado"], "causa": account.get("causa", "account is not active")}
    parsed = validar_payload(payload)
    if parsed["estado"] != "ACEPTADO":
        return parsed
    action = parsed["accion"]
    scope = "aportar_datos" if action in ("recoger",) else "herramientas"
    if scope not in cuenta.get("ambito", []):
        return {"estado": "RECHAZADA", "causa": "action is outside account scope"}
    expiry = cuenta.get("caduca_utc")
    if expiry:
        try:
            deadline = datetime.datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        except (TypeError, ValueError):
            return {"estado": "RECHAZADA", "causa": "account expiry is malformed"}
        if deadline <= (ahora or datetime.datetime.now(datetime.timezone.utc)):
            return {"estado": "RECHAZADA", "causa": "account is expired"}
    public = _key_path(cuenta.get("clave_publica"), key_dir)
    if public is None:
        return {"estado": "NO_DATA", "causa": "matching public key is unavailable locally"}
    verified = cuenta_cangrejo.verificar_firma(cuenta, firma, payload, public)
    if verified["estado"] != "OK":
        return {"estado": verified["estado"], "causa": verified["causa"]}
    return {"estado": "ACEPTADO", "causa": "signature, account, scope, and payload verified"}


def registrar_entrada(cuenta, accion, resultado, base=None):
    if not isinstance(cuenta, dict) or not isinstance(resultado, dict):
        return rechazar("account or result is missing")
    key = cuenta.get("clave_publica")
    if not isinstance(key, str) or not re.fullmatch(r"[0-9a-f]{64}", key):
        return rechazar("account fingerprint is invalid")
    try:
        receipt = canales.di("app", "agent-" + key[:12], json.dumps({"action": str(accion)[:40], "status": str(resultado.get("estado", "NO_DATA"))[:20]}, separators=(",", ":")), sello="MEDIDO", rol="agent", maquina={"fingerprint": key[:12]}, base=base)
    except (ValueError, OSError) as exc:
        return rechazar(type(exc).__name__)
    return {"estado": "REGISTRADO", "n": receipt.get("n")}


def main():
    if sys.argv[1:] != ["--self-test"]:
        return 2
    payload = b'{"esquema":"atlas.accion/1","accion":"esperar","origen":"agente"}'
    checked = validar_payload(payload)
    receipt = {"estado": checked["estado"], "maquina": platform.machine() or "NO_DATA",
               "fecha": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "payload_sha256": hashlib.sha256(payload).hexdigest()}
    encoded = json.dumps(receipt, separators=(",", ":"), sort_keys=True)
    if len(encoded.encode("utf-8")) >= LIMIT:
        return 1
    print(encoded)
    return 0 if checked["estado"] == "ACEPTADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
