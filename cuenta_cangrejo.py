import datetime
import atexit
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = "preceptoros.cuenta-cangrejo/1"
SCOPES = ("memoria_compartida", "conectar_ia", "herramientas", "aportar_datos")
PHASES = ("puente", "errante")
STATES = ("solicitado", "linkeado", "revocado")
HEX = re.compile(r"^[0-9a-f]{64}$")
NODE = re.compile(r"^nodo\.[0-9]{1,6}\.[a-z0-9][a-z0-9-]{0,30}$")
NAMESPACE = "preceptoros-agent"
ACCOUNT_NAMESPACE = "preceptoros-account"


def _utc(value=None):
    value = value or datetime.datetime.now(datetime.timezone.utc)
    return value.astimezone(datetime.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run(args, data=None):
    return subprocess.run(args, input=data, capture_output=True, timeout=20, check=False)


def _fingerprint(public_path):
    return hashlib.sha256(Path(public_path).read_bytes().strip()).hexdigest()


def generar_par(persistente=False, directorio=None):
    if not shutil.which("ssh-keygen"):
        raise RuntimeError("NO_DATA: ssh-keygen is unavailable")
    if persistente:
        root = Path(directorio) if directorio else Path.home() / ".preceptoros" / "agent-keys"
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(root, 0o700)
        holder = root
    else:
        holder = Path(tempfile.mkdtemp(prefix="preceptor-agent-"))
        os.chmod(holder, 0o700)
        atexit.register(shutil.rmtree, holder, ignore_errors=True)
    private = holder / "identity"
    result = _run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private), "-C", "agent"])
    if result.returncode:
        if not persistente:
            shutil.rmtree(holder, ignore_errors=True)
        raise RuntimeError("NO_DATA: Ed25519 key generation failed")
    os.chmod(private, 0o600)
    return _fingerprint(str(private) + ".pub"), str(private)


def firmar(payload, ruta_privada):
    if not isinstance(payload, bytes) or len(payload) >= 1024:
        raise ValueError("payload must be bytes below 1024 B")
    if not Path(ruta_privada).is_file() or not shutil.which("ssh-keygen"):
        raise RuntimeError("NO_DATA: private key or ssh-keygen unavailable")
    with tempfile.TemporaryDirectory(prefix="preceptor-sign-") as folder:
        source = Path(folder) / "payload"
        source.write_bytes(payload)
        result = _run(["ssh-keygen", "-q", "-Y", "sign", "-n", NAMESPACE, "-f", ruta_privada, str(source)])
        signature = source.with_name("payload.sig")
        if result.returncode or not signature.is_file():
            raise RuntimeError("NO_DATA: signature creation failed")
        return signature.read_text(encoding="utf-8")


def _verify(payload, signature, public_path):
    if not shutil.which("ssh-keygen"):
        return "NO_DATA", "ssh-keygen is unavailable"
    with tempfile.TemporaryDirectory(prefix="preceptor-verify-") as folder:
        root = Path(folder)
        pub = Path(public_path).read_text(encoding="utf-8").split()
        if len(pub) < 2:
            return "RECHAZADA", "public key format is invalid"
        allowed = root / "allowed_signers"
        allowed.write_text("agent " + pub[0] + " " + pub[1] + "\n", encoding="utf-8")
        source = root / "payload"
        source.write_bytes(payload)
        sig = root / "payload.sig"
        sig.write_text(signature, encoding="utf-8")
        result = _run(["ssh-keygen", "-Y", "verify", "-f", str(allowed), "-I", "agent", "-n", NAMESPACE, "-s", str(sig)], payload)
        return ("OK", "signature verified") if result.returncode == 0 else ("RECHAZADA", "signature verification failed")


def _verify_signer(payload, signature, signers, identity, namespace):
    if not signers or not Path(signers).is_file():
        return "NO_DATA", "allowed signers are unavailable"
    if not shutil.which("ssh-keygen"):
        return "NO_DATA", "ssh-keygen is unavailable"
    with tempfile.TemporaryDirectory(prefix="preceptor-signer-") as folder:
        sig = Path(folder) / "payload.sig"
        sig.write_text(signature, encoding="utf-8")
        result = _run(["ssh-keygen", "-Y", "verify", "-f", str(signers), "-I", identity, "-n", namespace, "-s", str(sig)], payload)
        return ("OK", "signature verified") if result.returncode == 0 else ("RECHAZADA", "signature verification failed")


