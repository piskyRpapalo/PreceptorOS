"""Hexelion acts from the chat: a message that starts with «/» is an ACTION, not a question.

Policy (the Sovereign, 2026-11-12): «hexelion debe poder leer y escribir, igual que los preceptores · no debe pedirme
firmas, solo ejecutar y proponer». The model is never asked to choose a tool: the person types the action, this module
parses it with a small exact grammar, and runs it through the native MCP server (p0x bin/mcp_preceptoros_nativo.py,
S-3) as voice «hexelion». The fences live in that server, not here: worktrees ~/wt/hexelion-*, branches hexelion/*,
draft HITL PRs, and the hard lines (no merge, no push to main, no force, no signing). Each call leaves its receipt in
the server's audit; the result goes to the thread as Hexelion's turn, marked «not model».

Grammar (es/en):
  /estado | /state                              host + house services
  /capacidades | /capabilities                  what Hexelion may do, and why
  /registro [n] | /audit [n]                    last n receipts (1..20)
  /firmas | /signatures                         what awaits the Sovereign's signature (local read, no MCP)
  /lab                                          the Lab bench results the Notebook shows (local read, no MCP)
  /preceptores | /preceptors                    declared preceptor heartbeats + who acted (local read, no MCP)
  /ejecuta [@worktree] <command> | /run ...     one command, inside ~/wt/<worktree> when named
  /escribe @worktree <path> :: <text> | /write  one text file inside that worktree
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

VOZ = "hexelion"
TIMEOUT = 300
TOPE_TEXTO = 1600
_WT = re.compile(r"^@([a-z0-9][a-z0-9._-]{0,60})$")
_REL = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[\w.\-/]{1,160}$")
ACCIONES = {
    "estado": "state", "state": "state",
    "capacidades": "capabilities", "capabilities": "capabilities",
    "registro": "audit_last", "audit": "audit_last",
    "ejecuta": "exec", "run": "exec",
    "escribe": "write_file", "write": "write_file",
    "firmas": "signatures", "signatures": "signatures",
    "lab": "lab",
    "preceptores": "preceptors", "preceptors": "preceptors",
    "dispositivos": "devices", "devices": "devices",
    "modelos": "models", "models": "models",
}
# Local READS (APP-TALK-E2E-01, 2026-11-13): no MCP, no model, no network. Each one reads a projection an existing
# producer already writes under <casa>: the signature list (bin/firmas-scraper), the Lab bench (lab_bench.py) and
# the preceptor heartbeats (notebook/agents.json), through the same readers the Notebook and /api/firmas use.
LOCALES = ("signatures", "lab", "preceptors", "devices", "models")
FIRMAS_FRESCAS_S = 1800   # the scraper runs every 10 min; older than 30 min is said as STALE
# The chat door answers inside a 1,023 B envelope (estado_compacto); the action fields take ~350 B of it. A local
# read says the most important lines first and is cut, with a mark, at this many UTF-8 bytes.
TOPE_LOCAL_B = 560
AYUDA = ("/estado · /capacidades · /registro [n] · /firmas · /lab · /preceptores · /dispositivos · /modelos · "
         "/ejecuta [@worktree] <command> · "
         "/escribe @worktree <path> :: <text>")


# One sentence, no typing (NORTE §4: «si el Soberano es ciego, NO tiene que teclear»). Exact phrases only, and only
# READ actions: a phrase never writes, runs a command or picks a tool by model. Anything else stays a question.
FRASES = {
    "/estado": (
        "estado del rack", "como esta el rack", "como va el rack", "estado de la casa", "como esta la casa",
        "que servicios fallan", "que esta caido", "hay algo caido", "estado de los servicios",
        "rack state", "rack status", "how is the rack", "what is down", "is anything down", "house status",
        "estado do rack", "como esta o rack", "o que esta em baixo",
    ),
    "/capacidades": (
        "que puedes hacer", "que puede hacer hexelion", "tus capacidades", "que te esta permitido",
        "what can you do", "your capabilities", "what are you allowed to do",
        "o que podes fazer", "o que voce pode fazer",
    ),
    "/registro 5": (
        "que has hecho", "ultimas acciones", "tus ultimas acciones", "registro de acciones", "que hiciste",
        "what did you do", "last actions", "recent actions", "your last actions",
        "o que fizeste", "ultimas acoes",
    ),
    "/firmas": (
        "que espera mi firma", "que espera de mi firma", "que tengo que firmar", "que falta por firmar",
        "firmas pendientes", "que hay que firmar",
        "what awaits my signature", "what needs my signature", "what do i have to sign", "pending signatures",
        "o que espera a minha assinatura", "o que tenho de assinar", "assinaturas pendentes",
    ),
    "/lab": (
        "que resultados tenemos del laboratorio", "resultados del laboratorio", "resultados del lab",
        "que dice el laboratorio", "que dice el lab",
        "lab results", "what are the lab results", "what does the lab say", "laboratory results",
        "resultados do laboratorio", "o que diz o laboratorio",
    ),
    "/preceptores": (
        "que preceptores estan trabajando", "que preceptores trabajan", "quien esta trabajando", "quien trabaja",
        "which preceptors are working", "who is working", "what are the preceptors doing",
        "que preceptores estao a trabalhar", "quem esta a trabalhar",
    ),
    "/dispositivos": (
        "que dispositivos estan conectados", "que dispositivos hay", "que dispositivos tenemos", "que nodos hay",
        "que dispositivos estan reservados para acurast",
        "what devices are connected", "which devices are connected", "what devices do we have", "which nodes are there",
        "que dispositivos estao ligados", "que dispositivos temos",
    ),
    "/modelos": (
        "que modelos tenemos", "que modelos hay", "modelos disponibles",
        "what models do we have", "which models do we have", "what models are there",
        "que modelos temos",
    ),
}
_FRASE = {f: orden for orden, frases in FRASES.items() for f in frases}


def normaliza(texto):
    norm = unicodedata.normalize("NFKD", texto.casefold())
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    norm = norm.strip().strip("¿?¡! .,")
    return re.sub(r"\s+", " ", norm)


def frase(texto):
    """The read action an exact phrase names, or None (then it is an ordinary question)."""
    if not isinstance(texto, str) or not 0 < len(texto) <= 120:
        return None
    return _FRASE.get(normaliza(texto))


def es_accion(texto):
    return isinstance(texto, str) and texto.lstrip().startswith("/")


def servidor():
    return Path(os.environ.get("PRECEPTOROS_MCP_NATIVO") or Path.home() / "bin" / "mcp_preceptoros_nativo.py")


def raiz_wt():
    return Path(os.environ.get("PRECEPTOROS_WT_RAIZ") or Path.home() / "wt")


def interpreta(texto):
    """(tool, arguments) or (None, cause). Exact grammar; anything else is refused with its cause."""
    if not es_accion(texto) or len(texto) > 600:
        return None, "action_invalid"
    cuerpo = texto.strip()[1:]
    verbo, _, resto = cuerpo.partition(" ")
    tool = ACCIONES.get(verbo.casefold())
    resto = resto.strip()
    if tool is None:
        return None, "action_unknown"
    if tool in ("state", "capabilities") + LOCALES:
        return (tool, {}) if not resto else (None, "action_takes_no_arguments")
    if tool == "audit_last":
        if not resto:
            return tool, {"n": 5}
        return (tool, {"n": int(resto)}) if resto.isdigit() and 1 <= int(resto) <= 20 else (None, "audit_count_1_to_20")
    cwd = None
    if resto.startswith("@"):
        etiqueta, _, resto = resto.partition(" ")
        m = _WT.match(etiqueta)
        if not m:
            return None, "worktree_name_invalid"
        cwd = raiz_wt() / m.group(1)
        resto = resto.strip()
    if tool == "exec":
        if not resto:
            return None, "command_missing"
        return tool, ({"command": resto, "cwd": str(cwd)} if cwd else {"command": resto})
    # write_file
    if cwd is None:
        return None, "write_needs_worktree"
    ruta, sep, contenido = resto.partition(" :: ")
    if not sep or not _REL.match(ruta.strip()):
        return None, "write_path_or_separator_invalid"
    return tool, {"path": str(cwd / ruta.strip()), "content": contenido + ("" if contenido.endswith("\n") else "\n")}


def llama(tool, args, server=None, timeout=TIMEOUT):
    """One stdio JSON-RPC session with the native server as voice hexelion. Never raises."""
    server = Path(server or servidor())
    if not server.is_file():
        return {"estado": "NO_DATA", "causa": "mcp_nativo_missing"}
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": tool, "arguments": args}}]
    env = dict(os.environ, PRECEPTOROS_MCP_VOZ=VOZ)
    t0 = time.monotonic()
    try:
        proc = subprocess.run([sys.executable, "-I", str(server)], input="".join(json.dumps(m) + "\n" for m in msgs),
                              capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {"estado": "NO_DATA", "causa": "mcp_nativo_timeout"}
    except OSError:
        return {"estado": "NO_DATA", "causa": "mcp_nativo_unrunnable"}
    ms = int((time.monotonic() - t0) * 1000)
    replies = {}
    for line in proc.stdout.splitlines():
        try:
            d = json.loads(line)
            replies[d.get("id")] = d
        except (ValueError, AttributeError):
            continue
    names = [t.get("name") for t in ((replies.get(2) or {}).get("result") or {}).get("tools", [])]
    if "capabilities" not in names or tool not in names:
        return {"estado": "NO_DATA", "causa": "mcp_s3_not_installed"}
    call = replies.get(3) or {}
    try:
        result = json.loads(call["result"]["content"][0]["text"])
    except (KeyError, IndexError, TypeError, ValueError):
        return {"estado": "NO_DATA", "causa": "mcp_reply_invalid"}
    if not isinstance(result, dict):
        return {"estado": "NO_DATA", "causa": "mcp_reply_invalid"}
    return {"estado": "MEASURED", "ms": ms, "resultado": result}


def _recorta(s):
    s = s if isinstance(s, str) else ""
    return s if len(s) <= TOPE_TEXTO else "…" + s[-(TOPE_TEXTO - 1):]


def resumen(tool, result):
    """A short plain-text line for the thread and the chat bubble."""
    if result.get("denied"):
        return "Refused by the fence: %s." % (result.get("causa") or "no cause")
    if tool == "state":
        units = result.get("servicios") or []
        if isinstance(units, list):
            activos = sum(1 for u in units if isinstance(u, dict) and u.get("activo") == "active")
            caidos = [u.get("unidad") for u in units if isinstance(u, dict) and u.get("activo") == "failed"]
            svc = "%d/%d house services active" % (activos, len(units)) + ("; failed: " + ", ".join(caidos[:5]) if caidos else "")
        else:
            svc = "services: NO_DATA"
        mem = (result.get("memoria") or ["NO_DATA"])[0]
        disk = (result.get("disco_casa") or ["NO_DATA"])[0]
        models = result.get("modelos_cargados") or []
        return _recorta("Rack state: %s. Memory: %s. Home disk used/free: %s. Models loaded: %d. Uptime: %s."
                        % (svc, " ".join(str(mem).split()), " ".join(str(disk).split()), len(models),
                           str(result.get("uptime", "NO_DATA")).strip()))
    if tool == "capabilities":
        w = result.get("escritura")
        if not w:
            return "I can only read here (no preceptor voice)."
        return _recorta("I can read the rack, and write only in %s on branches %s: %s. I never: %s."
                        % (w.get("donde"), w.get("ramas"), w.get("regla"),
                           ", ".join((result.get("lineas_duras") or {}).get("nunca", []))))
    if tool == "audit_last":
        rows = result.get("recibos") or []
        lines = ["%s %s %s%s" % (r.get("ts", "?"), r.get("voz", "?"), r.get("tool", "?"),
                                 " denied: " + r.get("causa", "") if r.get("denied") else " rc=%s" % r.get("rc"))
                 for r in rows if isinstance(r, dict)]
        return _recorta("Last %d receipts:\n" % len(lines) + "\n".join(lines))
    if tool == "write_file":
        return "Written: %s B, sha256 %s." % (result.get("bytes"), str(result.get("sha256", ""))[:16])
    out = result.get("out") or ""
    return _recorta("rc=%s · %s ms\n%s" % (result.get("rc"), result.get("ms"), out.rstrip()))


def _edad(stamp, now):
    """Seconds since an ISO-8601 UTC stamp, or None."""
    import datetime as dt
    try:
        t = dt.datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        return None if t.tzinfo is None else (now - t).total_seconds()
    except ValueError:
        return None


def _hace(segundos):
    if segundos is None or segundos < 0:
        return "at an unknown time (NO_DATA)"
    return ("%d min ago" % (segundos // 60)) if segundos < 7200 else ("%d h ago" % (segundos // 3600))


def _firmas(base, now):
    """The same file and checks as GET /api/firmas (bin/firmas-scraper writes it). Never signs, never asks to."""
    ruta = Path(base) / "firmas" / "pendientes.json"
    try:
        if ruta.stat().st_size > 65536:
            return False, "signatures_unreadable", "I cannot read the signature list (too large)."
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        if not isinstance(datos, dict) or datos.get("esquema") != "preceptoros.firmas-pendientes/1":
            raise ValueError()
        filas = [f for f in datos.get("filas") or [] if isinstance(f, dict)]
    except FileNotFoundError:
        return False, "scraper_not_run", "I cannot say what awaits your signature: the signature list was never written."
    except (OSError, ValueError, AttributeError):
        return False, "signatures_unreadable", "I cannot read the signature list."
    edad = _edad(datos.get("medido"), now)
    firmar = [f for f in filas if f.get("action") in ("sign", "merge", "retarget")]
    otras = {}
    for f in filas:
        if f not in firmar:
            otras[f.get("action") or "no_data"] = otras.get(f.get("action") or "no_data", 0) + 1
    nombres = {"running": "with checks still running", "red": "with red checks", "wait_base": "waiting for their base",
               "no_data": "without check data"}
    if firmar:
        linea = "Waiting for your signature: %d — %s." % (len(firmar), "; ".join(
            "%s#%s «%s» (checks %s)" % (str(f.get("repo", "?")).split("/")[-1], f.get("n", "?"),
                                        " ".join(str(f.get("title", "")).split())[:70], f.get("checks", "NO_DATA"))
            for f in firmar[:3])) + (" (+%d more)" % (len(firmar) - 3) if len(firmar) > 3 else "")
    else:
        linea = "Nothing waits for your signature now."
    if otras:
        linea += " Not ready yet: " + ", ".join("%d %s" % (k, nombres.get(a, a)) for a, k in sorted(otras.items())) + "."
    linea += " Signature list measured %s. I never sign for you." % _hace(edad)
    if edad is None or edad < 0 or edad > FIRMAS_FRESCAS_S:
        return False, "signatures_stale", "STALE: " + linea
    return True, None, linea


def _lab(base, now):
    """Lab benchmark runs as the Notebook shows them (lab_bench.py projection, rechecked by notebook_read)."""
    import notebook_read
    vista = notebook_read.read(base, now)
    runs = vista.get("bench") or []
    if not runs:
        return False, vista.get("bench_cause") or "no_valid_bench_receipt", \
            "No Lab result I can show: %s." % (vista.get("bench_cause") or "no_valid_bench_receipt").replace("_", " ")
    partes = []
    for r in runs[-1:]:                 # the latest run; the Notebook keeps the others
        cheq = "fingerprint %s" % str(r.get("fingerprint", "NO_DATA")).lower()
        partes.append("%s %s: %s (%s)" % (str(r.get("date", ""))[:10], r.get("experiment", "?"), r["sentence"], cheq))
    return True, None, "Lab, %d run%s; latest: %s Lab projection written %s." % (
        len(runs), "" if len(runs) == 1 else "s", " ".join(partes), _hace(_edad(vista.get("bench_observed_at"), now)))


def _preceptores(base, now):
    """Who works = a declared heartbeat (notebook/agents.json). Receipts say who ACTED, never who is alive."""
    import notebook_read
    vista = notebook_read.read(base, now)
    agentes = vista.get("agents") or []
    recientes = {}
    for r in vista.get("receipts") or []:
        if r.get("voice") and r.get("status") in ("DECLARED", "VERIFIED"):
            recientes[r["voice"]] = recientes.get(r["voice"], 0) + 1
    actos = (" Actions with a receipt in the last 10 min: %s." % ", ".join(
        "%s %d" % (v, n) for v, n in sorted(recientes.items()))) if recientes else \
        " No action receipt in the last 10 min."
    if vista.get("agents_status") != "DECLARADO":
        causa = vista.get("agents_cause") or "agents_no_data"
        return False, "agents_" + causa, ("I cannot say which preceptors are working: no preceptor heartbeat is "
                                          "published (%s). I do not guess from installed tools." % causa.replace("_", " ")
                                          ) + actos
    estados = {"OBSERVADO": "heartbeat in the last 10 min", "STALE": "no heartbeat for over 10 min"}
    linea = "Preceptors (declared heartbeats): " + "; ".join(
        "%s (%s): %s" % (a["name"], a["role"], estados.get(a["status"], "NO_DATA " + str(a["cause"])))
        for a in agentes) + "."
    return True, None, linea + actos


def _federado(base, now):
    import federado
    return federado.from_lab(base, now=now)


def _dispositivos(base, now):
    """The declared devices and the evidence each has. LAB measures; the APP only reads and says. The full machine
    form is GET /api/federado (the chat answer must fit its envelope)."""
    vista = _federado(base, now)
    if vista.get("registry_cause"):
        return False, vista["registry_cause"], ("I cannot list your devices: the private device registry is "
                                                 "not readable (%s)." % vista["registry_cause"].replace("_", " "))
    rack, otros, acurast = [], [], []
    for d in vista["devices"]:
        if d["acurast"] or "ACURAST_EXTERNAL" in d["roles"]:
            acurast.append(d["label"] + (" (parked)" if d["parked"] else ""))
            continue
        server = next((e for e in d["evidence"] if e["role"] == "MODEL_SERVER" and d["kind"] == "rack_node"), None)
        if server is None:
            otros.append(d["label"] + (" (parked)" if d["parked"] else ""))
        elif server["state"] == "STALE":
            rack.append("%s seen %s" % (d["label"], _hace(server.get("age_s"))))
        elif server["state"] == "VERIFIED":
            rack.append("%s verified now" % d["label"])
        else:
            rack.append("%s no evidence (%s)" % (d["label"], server["cause"].replace("_", " ")))
    texto = "Devices: %d declared." % len(vista["devices"])
    if rack:
        texto += " Model servers (LAB): " + "; ".join(rack) + "."
    if otros:
        texto += " Declared only, not pinged: " + ", ".join(otros) + "."
    if acurast:
        texto += " Reserved to Acurast, never Hexelion workers: " + ", ".join(acurast) + "."
    if vista.get("lab_cause"):
        texto += " LAB evidence: NO_DATA (%s)." % vista["lab_cause"].replace("_", " ")
    return True, None, texto


def _modelos(base, now):
    """Installed models per node backend, from LAB's re-checked snapshots. Installed is not available."""
    vista = _federado(base, now)
    if vista.get("lab_cause"):
        return False, vista["lab_cause"], ("I cannot say which models we have: LAB node evidence is NO_DATA (%s)."
                                           % vista["lab_cause"].replace("_", " "))
    filas, edades, sin = [], [], []
    for r in vista["backends"]:
        nombre = r["node"] + ("" if r.get("backend") in (None, "default") else " " + r["backend"])
        if r["state"] == "NO_DATA":
            sin.append("%s (%s)" % (nombre, r["cause"].replace("_", " ")))
            continue
        filas.append("%s %d/%s" % (nombre, r["models_installed"],
                                   "NO_DATA" if r["models_resident"] is None else r["models_resident"]))
        edades.append(r["age_s"] or 0)
    texto = "Models installed/loaded by node (LAB snapshots, integrity rechecked): " + " · ".join(filas)
    if edades:
        texto += (", verified now" if all(r["state"] == "VERIFIED" for r in vista["backends"] if r["state"] != "NO_DATA")
                  else ", seen %s to %s" % (_hace(min(edades)), _hace(max(edades))))
    texto += "." + (" No evidence: " + "; ".join(sin) + "." if sin else "")
    return True, None, texto + " Installed is not available; no inference was run."


