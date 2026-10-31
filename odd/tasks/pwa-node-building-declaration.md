# PWA node identity provisioning and building declaration

Status: PROPOSAL · propose-only · 2026-11-01.

## Objective and boundary

Provision one canonical public node ID into this local PWA installation, then let the operator explicitly declare the already assigned building for that node. The app must never generate, display, or transmit a heartbeat credential to browser JavaScript. The local Python door reads the already provisioned credential from a private file and makes the fixed HTTPS request only after an explicit declaration action.

The signed Aduana writer contract is the authority for the declaration: `POST https://api.preceptoros.org/api/v1/edificios`, exact body `{"esquema":"preceptoros.edificio-declaracion/1","edificio":"observatorio-primer-ancla"}`, header `x-heartbeat-key`, one fixed assignment for canonical node `primer-ancla` at `{q:0,r:0}`. Aduana resolves the credential to a configured node and rejects any mismatch, duplicate assignment, or unassigned node. This app slice declares only that existing allocation; it does not create assignments for other nodes.

## Local provisioning

- Store only `{ "esquema":"preceptoros.pwa-node-identity/1", "node_id":"…" }` at `~/.preceptoros/node-identity.json`, atomically with mode 0600. The app may provision once; same-ID replay is idempotent and a different ID is rejected until the operator deliberately removes the local file.
- The operator enters the exact public ID from canonical `flota/2`; local validation checks syntax and does not fetch or cache a fleet snapshot. Provisioning is a local claim, not a canonical identity proof. At declaration time Aduana resolves the existing credential to exactly one configured node, and the PWA checks that the receipt names its configured ID.
- Read the existing credential from `PRECEPTOROS_HEARTBEAT_CREDENTIAL_FILE`, or the established local default `~/.preceptoros/heartbeat-key`. Require a regular non-symlink file with no group/world permissions and exactly 64 lowercase hex characters. This PR creates no key, copies no key, and does not alter heartbeat sequence state.
- Identity and credential files remain local and are never served as static assets or returned by an API. Missing/malformed files return typed `NO_DATA` with a stable cause.
- The identity form writes only to the loopback PWA. Building declaration is a separate explicit user action; browser code calls only the same-origin PWA route and never receives the credential.

## Fail-closed request path

`POST /api/nodo/edificio` is accepted only from a loopback client and a same-origin browser request. The server reloads both local files for each explicit request, requires configured identity `primer-ancla`, then POSTs the exact fixed declaration to the fixed HTTPS endpoint with an 8-second timeout and bounded response. The response must match `preceptoros.recibo-edificio/1`, the configured node and building, the request payload digest, and the receiver's receipt digest. Error bodies and exception text are reduced to stable cause codes; no key or local path enters the response.

No identity lookup, heartbeat, public fetch, or write occurs on page load. Provisioning and declaration are user-triggered. The PWA has no authority to mint identity, change node bindings, rotate credentials, or write the D7 heartbeat stream.

## Files and offline checks

- `data/pwa-node-identity.schema.json`, `data/edificio-declaracion.schema.json`, `data/pwa-edificio-accion.schema.json`, `data/recibo-edificio.schema.json`: versioned `preceptoros.*` wire/local contracts.
- `node_building.py`: strict local provisioning, credential reader, and injectable HTTP client.
- `tests/test_node_building.py`: temporary directories, synthetic credential, injected transport only; no network or rack service.
- `bin/preceptoros-pwa`, `interface/app.html`, `interface/node_building.js`, `interface/sw.js`, `version.py`, and focused tests: loopback routes, explicit UI actions, delivery/version alignment.

Tests must prove absent/malformed identity or key, insecure/symlink credential, conflicting reprovision, wrong node, tampered receipt, oversized/error responses, timeout, loopback/origin rejection, exact endpoint/body/header, no credential leakage, and no transport before the declaration action. Browser/runtime, live Aduana, D1 persistence, and rack provisioning remain `NO_DATA` until separately measured.

## Evidence log

- Base: clean `origin/main` at `a5ab7bfa987c18cfce2c661b38748e4ae9dbd0ee`; branch `mistral/pwa-node-building-declaration-20261101`.
- Assignment and request contract read from the signed writer specification in Aduana; no production key, network request, service restart, or database write was used while preparing this piece.
- **Open question:** this local checkout does not establish that the PWA service has `PRECEPTOROS_HEARTBEAT_CREDENTIAL_FILE` configured or that the default key file exists. Until the rack supplies the already provisioned key through one of those paths, declaration must return `NO_DATA` and make no network request.
