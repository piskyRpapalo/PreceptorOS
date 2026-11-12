"""One conversation, many preceptors · the router over the shared thread (APP-ROUTER-01).

The rack already has ONE conversation: the `orquesta` thread of `canales.py` (the `eventos.db` register). The person
writes there through the app, Hexelion answers there, and the rack CLI agents (Claude, Codex, ...) write there by
loopback in their own voice. What was missing is the router's other half: the app never showed that thread, and a
person could not address a message to one preceptor. This module is that half, pure: no network, no clock of its own.

  destinations(lectura, now) -> who can be addressed, by what transport, and when each one last spoke here
  project(lectura, now)      -> the last messages, each with an explicit identity (who, which kind, to whom)
  check_send(data)           -> the person's addressed message, validated, or a cause

Identity kinds: person (the Sovereign's voice, only through the app door), private (Hexelion, local station),
rack-cli (agents on this rack that read the thread in their own session), sensor (local tools, not a model),
external (agents outside the rack: no transport on this node, so NO_DATA) and unknown (a voice not in this table).
A message is data, never authority: addressing someone does not give them permission to act.
"""
from __future__ import annotations

import datetime as dt

SCHEMA = "preceptoros.multipreceptor/1"
THREAD = "orquesta"
MAX_TEXT = 600            # what the person may send (the chat door has the same ceiling)
MAX_SHOWN = 1200          # what one projected message may show
MAX_MESSAGES = 40

# The table of preceptors. Order is the order the app shows. `route`: station (Hexelion's door), thread (the message
# is delivered to the shared thread; the recipient reads it on its own turn), none (not addressable from here).
DESTINATIONS = (
    {"id": "hexelion", "name": "Hexelion", "kind": "private", "route": "station",
     "transport": "loopback station: a local model answers with verified quotes, or NO_DATA"},
    {"id": "claude", "name": "Claude", "kind": "rack-cli", "route": "thread",
     "transport": "shared thread: Claude Code on this rack reads it in its session and answers in its own voice"},
    {"id": "codex", "name": "Codex", "kind": "rack-cli", "route": "thread",
     "transport": "shared thread: Codex CLI on this rack reads it in its session and answers in its own voice"},
    {"id": "gemini", "name": "Gemini", "kind": "rack-cli", "route": "thread",
     "transport": "shared thread: a Gemini CLI on this rack reads it in its session and answers in its own voice"},
    {"id": "mistral", "name": "Mistral", "kind": "rack-cli", "route": "thread",
     "transport": "shared thread: a Mistral CLI on this rack reads it in its session and answers in its own voice"},
    {"id": "chatgpt", "name": "ChatGPT", "kind": "external", "route": "none",
     "transport": "NO_DATA: no authorized connector on this node; the Mesa issue is the place to reach it"},
    {"id": "mistral-web", "name": "Mistral Web", "kind": "external", "route": "none",
     "transport": "NO_DATA: no authorized connector on this node; the Mesa issue is the place to reach it"},
    {"id": "codex-web", "name": "Codex Web", "kind": "external", "route": "none",
     "transport": "NO_DATA: no authorized connector on this node; the Mesa issue is the place to reach it"},
)
BY_ID = {d["id"]: d for d in DESTINATIONS}
# Voices that speak in the thread but are not addressed: the person, and local tools that are not a model.
SPEAKERS = {"soberano": ("You", "person"), "orquestador": ("Local sensor", "sensor")}


def _age_seconds(stamp, now):
    try:
        then = dt.datetime.strptime(str(stamp), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError):
        return None
    gap = int((now - then).total_seconds())
    return gap if gap >= 0 else None


def identity(voice):
    """voice -> {from, name, kind}. A voice outside the table is shown as unknown, never as someone else."""
    if voice in SPEAKERS:
        name, kind = SPEAKERS[voice]
    elif voice in BY_ID:
        name, kind = BY_ID[voice]["name"], BY_ID[voice]["kind"]
    else:
        name, kind = str(voice or "")[:24] or "NO_DATA", "unknown"
    return {"from": str(voice or ""), "name": name, "kind": kind}


