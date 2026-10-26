# LF-6 · MCP client and Bubble frame transport receipt

Base: APP `a89022b60d717e7d193c53aeae0d823a0c8a3808` (LF-5 merged).
The declared client is `mcp-client-receipt.json`; run it with
`python3 tools/mcp_stdio_receipt.py`. It launches only the named local
`mcp_thegame_server.py` over stdio. It does not scan for servers, call a
mutating tool, read rack state or open a listener.

## Measured exchange

The helper performs `initialize`, `notifications/initialized`, `ping`, and
`tools/list`, then sends a Bubble-frame probe to the undeclared tool
`bubble_frame.validate`. It checks the protocol, response IDs, unique tool
names, UTF-8 serialization, LF delimiter, and the full 1,024-byte line ceiling.
The fixture digest is pinned in the config.

Measured local run: process exit 0; protocol `2026-07-28`; 7 tools; inventory
SHA-256 `6cd1a24ecebeb2ed593d54f45810855d7498d3e5760eb8cb4e657a7dc3ace134`.
Largest normal request 163 B, largest reply 881 B; all sizes include the JSON-RPC
envelope and LF. The pinned Bubble frame is 197 B, and its complete base64
`tools/call` probe is 378 B. The server rejects that probe with JSON-RPC
`-32602` because the tool is absent. The digest and sizes are a process/wire
receipt, not evidence of a browser or external model client.

The directed boundary case also builds a 697-byte Bubble frame whose complete
base64 JSON-RPC request is 1,046 B. The frame itself is below 1,024 B, but its
envelope is not; the client must reject it before writing. No implicit
truncation or artifact transport is defined.

## Scope and NO_DATA

The six focused tests cover the actual configured handshake, UTF-8 byte
counting, a sub-limit frame with an over-limit envelope, missing server
configuration, oversized reply rejection and response-ID mismatch. The test
joins `bin/pruebas` in this change.

This measures one short-lived APP stdio process. External model-client
attachment, a resident service, browser-to-MCP transport, and transfer of a
Bubble frame to a validator remain `NO_DATA`: the APP server has no declared
frame tool, as shown by the rejected probe. The separate `<private-repo>` server and its
web inspection tools are not conflated with this APP process.

Run `python3 -m unittest -v test_mcp_stdio_receipt` for the focused judge and
`python3 tools/mcp_stdio_receipt.py` for the live process receipt. The complete
APP runner is still required in CI/rack; a socket-restricted local run is not
reported as green.
