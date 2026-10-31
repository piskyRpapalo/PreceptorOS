# PWA node identity and live presence

Status: PROPOSAL · propose-only · no runtime or service changes in this slice.

## Objective

Let the local PWA show which canonical fleet node this installation represents and whether that node is currently present in the public map. Keep identity configuration local to the PWA, fleet identity in `lab/flota.json` (`preceptoros.flota/2`), and liveness exclusively in a fresh `GET /api/v1/latidos` response. The fleet snapshot is never a liveness source.

## Authority and scope

- Canonical identity source: `piskyRpapalo/lab` `main`, `flota.json`, `preceptoros.flota/2`; its `map_heartbeat_snapshot` is descriptive history, not runtime presence.
- Runtime presence source: `https://api.preceptoros.org/api/v1/latidos`, schema `preceptoros.openworld-estado/2`; accept only a valid response row matching the configured canonical identity and its unique cell.
- Local identity source: an operator-provisioned, untracked config file under the app data root, proposed as `node-identity.json`. It contains only the public fleet node ID. It must not contain a credential, private address, model identifier, API token, signing material, or sender sequence.
- This PWA is a reader. It does not POST heartbeats, add a D7 sender, change Aduana bindings, or infer a physical device/model/credential join.
- The page exposes only the typed identity and liveness result needed by the map; no new public service endpoint, telemetry, chat transport, or secret is introduced.

## Proposed files

1. `odd/tasks/pwa-node-identity-presence.md` — this specification and evidence log.
2. `node_identidad.py` — strict local config reader plus fleet contract resolver and bounded D7 read adapter. No snapshot liveness fallback.
3. `tests/test_node_identidad.py` — fixture tests for configured match, missing/malformed/unknown identity, duplicate ID/cell, unavailable or malformed D7 response, LIVE/STALE response rows, timeout and response-size limit. Tests inject HTTP and clock; no public requests in the unit suite.
4. `bin/preceptoros-pwa` — add one GET route `/api/nodo` that returns the typed adapter result and never includes raw config paths or transport details.
5. `interface/app.html` — consume `/api/nodo` at the existing map surface and render the returned state; no second map, new publisher, or request on page load before the existing user gesture/poll boundary.
6. `interface/sw.js` and `version.py` — advance the service-worker seal together if the served page changes, then verify the frozen-map file set and returned version against the exact commit.
7. `tests/test_pwa.py` and the relevant app browser gate — route and rendering contract, fail-closed cases, zero D7 calls without the declared poll/gesture, and no cache-based LIVE result after a response becomes stale.

## Contract and failure behavior

- `node-identity.json` must be a regular local file with exactly `{ "schema": "preceptoros.pwa-node-identity/1", "node_id": "..." }`. It is ignored by Git and never served as a static file.
- Resolve the configured `node_id` against the canonical `nodes[].id` entries in the measured `flota/2` artifact. Require one exact match and a unique `(q,r)` cell. Missing file, invalid shape, unknown or duplicate ID/cell returns `NO_DATA` with a stable cause; no default node is chosen.
- On a declared poll only, make one bounded same-origin-independent HTTPS GET to the fixed D7 URL. Require HTTP success, expected schema, typed MEDIDO coverage and one unambiguous matching row. Respect the source's `LIVE`/`STALE` status at response time; do not persist it or revive it from the fleet snapshot.
- Timeout, TLS/HTTP error, oversized body, invalid JSON/schema, missing row, duplicate matching row, alias/cell mismatch, or expired/STALE observation returns `NO_DATA` or `STALE` with an explicit cause. No exception text, local path, private address, or credentials are returned.
- Response size and timeout are constants selected only after measuring the current API payload and app runtime constraints; values remain `NO_DATA` until that measurement. Do not invent them in implementation.
- Keep coverage semantics separate: public D7 presence does not prove the local computer, model, or credential is that node.

## Checks and acceptance

- Contract tests cover every failure case above using injected fixtures; sabotage tests reject an unknown ID, duplicate cell, malformed D7 schema, and attempted snapshot fallback.
- Python: `python3 -m unittest discover -p 'test_*.py'`; repository gate: `./bin/pruebas`; browser tests on Chromium; report each total, skips and sabotage result independently.
- Static privacy gate proves no config value/path/key is served or committed. Static asset checks prove `app.html`, PWA route, `sw.js`, and `version.py` agree with one seal.
- Manual local smoke uses an explicitly provisioned test identity and captured API fixtures; physical rack/node join remains `NO_DATA` until measured at the authorized rack.
- No service restart, config provisioning, production deployment, public heartbeat mutation, or merge is included in this proposal.

## Open questions and log

- The exact current `flota/2` canonical source SHA and freshness policy for reading the lab contract at runtime must be fixed by the implementation piece. A stale checked-in copy cannot silently become authoritative.
- A public D7 `LIVE` row binds only the configured public alias/cell to current receiver state. A physical node or local model binding remains `NO_DATA` without separate measured evidence.
- 2026-10-31: Mesa commission ·6547694162 authorizes a minimal PWA proposal: identity from local gate config, fleet from the public D7 route, identity catalog from `flota/2`; no secret or new channel. This document records the design only.