def _source(f):
    """One citation as a short line: memory id, date and the first 12 hex of its fingerprint, or NO_DATA."""
    if not isinstance(f, dict):
        return "NO_DATA: citation unreadable"
    sha = str(f.get("sha256") or "")
    return "#%s · %s · %s" % (f.get("id", "NO_DATA"), str(f.get("updated_at") or "NO_DATA")[:20],
                              sha[:12] if len(sha) == 64 else "NO_DATA")


def _messages(lectura):
    if not isinstance(lectura, dict) or lectura.get("estado") != "MEDIDO":
        return None
    return [m for m in lectura.get("mensajes") or [] if isinstance(m, dict)]


def destinations(lectura, now):
    """Every preceptor in the table, with when it last spoke in the thread (or NO_DATA with its cause)."""
    msgs = _messages(lectura)
    last = {}
    for m in msgs or []:
        last[m.get("voz")] = m.get("t")
    out = []
    for d in DESTINATIONS:
        row = {"id": d["id"], "name": d["name"], "kind": d["kind"], "addressable": d["route"] != "none",
               "route": d["route"], "transport": d["transport"]}
        if msgs is None:
            row["last_spoke"] = "NO_DATA: the thread could not be read"
        elif d["id"] in last:
            row["last_spoke"] = last[d["id"]]
            row["age_s"] = _age_seconds(last[d["id"]], now)
        else:
            row["last_spoke"] = "NO_DATA: never spoke in this thread"
        out.append(row)
    return out


def project(lectura, now, since=0, limit=MAX_MESSAGES):
    """The thread as the app shows it: newest `limit` messages after `since`, each with who, kind and recipient."""
    msgs = _messages(lectura)
    base = {"schema": SCHEMA, "thread": THREAD, "observed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "authority": "none: a message grants no permission and is not a signature"}
    if msgs is None:
        cause = lectura.get("causa") if isinstance(lectura, dict) else None
        return dict(base, state="NO_DATA", cause=str(cause or "thread_unreadable"), last=0, messages=[],
                    destinations=destinations(lectura, now))
    rows = []
    for m in msgs:
        n = m.get("n")
        if not isinstance(n, int) or n <= since:
            continue
        text = str(m.get("texto") or "")
        machine = m.get("maquina") if isinstance(m.get("maquina"), dict) else {}
        row = dict(identity(m.get("voz")), n=n, t=str(m.get("t") or ""), seal=str(m.get("sello") or "NO_DATA"),
                   text=text[:MAX_SHOWN], cut=len(text) > MAX_SHOWN)
        to = machine.get("para")
        if isinstance(to, str) and to in BY_ID:
            row["to"] = to
        if isinstance(machine.get("modelo"), str):
            row["model"] = machine["modelo"][:60]
        if isinstance(machine.get("fuentes"), list):
            row["sources"] = [_source(f) for f in machine["fuentes"][:5]]
        rows.append(row)
    last = max([m.get("n") for m in msgs if isinstance(m.get("n"), int)] or [0])
    return dict(base, state="MEASURED", last=last, messages=rows[-limit:], hidden=max(0, len(rows) - limit),
                destinations=destinations(lectura, now))


def check_send(data):
    """The person's addressed message: {para, texto} exactly. -> (para, texto, None) or (None, None, cause)."""
    if type(data) is not dict or set(data) != {"para", "texto"}:
        return None, None, "request_invalid"
    para, texto = data["para"], data["texto"]
    if type(para) is not str or para not in BY_ID:
        return None, None, "recipient_unknown"
    if BY_ID[para]["route"] == "none":
        return None, None, "no_transport"
    if BY_ID[para]["route"] == "station":
        return None, None, "use_station_door"     # Hexelion is asked through /api/hexelion/chat
    if type(texto) is not str or not texto.strip() or len(texto) > MAX_TEXT:
        return None, None, "text_invalid"
    return para, texto.strip(), None
