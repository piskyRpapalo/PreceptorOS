# Phone-led node self-registration: design proposal

**Status:** proposal for Sovereign review (`REQUIRES_FIRMA`). **Date:** 2026-10-25. **Scope:** design only. No keys, credentials, database changes, or Cloudflare actions were performed.

## Decision in one sentence

The calendar date for “the Sovereign creates his own node in 1–2 clicks” is **NO_DATA** as of 2026-10-25. The required signer and custody model is undecided, both web trust pins are empty, the registration route is unbound, and the app has no creation flow. The click count is also unmeasured. Set a date only after those choices are signed and a phone-to-catalog end-to-end run measures the actual interaction count.

## Measured starting point

- The phone-to-rack bridge works for `/api/estado` through `adb reverse tcp:8740 tcp:8740` (D2 measurement supplied for this commission). This proves reachability for that endpoint only; node registration over the bridge is **NO_DATA**.
- `nodo_app.py:47-83,165-180` verifies a supplied SSH signature against local `allowed_signers` and imports a credential into local `nodo.json`. It does not create or sign a cédula.
- `nodo_export.py:10-16,24-47` targets provisional `POST https://api.preceptoros.org/aduana/cedulas`; it validates a signed credential and forwards it. It does not sign. The gateway route is measured as unbound (404) in the commission context; the command-level receipt is not available on this design branch.
- Rack source `nodos.py:112-130,265-288` (external repository) has local create/admin operations and emits `preceptoros.cedula-nodo/1` with `firma: null`; the rack declares and records, it does not sign. Its device-side key/signing helpers at lines 291-320 exist as a separate script, not an app flow. No rack operation was run for this design.
- Web `public/game/node_reception_contract.js:56-79,91-94` defines a signed cédula packet and `POST /aduana/cedulas`. `public/game/node_signature_verify.js` verifies signatures against a manifest; `node_trust_anchor.js:3` has null key and manifest pins, and the manifest export is null. The verifier therefore cannot establish trusted authenticity today.
- Web `public/assets/enviar.js:2,18-45,58-75` uses `/api/v1/reto` and `/api/v1/paquetes` for signed `preceptoros/correcciones/1` packets queued for review. This is an existing correction transport, not a node registry. The static node catalogue is `public/game/nodos-cedulas.js`; a live registry projection is **NO_DATA**.
- Exact current CORS behavior, gateway receiver implementation, registry persistence/uniqueness/revocation behavior, and web-to-gateway catalogue integration: **NO_DATA**.

## Proposed flow and build order

Each step is a separate reviewable piece; later steps depend on the preceding signed decisions and contracts.

| Order | Hop and measured artifact today | Exact piece to build |
|---|---|---|
| 0 | Sovereign decision; there is no agreed issuer/custody or anchor ceremony. Web pins are null (`public/game/node_trust_anchor.js:3`). | Sovereign signs the signer/custody, trust-anchor, identity uniqueness/revocation, and transport decisions below. No implementation before this boundary. |
| 1 | Phone reaches rack `/api/estado` over the measured USB reverse bridge. `nodo_app.py` imports only an already-issued credential. | App design/API contract for “Create node”: collect proposed node details, show canonical cédula and consequences, obtain explicit local consent, and expose signed/pending states. Do not claim one-click until measured. |
| 2 | Rack `nodos.py` can create a local row and emit an unsigned cédula; its phone-side helper is not integrated. | Implement the chosen signing flow on the phone or at the approved ceremony. Produce the exact `preceptoros.cedula-nodo/1` body expected by the verifier, bind signer identity and node identifier, and sign only after consent. Avoid exposing private key material to app logs/network. |
| 3 | App exporter already targets provisional `POST /aduana/cedulas` (`nodo_export.py:10-16`); gateway route is measured unbound (404). | Private gateway Worker receiver: validate size/schema/hash/signature/anchor, enforce idempotency and uniqueness, return a verifiable receipt, and expose a read-only public catalogue projection. Define rejection and retry semantics. No route or storage behavior is assumed to exist. |
| 4 | Web contract and verifier exist; trust pins and manifest are empty. | After the anchor ceremony, deploy the signed manifest/pins through the reviewed web piece; verify issuer, namespace, signature, body hash, registry receipt, revocation state, and duplicate policy. Pending/untrusted records must remain visibly pending, not catalogued as trusted. |
| 5 | `nodo_app.py:165-180` locally caches an imported credential; no server-issued receipt flow is integrated. | App verifies the registry receipt and signed cédula against the approved trust configuration, then stores the local cache and presents an accessible completion state. A failed or unavailable hop remains `NO_DATA` with cause. |
| 6 | Static catalogue exists; live projection consumer is **NO_DATA**. | Web reads the gateway’s reviewed public projection, runs the same verification rules, and renders only trusted, non-revoked nodes. Keep source provenance and pending/rejected states clear; do not turn unsigned rack declarations into trusted catalogue entries. |
| 7 | D2 bridge is measured, but this registration path and the claimed click count are not. | End-to-end acceptance on the phone: create, sign, submit, receive receipt, and observe verified catalogue entry; record device, commands, timing, taps, failures, and exact version. Only then set a date and substantiate “1–2 clicks.” |

