# Node export route map · 2026-10-25

## Scope and method

Read-only route measurement on the live local PWA and the public gateway. No
credential, model data, database write, or CLI write was used. The only POST
probes carried the deliberately invalid empty JSON object `{}`. The local
handler rejects that body before forwarding it.

Machine stamp: `x86_64` (architecture only); local endpoint: `127.0.0.1:8740`.
Measurement date: 2026-10-25. The gateway response is a live observation, not a
claim about browser behavior or physical-device behavior.

## Measured chain

| Hop | Measurement | Result |
|---|---|---|
| Browser → local PWA | `interface/app.js:1040-1055` sends the selected signed credential to same-origin `POST /api/nodo/export` after an explicit submit. | Route is served by the local PWA; no browser rendering or CORS preflight was exercised. |
| Local PWA → export handler | `bin/preceptoros-pwa:506-544` reads JSON and dispatches `/api/nodo/export`; `nodo_export.py:24-40` validates the wrapper and credential before networking. | Invalid `{}` probe returned HTTP 400 `{"estado":"bloqueado","codigo":"cuerpo_invalido"}`. The early input rejection means this probe did not call the gateway or write a database. |
| Export handler → gateway | `nodo_export.py:10-16,42-63` declares provisional `https://api.preceptoros.org/aduana/cedulas`, sends JSON POST, and maps an HTTP error without a recognized `codigo` to `aduana_rechazo`. | The single invalid-body POST returned HTTP 404 `{"detail":"Not Found"}`. No gateway `codigo` was returned; the adapter mapping for this response is `aduana_rechazo` (HTTP 502), not `aduana_no_disponible` or `cedula_mal_formada`. |
| Rack node credential source | Read-only inspection of `<private-ref>/nodos.py sha256=NO_DATA scope_not_signed:81-91,112-130,265-288`. | Schema and credential construction are present. The rack-side `cedula` function emits a declaration with `firma: null` and `autenticidad: NO_DATA`; it is not a signed credential. No credential values were read into this report. |

## Gateway observations

Commands run from this `x86_64` rack node on 2026-10-25:

```sh
curl -sI https://api.preceptoros.org/aduana/cedulas
```

Observed: HTTP/2 404; `date: Sun, 25 Oct 2026 16:58:59 GMT`,
`content-type: application/json`, `content-length: 22`, `server: cloudflare`,
`cf-cache-status: DYNAMIC`, and `alt-svc: h3=":443"; ma=86400`. The response also carried
per-request/reporting headers (`cf-ray`, `report-to`, `nel`); their values are
omitted because they are transient correlation/reporting data.

Exactly one gateway POST probe was run:

```sh
curl -sS -w '\nhttp_status=%{http_code}\n' -H 'Content-Type: application/json' --data '{}' https://api.preceptoros.org/aduana/cedulas
```

Observed body: `{"detail":"Not Found"}`; HTTP 404. The result supports the
inference that this path is not currently bound for POST. Exact route binding
and any receptor behind a future route remain **NO_DATA** because the response
is the generic 404, with no typed gateway error. CORS behavior is **NO_DATA**:
no OPTIONS probe was requested; the HEAD response did not include an
`access-control-allow-origin` header. The normal app flow is same-origin to the
local PWA, then server-side Python to the gateway, so browser CORS is not on
that observed path.

## Local PWA observations

The requested GET was piped through a field filter so only state and version
metadata were emitted:

```sh
curl -sS -w '\nhttp_status=%{http_code}\n' http://127.0.0.1:8740/api/estado | python3 -c 'import json,sys; raw,status=sys.stdin.read().rsplit("\nhttp_status=",1); d=json.loads(raw); v=d.get("version") or {}; print("http_status="+status.strip()+" state="+str(d.get("estado"))+" version_date="+str(v.get("fecha"))+" version_hash="+str(v.get("huella"))+" files="+str(v.get("ficheros"))+" missing_count="+str(len(v.get("faltan",[]))))'
```

Observed: HTTP 200, state `ok`, served version date `2026-10-23`, version hash
`b26973ce55ba`, 15 files, 0 missing. Source: `bin/preceptoros-pwa:1085-1144`
and `version.py:53-84`.

The local export probe was:

```sh
curl -sS -w '\nhttp_status=%{http_code}\n' -H 'Content-Type: application/json' --data '{}' http://127.0.0.1:8740/api/nodo/export
```

Observed: HTTP 400, `cuerpo_invalido`. Source validation (`nodo_export.py:30-31`)
returns before constructing or sending the gateway request. No database or
command-line write was performed.

## Result and gaps

- Local PWA state route: **MEASURED**, HTTP 200; version stamp recorded above.
- Local export route: **MEASURED**, HTTP 400 on the invalid-body probe; early
  validation prevented forwarding.
- Gateway GET/HEAD and POST at the provisional path: **MEASURED**, HTTP 404.
- Gateway route registration / final route: **NO_DATA**, cause: generic 404 has
  no typed receiver error.
- CORS preflight: **NO_DATA**, cause: no OPTIONS request was made.
- Receptor state behind the final route: **NO_DATA**, cause: no bound route was
  reached.
- Browser rendering and physical-device behavior: **NO_DATA**, cause: neither
  was exercised.

This map is a proposal based on the measured node side. It does not change the
provisional endpoint or claim gateway readiness.
