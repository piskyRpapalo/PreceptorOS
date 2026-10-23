import json
import sys

PROTOCOL = "2026-07-28"
LIMIT = 1024
TOOLS = [
    {"name": "leer_estado", "inputSchema": {"type": "object"}},
    {"name": "proponer_accion", "inputSchema": {"type": "object", "properties": {"instantanea": {"type": "object"}}, "required": ["instantanea"]}},
    {"name": "consultar_piloto", "inputSchema": {"type": "object", "properties": {"instantanea": {"type": "object"}}, "required": ["instantanea"]}},
    {"name": "leer_canal", "inputSchema": {"type": "object", "properties": {"canal": {"type": "string"}, "desde": {"type": "integer"}}, "required": ["canal"]}},
    {"name": "escribir_canal", "inputSchema": {"type": "object", "properties": {"canal": {"type": "string"}, "voz": {"type": "string"}, "texto": {"type": "string"}}, "required": ["canal", "voz", "texto"]}},
    {"name": "verificar_cuenta", "inputSchema": {"type": "object", "properties": {"cuenta": {"type": "object"}}, "required": ["cuenta"]}},
    {"name": "consultar_politica", "inputSchema": {"type": "object"}},
]
POLICY_CONDITIONS = {"registro_deudas", "freno_hidraulico", "fork_politico", "colateral_entrada", "cooperacion_obligatoria", "sandbox_wasmtime"}


def _bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _error(code, message):
    return {"code": code, "message": message}


def _read_policy():
    from pathlib import Path
    path = Path(__file__).parent / "politica_nodo.json"
    try:
        raw = path.read_bytes()
    except OSError:
        return None, "node policy is unavailable"
    if len(raw) >= LIMIT:
        return None, "node policy reaches the 1024-byte ceiling"
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None, "node policy is invalid JSON"
    if (not isinstance(value, dict) or set(value) != {"esquema", "version", "nodo", "no_data", "condiciones"}
            or value.get("esquema") != "preceptoros.politica-nodo/1" or set(value.get("condiciones", {})) != POLICY_CONDITIONS
            or any(not isinstance(condition, dict) for condition in value["condiciones"].values())):
        return None, "node policy does not match its closed six-condition contract"
    return value, None


def _call(name, args):
    if not isinstance(args, dict):
        raise ValueError("arguments must be an object")
    if name == "leer_estado":
        import casa
        import consola
        result = consola.instantanea(casa.raiz())
    elif name in ("proponer_accion", "consultar_piloto"):
        import aiact_art14_node_decide as pilot
        if name == "proponer_accion":
            policy, cause = _read_policy()
            if policy is None:
                return {"content": [{"type": "text", "text": _bytes({"estado": "NO_DATA", "causa": cause}).decode()}], "isError": False}
        result = pilot.decide(args.get("instantanea"))
        if name == "proponer_accion" and result.get("estado") == "OK":
            result = {"estado": "PROPUESTA", "accion": result["accion"], "firma": None}
    elif name == "leer_canal":
        import canales
        result = canales.lee(args.get("canal"), desde=args.get("desde", 0))
    elif name == "escribir_canal":
        import canales
        result = canales.di(args.get("canal"), args.get("voz"), args.get("texto"), sello="PROPUESTA", rol="agente")
    elif name == "verificar_cuenta":
        import casa
        import cuenta_cangrejo
        result = cuenta_cangrejo.verificar_cuenta(args.get("cuenta"), casa.raiz() / "allowed_signers_accounts")
    elif name == "consultar_politica":
        result, cause = _read_policy()
        if result is None:
            result = {"estado": "NO_DATA", "causa": cause}
    else:
        raise LookupError("unknown tool")
    if len(_bytes(result)) >= LIMIT:
        result = {"estado": "NO_DATA", "causa": "tool result reaches the 1024-byte channel ceiling"}
    return {"content": [{"type": "text", "text": _bytes(result).decode("utf-8")}], "isError": False}


def handle(message, initialized=False):
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return None, initialized
    method = message.get("method")
    request_id = message.get("id")
    if method == "notifications/initialized":
        return None, True
    if request_id is None:
        return None, initialized
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}}, "serverInfo": {"name": "preceptoros-thegame", "version": "1.0.0"}}}, True
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}, initialized
    if not initialized:
        return {"jsonrpc": "2.0", "id": request_id, "error": _error(-32002, "initialize is required")}, initialized
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}, initialized
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name") if isinstance(params, dict) else None
        if name not in {tool["name"] for tool in TOOLS}:
            return {"jsonrpc": "2.0", "id": request_id, "error": _error(-32602, "unknown tool")}, initialized
        required = {"proponer_accion": {"instantanea"}, "consultar_piloto": {"instantanea"},
                    "leer_canal": {"canal"}, "escribir_canal": {"canal", "voz", "texto"},
                    "verificar_cuenta": {"cuenta"}}
        allowed = {"leer_estado": set(), "consultar_politica": set(),
                   "proponer_accion": {"instantanea"}, "consultar_piloto": {"instantanea"},
                   "leer_canal": {"canal", "desde"}, "escribir_canal": {"canal", "voz", "texto"},
                   "verificar_cuenta": {"cuenta"}}
        arguments = params.get("arguments", {}) if isinstance(params, dict) else None
        if not isinstance(arguments, dict) or not required.get(name, set()).issubset(arguments) or set(arguments) - allowed[name]:
            return {"jsonrpc": "2.0", "id": request_id, "error": _error(-32602, "invalid tool arguments")}, initialized
        try:
            result = _call(name, arguments)
            return {"jsonrpc": "2.0", "id": request_id, "result": result}, initialized
        except (ValueError, TypeError):
            return {"jsonrpc": "2.0", "id": request_id, "error": _error(-32602, "invalid tool arguments")}, initialized
        except Exception as exc:
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": _bytes({"estado": "NO_DATA", "causa": type(exc).__name__}).decode()}], "isError": True}}, initialized
    return {"jsonrpc": "2.0", "id": request_id, "error": _error(-32601, "method not found")}, initialized


def main():
    from mcp_transport import serve
    return serve(sys.stdin.buffer, sys.stdout.buffer, handle)


if __name__ == "__main__":
    raise SystemExit(main())
