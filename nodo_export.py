"""Explicit, human-triggered export of an already signed node credential."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

import nodo_app

ENDPOINT = "https://api.preceptoros.org/api/v1/cedulas"
TIMEOUT_S = 15
CAUSAS_ADUANA = {
    "clave_publica_no_configurada", "plan_firmado_no_configurado",
    "plan_no_coincide", "firma_cedula_rechazada", "cedula_mal_formada",
    "registro_no_disponible", "cuerpo_invalido", "cuerpo_fuera_de_rango",
}


def _rechazo(codigo: str, http: int = 409) -> dict:
    return {"estado": "bloqueado", "codigo": codigo, "http": http}


def enviar(datos, *, transport=None, signers=None) -> dict:
    """Validate and forward one signed credential; never create a signature.

    The only network path is called by the explicit POST route. Tests inject a
    transport, so the live endpoint is never contacted by the test suite.
    """
    if not isinstance(datos, dict) or set(datos) != {"cedula"}:
        return _rechazo("cuerpo_invalido", 400)
    cedula = datos.get("cedula")
    forma = nodo_app._forma(cedula)
    if forma:
        return _rechazo("cedula_rechazada", 422)
    estado, causa = nodo_app.autenticidad(cedula, signers=signers)
    if estado == "NO_DATA":
        return _rechazo("firma_no_disponible", 503)
    if estado != "OK":
        return _rechazo("firma_rechazada", 422)

    cuerpo = json.dumps({"cedula": cedula}, ensure_ascii=False,
                        sort_keys=True, separators=(",", ":")).encode("utf-8")
    if transport is None:
        req = urllib.request.Request(
            ENDPOINT, data=cuerpo,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                if resp.status < 200 or resp.status >= 300:
                    return _rechazo("aduana_rechazo", 502)
                respuesta = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                fallo = json.loads(exc.read().decode("utf-8"))
                codigo = fallo.get("codigo") if isinstance(fallo, dict) else None
            except (UnicodeDecodeError, json.JSONDecodeError):
                codigo = None
            return _rechazo(codigo, 409) if codigo in CAUSAS_ADUANA else _rechazo("aduana_rechazo", 502)
        except (urllib.error.URLError, TimeoutError, OSError):
            return _rechazo("aduana_no_disponible", 502)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _rechazo("recibo_invalido", 502)
    else:
        try:
            respuesta = transport(ENDPOINT, cuerpo)
        except Exception:
            return _rechazo("aduana_no_disponible", 502)

    if not isinstance(respuesta, dict):
        return _rechazo("recibo_invalido", 502)
    paquete = respuesta.get("paquete")
    if (not isinstance(paquete, dict)
            or paquete.get("esquema") != "preceptoros/cedula-nodo/1"
            or paquete.get("firma", "missing") is not None
            or not isinstance(paquete.get("pares"), list)
            or len(paquete["pares"]) != 1):
        return _rechazo("paquete_invalido", 502)
    return {"estado": "encolado", "codigo": "recibido",
            "recibidos": respuesta.get("recibidos")}
