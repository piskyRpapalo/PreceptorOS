# Sovereign node-signing ceremony: design proposal

**Status:** design only; `REQUIRES_FIRMA` at merge. **Date:** 2026-10-25. No key was generated, imported, or used. No trust anchor was pinned.

## Ruling applied

The Sovereign's signed ruling sets the signer ceremony at the rack, with the Sovereign present and a trusted personal device performing the signing act. The rack never stores the signing key, and its declaration keeps `firma: null`. The phone is the intake client: it builds and displays the canonical unsigned cédula, explains the consequences, asks for explicit local consent, and submits it to `POST https://api.preceptoros.org/api/v1/cedulas`. The pending intake remains untrusted until a valid ceremony and trust verification complete.

The Sovereign has not yet selected the exact trusted device, key-backup method, or trust-anchor ceremony. Those remain explicit decisions for the next Mesa presentation. This proposal does not fill them in.

## Measured starting contracts

- `nodo_app.py:47-83` verifies OpenSSH signatures using the principal `soberano`, namespace `preceptoros-cedula`, local `allowed_signers`, and `ssh-keygen`; it does not sign.
- `nodo_app.py:25-29` excludes `sha256`, `firma_ssh`, `firma`, and `autenticidad` from the signed body. `nodo_app.py:86-99` validates `preceptoros.cedula-nodo/1`, node name, devices, and body hash.
- `nodo_export.py:10-16,24-47` now targets the Sovereign-selected apex endpoint and validates a supplied signature before sending. The new phone intake is separate because it intentionally sends a pending unsigned cédula after consent.
- Rack `nodos.py:265-288` emits its cédula with `firma: null` and `autenticidad: NO_DATA`; the rack does not sign. Its device-side helpers at lines 291-320 are not an integrated signing UI or ceremony.
- Web verifier code expects pinned issuer/manifest fingerprints; both web trust pins are currently null, per the earlier measured source review. The public route, pending intake store, signed receipt, and CORS behavior are not implemented or measured in this package.

## Proposed ceremony sequence

1. **Intake on the phone.** The phone presents the cédula schema, node identifier, `admin`/device fields, hash, and explicit consequences. It shows `firma: null`, `firma_ssh: null`, and `NO_DATA` authenticity. The Sovereign reviews the exact canonical body and explicitly consents to submit it. This consent allows only pending intake; it does not authorize a signature or claim of trust.
2. **Pending receipt.** The Door 1 endpoint returns a request/receipt identifier, canonical cédula hash, `state: pending`, `trust: untrusted`, and a machine-readable cause such as `signature_missing`. The phone verifies that the returned hash matches the preview and reports the cause. This is an intake acknowledgement, not a verified node or a signed credential.
3. **Move into the ceremony.** At the rack, the trusted signing device retrieves or receives the exact pending cédula associated with that receipt identifier. Transfer method (local rack protocol, QR, or removable file) is not implemented; it must preserve exact bytes and show the same hash on both the phone and signing device. A mismatch or unavailable pending record aborts.
4. **Sovereign review and confirmation.** With the Sovereign physically present, the signing device displays the node identifier, issuer/principal, signature namespace, cédula hash, and the resulting registration consequences. The Sovereign confirms the exact hash and performs the signing act on that device. The private key never enters the rack service, phone submission, gateway, or receipt.
5. **Attach and verify.** The ceremony adds the OpenSSH signature as `firma_ssh` while preserving rack-origin `firma: null`. The signed body is the canonical cédula body defined by the app contract; changing any signed field requires a new review and signature. The gateway verifies the issuer against the approved anchor and verifies the body hash before it can move beyond pending/untrusted.
6. **Final receipt and catalog state.** The gateway returns a receipt tied to the original receipt identifier and cédula hash, with explicit state and cause. The client verifies the hash, state transition, and receipt authenticity under the Sovereign-approved receipt trust policy. Only a fully verified, non-revoked result can be displayed as a trusted catalogue entry. Until the anchor ceremony chooses how receipt authenticity is established, the receipt remains informational.

## Trusted-device options for the Sovereign

| Option | Evidence and tradeoff |
|---|---|
| Sovereign's personal phone, signing locally during the rack ceremony | Convenient and the same device already previews/submits the request. The current PreceptorOS phone UI has no signer integration or measured secure key storage; daily-use exposure, OS backup, and lock-screen recovery need review. **NO_DATA** for hardware-backed storage on the commissioned handset. |
| Sovereign-controlled dedicated signing device brought to the rack | Separates signing from the daily phone and can be kept offline except for an explicit transfer. Adds a device, maintenance, and careful transfer/hash comparison. No such device or workflow was measured. |
| Existing trusted computer used as the signing device at the rack | The current verifier already uses OpenSSH SSHSIG conventions and `ssh-keygen`, so this matches the verification format. Requires the Sovereign to identify and physically control the computer and protect its key. Device identity, custody, and ceremony interface remain **NO_DATA**. |

**Proposal to take to the Sovereign:** use a Sovereign-controlled dedicated signing device at the rack if already available; otherwise use the personal phone only after its key protection and recovery have been measured and reviewed. The exact device is a signed choice, not an agent assumption.

## Identity binding and exact bytes

The node identifier is part of the canonical cédula body, so the Sovereign's signature covers the specific node proposal. The signer principal is `soberano` and the namespace is `preceptoros-cedula`, matching the current app verifier. The public-key fingerprint must match the issuer selected by the trust-anchor ceremony. The cédula `sha256` is recomputed over the canonical body; the ceremony device displays it before signing and the receipt repeats it. Any edit to node, admin, device list, or other signed field changes the hash and invalidates the review.

