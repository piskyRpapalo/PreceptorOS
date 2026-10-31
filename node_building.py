"""Local node identity provisioning and explicit Aduana building declaration.

The browser never receives the heartbeat credential. Network access exists only
inside ``declarar_edificio`` and is called by the explicit local PWA action.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

IDENTITY_SCHEMA = "preceptoros.pwa-node-identity/1"
DECLARATION_SCHEMA = "preceptoros.edificio-declaracion/1"
RECEIPT_SCHEMA = "preceptoros.recibo-edificio/1"
BUILDING_ID = "observatorio-primer-ancla"
ASSIGNED_NODE = "primer-ancla"
ENDPOINT = "https://api.preceptoros.org/api/v1/edificios"
KEY_FILE_ENV = "PRECEPTOROS_HEARTBEAT_CREDENTIAL_FILE"
KEY_HEADER = "x-heartbeat-key"
NODE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MAX_RESPONSE = 16_384
TIMEOUT_S = 8


def _canonical(value: object) -> bytes:
    """Match Aduana's sorted, compact, ASCII-escaped canonical JSON bytes."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("ascii")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _identity_path(base: os.PathLike | str) -> Path:
    return Path(base) / "node-identity.json"


def _read_identity(base: os.PathLike | str) -> tuple[str | None, str | None]:
    path = _identity_path(base)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        return None, "identidad_no_provisionada"
    except OSError:
        return None, "identidad_local_no_disponible"
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
            return None, "identidad_local_invalida"
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            fd = -1
            raw = stream.read(2049)
    except (OSError, UnicodeError):
        return None, "identidad_local_invalida"
    finally:
        if fd >= 0:
            os.close(fd)
    if len(raw.encode("utf-8")) > 2048:
        return None, "identidad_local_invalida"
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None, "identidad_local_invalida"
    if (not isinstance(value, dict) or set(value) != {"esquema", "node_id"}
            or value.get("esquema") != IDENTITY_SCHEMA
            or not isinstance(value.get("node_id"), str)
            or not NODE_ID.fullmatch(value["node_id"])):
        return None, "identidad_local_invalida"
    return value["node_id"], None


def leer_identidad(base: os.PathLike | str) -> dict:
    node_id, cause = _read_identity(base)
    if cause:
        return {"estado": "NO_DATA", "causa": cause}
    return {"estado": "configurada", "node_id": node_id}


def provisionar_identidad(base: os.PathLike | str, node_id: object) -> dict:
    """Create the public node-ID config once; never overwrite a different ID."""
    if not isinstance(node_id, str) or not NODE_ID.fullmatch(node_id):
        return {"estado": "NO_DATA", "causa": "identidad_canonica_invalida"}
    root = Path(base)
    try:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not stat.S_ISDIR(os.lstat(root).st_mode):
            return {"estado": "NO_DATA", "causa": "casa_local_invalida"}
    except OSError:
        return {"estado": "NO_DATA", "causa": "casa_local_no_disponible"}

    path = _identity_path(root)
    payload = _canonical({"esquema": IDENTITY_SCHEMA, "node_id": node_id}) + b"\n"
    temp_name = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix=".node-identity-", dir=root)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            # Hard-link creation is atomic and fails if another identity won.
            os.link(temp_name, path, follow_symlinks=False)
            os.chmod(path, 0o600, follow_symlinks=False)
            dir_fd = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
            return {"estado": "provisionada", "node_id": node_id}
        except FileExistsError:
            existing, cause = _read_identity(root)
            if cause:
                return {"estado": "NO_DATA", "causa": cause}
            if existing == node_id:
                return {"estado": "provisionada", "node_id": node_id, "repetida": True}
            return {"estado": "NO_DATA", "causa": "identidad_ya_provisionada"}
    except OSError:
        return {"estado": "NO_DATA", "causa": "identidad_local_no_disponible"}
    finally:
        if temp_name:
            try:
                os.unlink(temp_name)
            except OSError:
                pass


def _read_key(base: os.PathLike | str, *, key_path: os.PathLike | str | None = None) -> tuple[str | None, str | None]:
    path = Path(key_path) if key_path else Path(base) / "heartbeat-key"
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        return None, "credencial_no_provisionada"
    except OSError:
        return None, "credencial_local_invalida"
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode)
                or stat.S_IMODE(info.st_mode) & 0o077):
            return None, "credencial_local_invalida"
        with os.fdopen(fd, "r", encoding="ascii") as stream:
            fd = -1
            raw = stream.read(67)
    except (OSError, UnicodeError):
        return None, "credencial_local_invalida"
    finally:
        if fd >= 0:
            os.close(fd)
    if len(raw) > 66:
        return None, "credencial_local_invalida"
    value = raw.rstrip("\r\n")
    if raw not in (value, value + "\n", value + "\r\n") or not HEX64.fullmatch(value):
        return None, "credencial_local_invalida"
    return value, None


