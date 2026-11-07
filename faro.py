"""Observatory beacon (joya 15): the direct voice proof and the app-with-source proof, kept apart.

Law of the beacon: hexelion answering on its own station is NOT the app answering with a cited source.
Each proof carries its own state, cause and time; the frame never folds them into one verdict.
Loopback only, no redirects, no proxies; the clock is injected so the core is testable.
"""
import ipaddress
import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

import hexelion_proxy

SCHEMA = "preceptoros.faro/1"
CEILING_B = 1024
APP_TIMEOUT_S = 180
MAX_APP_RESPONSE_B = 65536
VOICE_PROMPT = "Answer in one short sentence: are you awake?"


def _ms(start, end):
    return round((end - start) * 1000, 1)


def voz_directa(*, endpoint=None, opener=None, clock=time.monotonic):
    """The station alone: hexelion_proxy.ask with a fixed prompt; wall time and generation time."""
    t0 = clock()
    r = hexelion_proxy.ask(VOICE_PROMPT, endpoint=endpoint, opener=opener, clock=clock)
    out = {"prueba": "voz_directa", "estado": r.get("estado", "NO_DATA"), "ms_total": _ms(t0, clock())}
    if out["estado"] == "MEASURED":
        out["ms_generacion"] = round(r["ms"], 1)
        out["modelo"] = r.get("modelo")
    else:
        out["causa"] = r.get("causa", "voice_unmeasured")
    return out


def _app_base(app):
    try:
        parts = urlsplit(app or "")
        ip = ipaddress.ip_address(parts.hostname or "")
        if parts.scheme != "http" or not ip.is_loopback or parts.port is None or parts.path not in ("", "/"):
            return None
        return f"http://{parts.hostname}:{parts.port}"
    except (ValueError, TypeError):
        return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def app_con_fuente(pregunta, *, app=None, opener=None, clock=time.monotonic):
    """The app path: /api/hexelion/chat must answer MEASURED, in Hexelion's voice, with at least one source."""
    base = _app_base(app)
    out = {"prueba": "app_con_fuente"}
    if base is None:
        return dict(out, estado="NO_DATA", causa="app_loopback_required", ms_total=0.0)
    body = json.dumps({"texto": pregunta, "panel": "mando"}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(base + "/api/hexelion/chat", data=body, method="POST", headers={
        "Content-Type": "application/json", "Origin": base, "Sec-Fetch-Site": "same-origin"})
    open_url = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect()).open
    t0 = clock()
    try:
        with open_url(req, timeout=APP_TIMEOUT_S) as resp:
            raw = resp.read(MAX_APP_RESPONSE_B + 1)
        if len(raw) > MAX_APP_RESPONSE_B:
            raise ValueError("app_response_too_large")
        data = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # The app answers an honest NO_DATA with a non-2xx status (measured: 503 + {"causa":"no_matches"}):
        # read its cause when the body says one; otherwise it is a rejection.
        elapsed = _ms(t0, clock())
        try:
            said = json.loads(exc.read(MAX_APP_RESPONSE_B).decode("utf-8"))
            said = said.get("respuesta", said) if isinstance(said, dict) else {}
            causa = said.get("causa") if isinstance(said, dict) else None
        except (ValueError, UnicodeError, OSError, AttributeError):
            causa = None
        return dict(out, estado="NO_DATA", causa=causa[:64] if isinstance(causa, str) and causa else "app_rejected_request",
                    ms_total=elapsed)
    except (urllib.error.URLError, TimeoutError, OSError):
        return dict(out, estado="NO_DATA", causa="app_unavailable", ms_total=_ms(t0, clock()))
    except (ValueError, UnicodeError):
        return dict(out, estado="NO_DATA", causa="app_invalid_response", ms_total=_ms(t0, clock()))
    out["ms_total"] = _ms(t0, clock())
    r = data.get("respuesta", data) if isinstance(data, dict) else {}
    fuentes = r.get("fuentes") if isinstance(r, dict) else None
    if (isinstance(r, dict) and r.get("estado") == "MEASURED" and r.get("voz") == "hexelion"
            and isinstance(fuentes, list) and fuentes):
        maquina = r.get("maquina") if isinstance(r.get("maquina"), dict) else {}
        out.update(estado="MEASURED", fuentes=len(fuentes), modelo=maquina.get("modelo"))
        if isinstance(maquina.get("ms"), (int, float)):
            out["ms_generacion"] = round(maquina["ms"], 1)
        return out
    causa = r.get("causa") if isinstance(r, dict) and isinstance(r.get("causa"), str) else "app_answer_without_source"
    return dict(out, estado="NO_DATA", causa=causa[:64])


def faro(pregunta, *, endpoint=None, app=None, opener=None, clock=time.monotonic, fecha=None):
    """Both proofs, side by side, under 1,024 UTF-8 bytes. There is deliberately no combined verdict."""
    frame = {"esquema": SCHEMA, "fecha": fecha,
             "voz_directa": voz_directa(endpoint=endpoint, opener=opener, clock=clock),
             "app_con_fuente": app_con_fuente(pregunta, app=app, opener=opener, clock=clock),
             "ley": "direct voice is not the app with a source"}
    raw = json.dumps(frame, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) >= CEILING_B:
        return {"esquema": SCHEMA, "estado": "NO_DATA", "causa": "frame_exceeds_ceiling"}
    return frame
