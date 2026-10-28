# External signature announcement · proposal

Status: PROPUESTA · REQUIERE_FIRMA. Baseline: app main `78364da`, 2026-10-28. This is a contract proposal, not a network implementation. Reading depth: app registration, account signature, export and PWA route files; other repositories and live endpoint behavior are NO_DATA because they were not examined.

## Measured app model

- `interface/node_registration.js:27` creates a canonical node cédula with null signatures; `:45` requires explicit consent, checks its hash and size, and POSTs to `/api/v1/cedulas`. Only a matching pending/untrusted receipt is accepted (`:64`). The mounted form requires an explicit action (`:116`, `:135`, `:139`). The rack ceremony and trust-anchor review are described in `interface/app.html:169`; their execution and live API response are NO_DATA because neither was exercised.
- The R-NODO sequence visible here is draft → preview → consented → submitting → pending_untrusted, or the synthetic catalog stub (`interface/node_registration.js:6`, `:79`). `node_registration.py:1` and `:16` implement a loopback test preview, no persistence or real verification; it is not a live registration. The precise full ceremony beyond this app sequence is NO_DATA, since this tree does not establish it.
- A node credential signature covers canonical JSON without the hash, signature and authenticity fields (`nodo_app.py:47`, `:51`); SSH verification uses a configured Sovereign signer and namespace (`:57`). Missing signature, signer list or verifier is NO_DATA; an invalid signature is rejected. A linked device reaches level 3 only after verification (`:103`, `:120`). Account signatures are a separate SSH signature over bytes, tied to a public-key fingerprint (`cuenta_cangrejo.py:59`, `:109`); neither proves a real-world identity by itself.
- The explicit signed-credential exporter validates shape and authenticity before network transfer (`nodo_export.py:26`), and reports the upstream state without upgrading pending to trusted (`:72`). It accepts a node cédula, not an external person's announcement. `node_registration.py:25` accepts only the synthetic request shape and rejects a real signer (`:36`).

## Baseline acceptance case

The commissioned approximately 12-hour external test is DECLARADO by the Sovereign; its raw record and independent replay are NO_DATA because they were not supplied. The inspected app paths above contain no receiver for an external signature announcement. Thus an end-to-end external announcement and node registration is NO_DATA: there is no identified channel and no measured receipt. This source inspection does not prove the absence of every possible external service. Search on this app tree: `rg -n -i 'r-nodo|external.sign|firma.externa|api/v1/cedulas'`; source and lines above define the scope.

## Proposed smallest matching piece

1. A person explicitly chooses a node and initiates an announcement, previews its exact contents and destination, then confirms each transmission. No background collection, polling for identities, or silent registration. Only the necessary public declaration is sent; private keys, machine identifiers and unrelated account data never leave the device.
2. The eventual Sovereign-selected landing endpoint and its schema are NO_DATA pending the web proposal and decision. Until then the app shows NO_DATA with cause and cannot send. The existing cédula endpoint is not assumed to accept this new message.
3. A node receiver, once commissioned, validates a versioned bounded envelope and deterministic canonical bytes. It records an explicitly declared announcement only after a valid receipt from its own storage; a duplicate produces the same logical record and a cause-bearing receipt. A signature can be called verified only if the agreed key, signed bytes and verification method are available and verification succeeds. Missing verification material stays NO_DATA; invalid data is rejected. A received declaration grants no node admission, authority or level 3.
4. Minimal acceptance cases: no consent causes no send or record; confirmation names the selected node and exact declaration; invalid or oversized data is rejected; unavailable destination returns NO_DATA with cause; replay does not create a second logical record; unavailable verifier never yields verified; successful registration has a node receipt; no private key or unrelated identifier appears in the envelope or receipt. A real external test must produce both transmission and node receipt before success is MEDIDO.

## Log

- 2026-10-28: endpoint, representation of the external signature, consent withdrawal and retention policy remain undecided. Default: no network action and NO_DATA with cause; continue with this reviewable contract. The announcement is separate from Sovereign-signed node credentials. No signature is inferred from this document.
