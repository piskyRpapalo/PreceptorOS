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
}
AYUDA = "/estado · /capacidades · /registro [n] · /ejecuta [@worktree] <command> · /escribe @worktree <path> :: <text>"


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
    if tool in ("state", "capabilities"):
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


def ejecuta(texto, server=None):
    """Parse, call, summarise. Returns the receipt the chat door sends and writes."""
    tool, args = interpreta(texto)
    if tool is None:
        return {"estado": "NO_DATA", "causa": args, "ayuda": AYUDA}
    r = llama(tool, args, server)
    if r["estado"] != "MEASURED":
        return {"estado": "NO_DATA", "causa": r["causa"], "herramienta": tool}
    res = r["resultado"]
    ok = bool(res.get("ok")) and not res.get("denied")
    return {"estado": "MEASURED", "herramienta": tool, "ok": ok, "denegada": bool(res.get("denied")),
            "causa": res.get("causa") if res.get("denied") else None, "rc": res.get("rc"), "ms": r["ms"],
            "allowlist_version": res.get("allowlist_version"), "texto": resumen(tool, res)}
