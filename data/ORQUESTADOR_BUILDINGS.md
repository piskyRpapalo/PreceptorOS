# App routes for building cartridges

This contract gives the web client a bounded path into the local app. It
validates and relays records; it does not implement the game engine, render
assets, deploy a web building, or write RAG data.

## Route

`POST http://127.0.0.1:8740/api/orquestador`

The local PWA accepts UTF-8 JSON below 1,024 bytes. The whole request, compact
building label, and response are checked as bytes; 1,024 bytes or more is
rejected as a whole. The optional browser origin is exactly
`https://preceptoros.org`; its preflight permits only `POST`, `OPTIONS`, and
`Content-Type`, without credentials. Every other origin and requested header
is denied. A browser that does not grant local-network access cannot use this
route and must show `NO_DATA` with its cause.

Request envelope:

```json
{"esquema":"preceptoros.orquestador/1","intent":"QUERY_STATE","payload":{"id":"ensayo"}}
```

The three intents are closed:

| Intent | App behavior |
| --- | --- |
| `DEPLOY_BUILDING` | Validates `preceptoros.edificio/1` and its required `ficha`; returns `PROPOSED`, `requiere: FIRMO DESPLIEGUE`, and no effect. The web motor owns game behavior and actual rendering/deployment. |
| `QUERY_STATE` | Accepts either a local cartridge `id` (delegated to an injected rack adapter) or a `consulta` (retrieved from the local read-only RAG index, then answered by the local mini-model). RAG returns `MEASURED` only when retrieval and local inference both succeed; otherwise it returns `NO_DATA` with cause. The app does not calculate lifecycle, combat, cooldown behavior, or game results. |
| `UPDATE_RAG` | Always returns cause-bearing `NO_DATA` from chat. RAG writes require a separately attached, signed `frontera.py` adapter; no chat request writes data. |

Every response includes a deterministic `motivo` code and `habla` utterance
selected from the exact `(intent, estado)` pair. The web client may speak the
fixed utterance; this contract does not synthesize audio or let model text
choose the status. The pair list has a 1:1 parity check against
[orquestador-respuesta.schema.json](orquestador-respuesta.schema.json), which
is the response contract. `NO_DATA` carries a concrete `causa`; `STALE` uses
its fixed utterance and carries the rack observation as `dato`.

The language/math card schema is [ficha_cartucho.schema.json](ficha_cartucho.schema.json).
It carries the closed verbs, measures and their stamps/causes, postures,
`cooldown_ticks`, and `ram_bytes`. The full compact label includes the web
manifest plus this card and must remain below 1,024 bytes. Visual skin and
`silhouette_hex` are separate assets and are rejected as card fields.

The route is local-first and has no credentials, outbound calls, install
operation, or telemetry. `DEPLOY_BUILDING` is a proposal only until the
signature boundary is implemented and exercised.
