"""Energy observation for the local app and Hexelion; read only, fail closed.

This does not manage a solar battery, allocate jobs, or switch a socket. The
pre-existing meter reader is the only power source; solar and battery state
remain NO_DATA until independently instrumented. No private address enters
the payload, and both machine and spoken views derive from the same object.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math

import metricas as _metricas

SCHEMA = "preceptoros.energy-read/1"


def _cause(raw):
    """Stable public cause codes, never a URL, IP or exception message."""
    if not isinstance(raw, str):
        return "meter_read_invalid"
    if "meter endpoint not configured" in raw:
        return "meter_endpoint_not_configured"
    if "electrical" in raw or "incoheren" in raw.lower():
        return "meter_electrical_incoherent"
    if "StatusSNS.ENERGY.Power" in raw:
        return "meter_schema_incomplete"
    if "no responde" in raw:
        return "meter_unreachable"
    return "meter_read_invalid"


def snapshot(*, reader=None, clock=None):
    """Take one bounded reading. The returned payload contains no actuators."""
    reader = reader or _metricas._consumo_w
    clock = clock or (lambda: datetime.now(timezone.utc))
    try:
        when = clock()
        if not isinstance(when, datetime) or when.tzinfo is None:
            raise ValueError("clock_invalid")
        instant = when.astimezone(timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, OverflowError):
        instant = "NO_DATA"
    try:
        power = reader()
    except Exception:
        power = {"estado": "NO_DATA", "causa": "meter_reader_failed"}
    good = (type(power) is dict and power.get("estado") == "MEDIDO"
            and type(power.get("valor")) in (int, float)
            and math.isfinite(power["valor"]) and power["valor"] >= 0)
    if good:
        consumo = {"estado": "MEDIDO", "valor": round(float(power["valor"]), 2),
                   "unidad": "W", "fuente": "local_plug_status8"}
    else:
        consumo = {"estado": "NO_DATA", "valor": None, "unidad": "W",
                   "causa": _cause(power.get("causa") if isinstance(power, dict) else None)}
    return {
        "esquema": SCHEMA, "medido_utc": instant,
        "estado": "PARCIAL" if good else "NO_DATA",
        "consumo": consumo,
        "bateria": {"estado": "NO_DATA", "causa": "battery_soc_not_instrumented"},
        "solar": {"estado": "NO_DATA", "causa": "solar_generation_not_instrumented"},
        "reparto": {"estado": "NO_DATA", "causa": "solar_cadence_not_operational"},
        "solo_lectura": True,
    }


def decir(ficha):
    """One screen-reader / machine-consistent sentence; no model invention."""
    watts = ficha.get("consumo") if isinstance(ficha, dict) else None
    if not isinstance(watts, dict):
        return "Energy: NO_DATA (snapshot_invalid)."
    if watts.get("estado") == "MEDIDO":
        base = f"Energy: plug reports {watts['valor']} W."
    else:
        base = f"Energy: NO_DATA ({_cause_public(watts.get('causa'))})."
    return (base + " Battery: NO_DATA (battery_soc_not_instrumented)."
            " Solar: NO_DATA (solar_generation_not_instrumented)."
            " Allocation: NO_DATA (solar_cadence_not_operational)."
            " Read only; no load switching.")


def _cause_public(value):
    allowed = {"meter_endpoint_not_configured", "meter_electrical_incoherent",
               "meter_schema_incomplete", "meter_unreachable", "meter_read_invalid"}
    return value if value in allowed else "meter_read_invalid"


def respuesta(*, reader=None, clock=None):
    """Identical source for local agents, the app, and voice renderers."""
    d = snapshot(reader=reader, clock=clock)
    d["texto"] = decir(d)
    return d
