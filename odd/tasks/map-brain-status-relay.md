# Map-brain status relay through the app door

Status: PROPOSAL · fail-closed adapter · no model/runtime health claim.

## Purpose and exact route

The web client and Claude's chat UI can read the status through the existing local-app door:

- `POST http://127.0.0.1:8740/api/orquestador`
- Existing CORS allowlist stays restricted to `https://preceptoros.org`.
- Existing 1,023-byte body/response ceiling remains in force.
- No new port, channel, network publisher, or prompt/response forwarding is added.

Request:

```json
{"esquema":"preceptoros.orquestador/1","intent":"MAP_BRAIN_STATUS","payload":{}}
```

Response wrapper at the existing door, containing the #512 typed verdict:

```json
{"esquema":"preceptoros.orquestador/1","intent":"MAP_BRAIN_STATUS","estado":"NO_DATA","causa":"runtime_integrity_unavailable","dato":{"choice":null,"score":null,"no_data":true,"causa":"runtime_integrity_unavailable"}}
```

The nested fail-closed status object is exactly:

```json
{"choice":null,"score":null,"no_data":true,"causa":"runtime_integrity_unavailable"}
```

## Behavior and source boundaries

- The app currently has no measured local map-brain runtime integrity adapter. The route therefore always reports `runtime_integrity_unavailable`; it never upgrades based on model files, fleet identity, heartbeat, or a caller-supplied claim.
- The request payload is empty. Extra fields are rejected by the router; no identity, secret, model path, conversation, response, or machine state crosses this relay.
- `MAP_BRAIN_STATUS` is a new verb on the existing bounded `/api/orquestador` contract. It does not replace the chat, map, D7, or JN pieces.
- Public typed verdict source: `piskyRpapalo/preceptoros-web` main `odd/contracts/map-brain-status-verdict.schema.json`, SHA `b7d93350611073b2a4bfd9becfe204e1fe12e95d`, verified 2026-10-31.
- Service tree refreshed to PreceptorOS `1292a212e19a406bfac74671c1b94389f4d5f9be`; runtime smoke needs CI and rack browser evidence before the new relay can be claimed live.

## Checks

- Router test proves exact fail-closed JSON and rejects payload data.
- Response schema covers the wrapper; the public status schema remains owned by web #512.
- CI runs the full app checks on the exact PR head. Browser/UI consumption and a healthy model result remain NO_DATA until separately measured.