def _valid_receipt(value: object, node_id: str, body: dict) -> tuple[bool, str]:
    required = {"esquema", "estado", "causa", "nodo", "edificio", "payload_sha256",
                "recibido_en", "procedencia", "recibo_sha256"}
    if not isinstance(value, dict) or set(value) != required:
        return False, "recibo_mal_formado"
    if value.get("esquema") != RECEIPT_SCHEMA or value.get("estado") != "recibido" or value.get("causa") is not None:
        return False, "declaracion_rechazada"
    if value.get("nodo") != node_id or value.get("edificio") != BUILDING_ID:
        return False, "recibo_no_coincide"
    payload_hash = hashlib.sha256(_canonical(body)).hexdigest()
    if value.get("payload_sha256") != payload_hash:
        return False, "recibo_no_coincide"
    if (not isinstance(value.get("recibido_en"), str)
            or not value["recibido_en"].endswith("Z")
            or not isinstance(value.get("procedencia"), str)
            or not value["procedencia"]
            or not HEX64.fullmatch(str(value.get("recibo_sha256", "")))):
        return False, "recibo_mal_formado"
    base = {key: value[key] for key in value if key != "recibo_sha256"}
    if hashlib.sha256(_canonical(base)).hexdigest() != value["recibo_sha256"]:
        return False, "recibo_no_coincide"
    return True, ""


def _http_post(endpoint: str, body: bytes, headers: dict, timeout: int) -> tuple[int, bytes, str]:
    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, response_headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect())
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        data = response.read(MAX_RESPONSE + 1)
        return response.status, data, response.geturl()


def declarar_edificio(base: os.PathLike | str, *, key_path: os.PathLike | str | None = None,
                     transport=None) -> dict:
    """Make the fixed declaration; injected transport keeps tests offline."""
    node_id, cause = _read_identity(base)
    if cause:
        return {"estado": "NO_DATA", "causa": cause}
    if node_id != ASSIGNED_NODE:
        return {"estado": "NO_DATA", "causa": "nodo_sin_edificio_asignado"}
    key, cause = _read_key(base, key_path=key_path)
    if cause:
        return {"estado": "NO_DATA", "causa": cause}
    body_value = {"esquema": DECLARATION_SCHEMA, "edificio": BUILDING_ID}
    body = _canonical(body_value)
    if len(body) > 1024:
        return {"estado": "NO_DATA", "causa": "declaracion_fuera_de_rango"}
    headers = {"Content-Type": "application/json", KEY_HEADER: key}
    try:
        if transport is None:
            status, raw, final_url = _http_post(ENDPOINT, body, headers, TIMEOUT_S)
        else:
            status, raw, final_url = transport(ENDPOINT, body, headers, TIMEOUT_S)
    except (OSError, TimeoutError, urllib.error.URLError):
        return {"estado": "NO_DATA", "causa": "aduana_no_disponible"}
    except Exception:
        return {"estado": "NO_DATA", "causa": "aduana_no_disponible"}
    if final_url != ENDPOINT:
        return {"estado": "NO_DATA", "causa": "destino_no_coincide"}
    if not isinstance(raw, (bytes, bytearray)) or len(raw) > MAX_RESPONSE:
        return {"estado": "NO_DATA", "causa": "respuesta_fuera_de_rango"}
    try:
        result = json.loads(bytes(raw).decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError, ValueError):
        return {"estado": "NO_DATA", "causa": "respuesta_mal_formada"}
    if status not in (200, 202):
        code = result.get("causa") if isinstance(result, dict) else None
        return {"estado": "NO_DATA", "causa": code if isinstance(code, str) and re.fullmatch(r"[a-z0-9_]{1,64}", code)
                else "declaracion_rechazada", "http": status}
    if (not isinstance(result, dict) or result.get("esquema") != RECEIPT_SCHEMA
            or result.get("estado") != "recibido"):
        code = result.get("causa") if isinstance(result, dict) else None
        return {"estado": "NO_DATA", "causa": code if isinstance(code, str) and re.fullmatch(r"[a-z0-9_]{1,64}", code)
                else "declaracion_rechazada", "http": status}
    valid, receipt_cause = _valid_receipt(result, node_id, body_value)
    if not valid:
        return {"estado": "NO_DATA", "causa": receipt_cause, "http": status}
    return {"estado": "recibido", "causa": None, "nodo": node_id,
            "edificio": BUILDING_ID, "payload_sha256": result["payload_sha256"],
            "recibo_sha256": result["recibo_sha256"], "http": status}