## Sovereign decisions (`REQUIRES_FIRMA` each)

### Who signs the cédula, and where?

| Option | Evidence and tradeoff |
|---|---|
| Sovereign key on phone | Rack script documents device-side key and signing helpers (`nodos.py:291-320`), but the app has no integration and its current verifier expects SSHSIG plus local `allowed_signers` (`nodo_app.py:47-83`). Keeps signing with the person’s device and fits local-first custody; requires a reviewed phone key-storage, backup, recovery, rotation, and signer-enrollment design. These protections and UX are **NO_DATA** today. |
| Rack ceremony | Rack can create a row and issue an unsigned declaration (`nodos.py:112-130,265-288`); it explicitly does not sign. A ceremony could have the Sovereign sign on a trusted device while present at the rack, but signing location, identity binding, and receipt are not implemented. Putting the signing key on the rack would change the documented custody boundary and needs a separate explicit decision. |
| Gateway-issued identity | Current `/aduana/cedulas` is unbound (404), and no issuer is measured. This centralizes issuance and recovery in a private Worker and requires a new authority key, custody/operations policy, and trust ceremony. It departs most from the existing person-signed cédula model. |

### What does the trust-anchor ceremony pin?

Today the web anchor has null `key_sha256` and `manifest_sha256`, and the manifest export is null. The existing verifier expects an issuer key fingerprint and signed-manifest fingerprint; it checks SSH namespaces `preceptoros-trust-manifest` and `preceptoros-cedula` (`node_signature_verify.js`). The Sovereign must decide and sign: (1) issuer public-key fingerprint and manifest hash, (2) issuer identity and permitted namespace/purpose, (3) whether one key signs manifest and cédulas (current verifier expects the same key), (4) validity and environment, (5) rotation, revocation, compromise recovery, and pin-update authority, and (6) how an out-of-band human verifies the values before pinning. Pins establish a verification root; they do not themselves sign a node cédula. No values are generated or pinned here.

### Which transport wins: Door 1 or `/api/v1/paquetes`?

**Proposal:** use Door 1 (`POST /aduana/cedulas`) for node identity and keep `/api/v1/paquetes` for its current correction/review queue. This aligns the existing app exporter and web cédula contract. Door 1 currently returns 404; it needs a private Worker receiver, validation, durable registry/idempotency, uniqueness and revocation rules, receipt, and public read projection. These are all new pieces.

`/api/v1/paquetes` already has a challenge/sign/POST path, but its measured caller sends `preceptoros/correcciones/1` for human review (`public/assets/enviar.js`). Reusing it would require a new node-registration schema and receiver policy, registry importer, idempotency/uniqueness, trust verification, receipt and catalogue publication semantics, while separating identity creation from the correction queue. This may reuse transport plumbing, but semantic fit and runtime support are **NO_DATA**. The Sovereign chooses; no dual-write is proposed.

## Piece boundaries and review gates

| Owner | Piece | Review boundary |
|---|---|---|
| Sovereign ceremony | Choose signer/custody, node authority/uniqueness, and recovery policy. | Separate `REQUIRES_FIRMA`; no code can decide this. |
| Sovereign ceremony | Pin issuer key and manifest; approve namespace, validity, rotation, revocation, and pin-update procedure. | Separate `REQUIRES_FIRMA`; values remain unset until performed. |
| App | Local create/preview/consent/sign integration, receipt verification, and cache/status UI. | App PR titled `REQUIERE_FIRMA`; no key generation in this design. |
| Private gateway Worker | Door 1 receiver, signature/anchor validation, registry, dedupe, receipt, and read-only catalogue projection. | Gateway PR titled `REQUIERE_FIRMA`; private worker code remains a distinct piece. |
| Web | Trust manifest/pin delivery after ceremony, verified catalogue projection, and visible pending/revoked/error states. | Web PR titled `REQUIERE_FIRMA`; static catalogue replacement is not authorized here. |
| Rack, only if selected | Reviewed bridge from the existing local node protocol to the chosen registration contract. | Separate PR titled `REQUIERE_FIRMA`; no rack writes or CLI execution in this design. |

No piece is approved for implementation by this proposal. No merge, deployment, key operation, database write, or Cloudflare operation is included.

## Receipt facts and gaps

Measurement date: 2026-10-25. Source paths and line ranges above identify code inspected; live 404 and D2 bridge facts are supplied as measured commission context. Command/yardstick for the gateway request and D2 phone observation are **NO_DATA in this workspace receipt** (prior measurement receipts were not available on the `origin/main` design branch). Browser rendering, live service worker behavior, CORS, route receiver, registry, and full self-registration remain **NO_DATA**. This document is a design, not an end-to-end result.