def _account_payload(cuenta):
    return json.dumps({k: v for k, v in cuenta.items() if k not in ("estado", "firma_ssh")},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verificar_firma(cuenta, firma, payload, public_path):
    if not isinstance(cuenta, dict) or not isinstance(payload, bytes) or not isinstance(firma, str):
        return {"estado": "NO_DATA", "causa": "account, signature, or payload is missing"}
    if len(payload) >= 1024:
        return {"estado": "RECHAZADA", "causa": "payload reaches the 1024-byte ceiling"}
    if cuenta.get("clave_publica") != _fingerprint(public_path):
        return {"estado": "RECHAZADA", "causa": "public key fingerprint does not match account"}
    state, cause = _verify(payload, firma, public_path)
    return {"estado": state, "causa": cause}


def crear_cuenta(fase, nodo, ambito, clave_publica=None, ahora=None):
    if fase not in PHASES or not isinstance(nodo, str) or not NODE.fullmatch(nodo):
        raise ValueError("phase or node is invalid")
    if not isinstance(ambito, list) or not ambito or len(set(ambito)) != len(ambito) or any(x not in SCOPES for x in ambito):
        raise ValueError("scope is invalid")
    if not isinstance(clave_publica, str) or not HEX.fullmatch(clave_publica):
        raise ValueError("a measured public-key fingerprint is required")
    now = ahora or datetime.datetime.now(datetime.timezone.utc)
    expiry = None if fase == "errante" else _utc(now + datetime.timedelta(minutes=30))
    return {"esquema": SCHEMA, "fase": fase, "clave_publica": clave_publica, "nodo": nodo,
            "creada_utc": _utc(now), "caduca_utc": expiry, "ambito": ambito, "estado": "solicitado"}


def activar_cuenta(cuenta, firma_soberano, signers=None):
    valid = verificar_cuenta(cuenta, signers=None)
    if valid["estado"] not in ("NO_DATA", "OK"):
        return valid
    if not isinstance(firma_soberano, str) or not firma_soberano:
        return {"estado": "NO_DATA", "causa": "Sovereign signature is missing"}
    state, cause = _verify_signer(_account_payload(cuenta), firma_soberano, signers, "soberano", ACCOUNT_NAMESPACE)
    if state != "OK":
        return {"estado": state, "causa": cause}
    result = dict(cuenta)
    result["estado"] = "linkeado"
    result["firma_ssh"] = firma_soberano
    return result


def cambiar_fase(cuenta, fase, firma_soberano=None, signers=None):
    if not isinstance(cuenta, dict) or cuenta.get("fase") != "puente" or fase != "errante":
        return {"estado": "RECHAZADA", "causa": "only a bridge-to-wandering transition is defined"}
    if not firma_soberano:
        return {"estado": "RECHAZADA", "causa": "phase change requires a Sovereign signature"}
    result = dict(cuenta)
    result["fase"] = fase
    result["caduca_utc"] = None
    state, cause = _verify_signer(_account_payload(result), firma_soberano, signers, "soberano", ACCOUNT_NAMESPACE)
    if state != "OK":
        return {"estado": state, "causa": cause}
    result["firma_ssh"] = firma_soberano
    return result


def verificar_cuenta(cuenta, signers=None):
    if not isinstance(cuenta, dict) or cuenta.get("esquema") != SCHEMA:
        return {"estado": "RECHAZADA", "causa": "account schema is invalid"}
    if cuenta.get("fase") not in PHASES or cuenta.get("estado") not in STATES or not HEX.fullmatch(str(cuenta.get("clave_publica", ""))):
        return {"estado": "RECHAZADA", "causa": "account fields are invalid"}
    if not NODE.fullmatch(str(cuenta.get("nodo", ""))) or not isinstance(cuenta.get("ambito"), list) or any(x not in SCOPES for x in cuenta["ambito"]):
        return {"estado": "RECHAZADA", "causa": "node or scope is invalid"}
    if cuenta["estado"] == "revocado":
        return {"estado": "RECHAZADA", "causa": "account is revoked"}
    if not signers or not Path(signers).is_file():
        return {"estado": "NO_DATA", "causa": "allowed signers are unavailable"}
    signature = cuenta.get("firma_ssh")
    if not signature:
        return {"estado": "NO_DATA", "causa": "account activation signature is missing"}
    expiry = cuenta.get("caduca_utc")
    if expiry is not None:
        try:
            parsed = datetime.datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        except (TypeError, ValueError):
            return {"estado": "RECHAZADA", "causa": "account expiry is malformed"}
        if parsed <= datetime.datetime.now(datetime.timezone.utc):
            return {"estado": "RECHAZADA", "causa": "account is expired"}
    state, cause = _verify_signer(_account_payload(cuenta), signature, signers, "soberano", ACCOUNT_NAMESPACE)
    return {"estado": state, "causa": cause}


def revocar_cuenta(clave_publica):
    if not isinstance(clave_publica, str) or not HEX.fullmatch(clave_publica):
        return {"estado": "RECHAZADA", "causa": "public-key fingerprint is invalid"}
    return {"estado": "REQUIERE_FIRMA", "clave_publica": clave_publica, "estado_cuenta": "revocado",
            "causa": "revocation record must be persisted by an authorized writer"}


def main():
    if sys.argv[1:] != ["--self-test"]:
        return 2
    fingerprint, private = generar_par()
    payload = b'{"self_test":true}'
    signature = firmar(payload, private)
    result = verificar_firma({"clave_publica": fingerprint}, signature, payload, private + ".pub")
    receipt = {"estado": result["estado"], "maquina": platform.machine() or "NO_DATA", "fecha": _utc(),
               "payload_sha256": hashlib.sha256(payload).hexdigest()}
    encoded = json.dumps(receipt, separators=(",", ":"), sort_keys=True)
    if len(encoded.encode("utf-8")) >= 1024:
        return 1
    print(encoded)
    return 0 if result["estado"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
