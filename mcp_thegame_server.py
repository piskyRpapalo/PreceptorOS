import json
import sys

PROTOCOL = "2026-07-28"
LIMIT = 1024
TOOLS = [
    {"name": "leer_estado", "description": "Read the local node snapshot.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "proponer_accion", "description": "Propose a game action without executing it.", "inputSchema": {"type": "object", "properties": {"instantanea": {"type": "object"}}, "required": ["instantanea"], "additionalProperties": False}},
    {"name": "consultar_piloto", "description": "Ask the fixed game pilot for a suggested action.", "inputSchema": {"type": "object", "properties": {"instantanea": {"type": "object"}}, "required": ["instantanea"], "additionalProperties": False}},
    {"name": "leer_canal", "description": "Read an append-only conversation channel.", "inputSchema": {"type": "object", "properties": {"canal": {"type": "string"}, "desde": {"type": "integer", "minimum": 0}}, "required": ["canal"], "additionalProperties": False}},
    {"name": "escribir_canal", "description": "Append an agent message to a conversation channel.", "inputSchema": {"type": "object", "properties": {"canal": {"type": "string"}, "voz": {"type": "string"}, "texto": {"type": "string"}}, "required": ["canal", "voz", "texto"], "additionalProperties": False}},
    {"name": "verificar_cuenta", "description": "Verify an agent account record.", "inputSchema": {"type": "object", "properties": {"cuenta": {"type": "object"}}, "required": ["cuenta"], "additionalProperties": False}},
    {"name": "consultar_politica", "description": "Read the local node policy.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
]


def _bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _error(code, message):
    return {"code": code, "message": message}


def _call(name, args):
    if not isinstance(args, dict):
        raise ValueError("arguments must be an object")
    if name == "leer_estado":
        import casa
        import consola
        result = consola.instantanea(casa.raiz())
    elif name in ("proponer_accion", "consultar_piloto"):
        import aiact_art14_node_decide as pilot
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
        import cuenta_cangrejo
        result = cuenta_cangrejo.verificar_cuenta(args.get("cuenta"), [])
    elif name == "consultar_politica":
        from pathlib import Path
        path = Path(__file__).parent / "politica_nodo.json"
        if not path.is_file():
            result = {"estado": "NO_DATA", "causa": "node policy file has not been added yet"}
        else:
            result = json.loads(path.read_text(encoding="utf-8"))
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
        try:
            result = _call(name, params.get("arguments", {}))
            return {"jsonrpc": "2.0", "id": request_id, "result": result}, initialized
        except (ValueError, TypeError):
            return {"jsonrpc": "2.0", "id": request_id, "error": _error(-32602, "invalid tool arguments")}, initialized
        except Exception as exc:
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": _bytes({"estado": "NO_DATA", "causa": type(exc).__name__}).decode()}], "isError": True}}, initialized
    return {"jsonrpc": "2.0", "id": request_id, "error": _error(-32601, "method not found")}, initialized


def main():
    initialized = False
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response, initialized = handle(request, initialized)
        except (ValueError, TypeError):
            response = {"jsonrpc": "2.0", "id": None, "error": _error(-32700, "parse error")}
        if response is not None:
            sys.stdout.write(_bytes(response).decode("utf-8") + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