The phone cannot turn a pending request into a signed one. The rack declaration retains `firma: null`; the separate `firma_ssh` is attached only by the trusted signing device after confirmation. No signature is accepted if the signer principal, namespace, fingerprint, hash, or receipt association fails verification.

## Receipt options to bring with the trust-anchor question

| Receipt model | What the Sovereign can verify | Cost / limitation |
|---|---|---|
| TLS intake acknowledgement | Endpoint, receipt identifier, returned cédula hash, and pending/untrusted cause. | Confirms transport intake only. It is not a portable cryptographic proof of gateway state and cannot independently establish trusted catalog publication. CORS and live route behavior are **NO_DATA**. |
| Gateway-signed receipt under a separate pinned receipt key | Signature, receipt identifier, cédula hash, state, cause, and transition independent of the cédula signer. | Requires a second key, custody, anchor, rotation/revocation, and verification path. None exists today. |
| Receipt signed by the same issuer key as the cédula | Can reuse one trust root if policy permits. | Couples intake-service status to the Sovereign's signing authority and does not prove independent gateway custody. The existing verifier assumes one key for manifest and cédula; using this key for gateway receipts would need a new namespace and explicit policy. |

**Recommended interim truth:** a pending receipt says only “these bytes were received and are awaiting the ceremony.” It must never label the node trusted. The Sovereign should decide whether a separate gateway receipt anchor is required before the receipt can support catalog publication.

## Concrete trust-anchor ceremony options for the Mesa

Both current web pins (`key_sha256` and `manifest_sha256`) are empty. The web verifier currently expects the same issuer key to verify the trust manifest and cédula. The Mesa can bring these choices:

| Option | Ceremony and pins | Tradeoff |
|---|---|---|
| One Sovereign issuer root | In person, the Sovereign verifies the issuer fingerprint and signed manifest hash on the trusted device and an independent display. Pin both values; the same issuer key signs the manifest and cédulas, matching the current verifier. | Lowest implementation change. A compromised issuer key affects both manifest and cédula authority. |
| Split manifest and cédula issuers | The Sovereign pins separate fingerprints and explicitly records which key may sign each namespace. Update the current verifier, which assumes a shared key. | Better separation of duties, with more pins, rotation rules, recovery paths, and code to review. |
| Add a separate gateway receipt key | Keep the Sovereign issuer pin for cédulas and add a gateway receipt fingerprint for signed intake/final receipts. | Gives portable proof of gateway state, but creates a distinct operational key and independent rotation/revocation ceremony. |

For comparing fingerprints during the human ceremony, options are (a) show the fingerprint and manifest hash as a QR on both the trusted signing device and an independently maintained reference device, or (b) read/compare the complete values from a separately held signed paper record. QR is quicker but depends on the reference device's integrity; paper avoids a second live display but needs secure custody and a clear update procedure. In all options, the Sovereign approves the values and update authority in person; no values are proposed or pinned here.

## Backup, recovery, and rotation

- Keep the signing key only on the selected trusted device. The rack and gateway store public identity and signatures, never the private key.
- Backup options for the Sovereign: an encrypted offline export held separately from the device, or a second Sovereign-controlled signing device. The first adds backup-passphrase custody; the second adds device custody and synchronization risk. Neither is implemented or measured.
- Recovery after device loss must not be a gateway reset or rack override. It requires an out-of-band Sovereign ceremony that revokes the lost fingerprint and anchors a replacement issuer before new signatures are trusted.
- Rotation should bind both old and new public fingerprints and require proof from the new key plus authorization from the old key when available. Rack `nodos.py` has a device-key rotation helper, but that helper covers device intents, not this cédula issuer; reuse requires a separately reviewed protocol adaptation.
- Define expiry, revocation distribution, compromise response, and maximum pending lifetime in the trust-anchor piece. Current values: **NO_DATA**.

## Valid and invalid ceremony conditions

**Valid only when** the Sovereign is present; the selected trusted device is under his control; the exact pending hash and node identifier match on phone, rack, and signer; explicit consent is recorded for that body; the signature verifies under the approved principal, namespace, and pinned fingerprint; the request is not stale, replayed, duplicate, or revoked; and the receipt repeats the signed cédula hash and passes the chosen receipt policy.

**Abort and remain pending/untrusted when** the Sovereign is absent; the signature is missing, malformed, or from an unanchored key; the displayed hash differs; any body field changes; the pending receipt is stale or cannot be matched; the node is duplicate or revoked; the trust anchor is empty/unknown; the gateway route or receipt is unavailable; or any verification step has `NO_DATA`. No fallback signer or rack-held key is allowed.

Proposed machine-readable causes include `sovereign_absent`, `signature_missing`, `signature_invalid`, `signer_not_anchored`, `cedula_hash_mismatch`, `pending_receipt_missing`, `pending_expired`, `node_conflict`, `issuer_revoked`, `receipt_unverified`, and `route_unavailable`. They are proposed vocabulary, not measured runtime responses.

## Review boundary

This ceremony design is a separate propose-only piece and requires its own `REQUIRES_FIRMA` review. Implementation requires separately reviewed app, rack-local ceremony interface, and private gateway/web pieces. Trust-anchor values and ceremony approvals require their own Sovereign ceremony. No key creation, key import, trust pin, database write, live endpoint request, deployment, or merge is included here.