_LECTORES = {"signatures": (_firmas, "firmas/pendientes.json"), "lab": (_lab, "notebook/bench.json"),
             "preceptors": (_preceptores, "notebook/agents.json + notebook/receipts.json"),
             "devices": (_dispositivos, "federado/dispositivos.json + LAB node receipts"),
             "models": (_modelos, "LAB node receipts")}


def cabe(texto, tope=TOPE_LOCAL_B):
    """The text, or its first `tope` UTF-8 bytes on a character boundary plus a visible cut mark."""
    marca = " … (cut to fit the chat)"
    if len(texto.encode("utf-8")) <= tope:
        return texto
    corte = texto.encode("utf-8")[:tope - len(marca.encode("utf-8"))].decode("utf-8", "ignore")
    return corte.rstrip() + marca


def lee_local(tool, base=None, now=None):
    """One local read. Never raises, never writes, never calls the model or the network."""
    import datetime as dt
    if base is None:
        import casa
        base = casa.raiz()
    now = now or dt.datetime.now(dt.timezone.utc)
    lector, fuente = _LECTORES[tool]
    t0 = time.monotonic()
    try:
        ok, causa, texto = lector(base, now)
    except Exception:   # a reader bug must still answer with a cause, never a stack trace in the chat
        ok, causa, texto = False, "local_read_failed", "I could not read %s." % fuente
    return {"estado": "MEASURED", "herramienta": tool, "ok": ok, "denegada": False, "causa": causa,
            "rc": 0 if ok else 1, "ms": int((time.monotonic() - t0) * 1000), "allowlist_version": None,
            "via": "lectura_local", "fuente": fuente, "texto": cabe(texto),
            "evidencia": {"fuente": fuente} if ok is True else {}}


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def evidencia(tool, res):
    """The fields this tool's own contract uses to confirm a result, shaped for the thread; {} when absent or ill-typed.

    Measured 2026-11-13 against the native server: exec proves its result with `rc`; write_file has no rc and proves it
    with the bytes written and their SHA-256; state, capabilities and audit_last have no rc and prove a read with the
    field they read. `ok` is never part of the proof. turnos_hexelion judges these; this only carries them.
    """
    if not isinstance(res, dict) or res.get("denied") or res.get("ok") is not True:
        return {}
    if tool == "exec":
        rc = res.get("rc")
        return {"rc": rc} if type(rc) is int else {}
    if tool == "write_file":
        n, sha = res.get("bytes"), res.get("sha256")
        return ({"bytes": n, "sha256": sha} if type(n) is int and n >= 0 and isinstance(sha, str)
                and _SHA256.match(sha) else {})
    if tool == "state":
        units = res.get("servicios")
        return {"servicios": len(units)} if isinstance(units, list) else {}
    if tool == "capabilities":
        v = res.get("allowlist_version")
        return {"allowlist_version": v} if isinstance(v, str) and 0 < len(v) <= 64 else {}
    if tool == "audit_last":
        n, rows = res.get("n"), res.get("recibos")
        return {"n": n} if type(n) is int and isinstance(rows, list) and n == len(rows) else {}
    return {}


def ejecuta(texto, server=None, base=None):
    """Parse, call, summarise. Returns the receipt the chat door sends and writes."""
    tool, args = interpreta(texto)
    if tool is None:
        return {"estado": "NO_DATA", "causa": args, "ayuda": AYUDA}
    if tool in LOCALES:
        return lee_local(tool, base)
    r = llama(tool, args, server)
    if r["estado"] != "MEASURED":
        return {"estado": "NO_DATA", "causa": r["causa"], "herramienta": tool}
    res = r["resultado"]
    ok = bool(res.get("ok")) and not res.get("denied")
    return {"estado": "MEASURED", "herramienta": tool, "ok": ok, "denegada": bool(res.get("denied")),
            "causa": res.get("causa") if res.get("denied") else None, "rc": res.get("rc"), "ms": r["ms"],
            "allowlist_version": res.get("allowlist_version"), "via": "mcp_nativo", "texto": resumen(tool, res),
            "evidencia": evidencia(tool, res) if ok else {}}
