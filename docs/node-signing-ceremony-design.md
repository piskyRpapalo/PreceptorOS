# Node issuer signing ceremony design

**Status:** proposal only; `REQUIERE_FIRMA`. This revision applies the Sovereign's registered rack custody ruling. No issuer key was generated, imported, or used; no trust anchor was pinned. Until the issuer key and manifest are pinned, a signed cédula remains pending and untrusted.

## Ruling and measured contracts

- One Sovereign issuer root signs both the trust manifest and node cédulas. The verifier must recognize the same public key for both signed objects, using distinct signature namespaces.
- The issuer private key is to be generated and held on the rack node. Only the Sovereign knows its passphrase. The key is used only by an explicit, local ceremony command while the Sovereign is physically present and consenting.
- The automatic rack declaration remains unsigned: `firma: null`. The issuer key must never enter its process, account, code path, service environment, or automatic invocation path.
- The Sovereign accepts the shared-machine risks: declarer and signer share one machine, server exposure can threaten the issuer root, and backup/recovery is mandatory.
- The existing rack declaration in `nodos.py:265-288` emits `firma: null` and `autenticidad: NO_DATA`. The device key helpers in `nodos.py:291-320` are for device intents, not this issuer root.
- The app verifier in `nodo_app.py:47-83` verifies `firma_ssh` with SSHSIG namespace `preceptoros-cedula`, identity `soberano`, and a local `allowed_signers` file. Its signed body excludes `sha256`, `firma_ssh`, `firma`, and `autenticidad` (`nodo_app.py:48-53`). The app does not sign.
- The selected registration transport is `POST https://api.preceptoros.org/api/v1/cedulas`. Route binding, receiver behavior, and anchor publication remain `NO_DATA` here; this document does not probe or invoke them. `/api/v1/paquetes` remains corrections-only by ruling.

## Intended flow and build order

1. **Phone prepares a pending cédula.** The phone collects node details, renders the canonical cédula and consequences, and records explicit local consent to submit it for rack ceremony. The phone has no issuer key and never signs. It submits to the selected apex endpoint. Until signed and anchored, its state is `pending/untrusted`, with cause such as `signature_missing` or `trust_anchor_missing`.
2. **Receiver queues the exact object.** The gateway validates shape and integrity, preserves the submitted canonical body and hash, and returns a receipt ID plus cédula hash. Receiver implementation and durable queue behavior are not measured; build and review this as a separate gateway piece.
3. **Sovereign conducts a local rack ceremony.** On the rack console, the Sovereign reviews the pending receipt, node identifier, canonical body, and hash. A dedicated ceremony command checks the exact pending object, prompts for the passphrase without echo, displays the consequences, and requires explicit confirmation. It signs only this object.
4. **Rack returns a signed result.** The ceremony command emits the original declaration, preserving `firma: null`, plus detached `firma_ssh` and its receipt linkage. It signs the exact body the app verifies, using `preceptoros-cedula`. It does not change the automatic `cedula()` path.
5. **Trust anchor is pinned.** A reviewed manifest, signed by the same issuer root under a distinct manifest namespace, binds the issuer fingerprint and manifest digest. The Sovereign pins the issuer key fingerprint and manifest digest through the separately approved web anchor ceremony. Until both pins are active and verified, the cédula remains pending/untrusted even if its signature verifies.
6. **Catalog admits the node.** The web catalog accepts only a valid cédula signature from the pinned root, matching node identity, exact receipt/hash, and current manifest. Catalog admission is a later web piece; its live behavior is `NO_DATA` here.

## Rack key custody and separation requirements

These are proposed controls, not implemented or measured controls.

- Generate one OpenSSH Ed25519 issuer key on the rack during an attended setup ceremony. Use an interactive local console and a dedicated issuer-only account and directory. No key generation occurs in this proposal.
- Store the private key encrypted at rest with a strong passphrase known only to the Sovereign. Prompt interactively for each signing operation. Do not put the passphrase or decrypted key in argv, environment variables, shell history, logs, an unattended agent, or a service process. Restrictive directory and file permissions are required; encrypt the underlying storage volume where supported as defense in depth.
- Keep the issuer account and key unreadable to the automatic node service account. Do not mount the key into that service, expose a signing socket, or configure a general-purpose SSH agent. The automatic declaration must run successfully without the key present or readable.
- Implement a separate ceremony-only executable, provisionally named `node-issuer ceremony-sign`. It accepts a pending receipt ID and expected hash; it must not be imported or called by `cedula()`, `estado()`, startup, cron, HTTP handlers, or any automated task. No HTTP endpoint may invoke it.
- Require a local interactive TTY, fresh passphrase entry, display of node ID/hash/consequences, and explicit confirmation. A TTY is a guardrail, not proof of physical presence; the human ceremony protocol supplies that assurance. Reject non-interactive and remote automation contexts where detectable.
- Keep `cedula()`'s code path and output unsigned. Demonstrate separation before release with a reviewed call graph and tests: execute automatic declaration as the service UID with the issuer key absent and present-but-unreadable; assert `firma` remains null and no key read or signer process occurs. Disable/remove the ceremony executable and show declaration still works. Conversely, ceremony tests must prove signing cannot proceed under the service UID or without an interactive confirmation.
- Signing necessarily exposes the decrypted key to the ceremony process briefly. The shared machine remains a single compromise boundary: a compromised rack, kernel, console, or ceremony process could capture the passphrase/key or produce signatures. These controls reduce accidental coupling; they cannot make a compromised host trustworthy.

## Identity binding, signature, and receipt

- The signed cédula body binds the canonical node identifier and declared node data. Sign the exact canonical UTF-8 JSON body expected by `nodo_app.py`; retain the existing cédula hash convention and verify it before signing.
- Put the SSHSIG in `firma_ssh`; preserve the declaration's `firma: null` field as required by the rack declaration contract. Use identity `soberano` and namespace `preceptoros-cedula` to match the current verifier. The manifest uses this same issuer key with a distinct namespace; the verifier and manifest format for that namespace need an explicit reviewed contract before implementation.
- The ceremony receipt records receipt ID, node identifier, cédula hash, issuer public-key fingerprint, signature namespace, ceremony time, and outcome. It contains no private material or passphrase. The Sovereign checks that the displayed and returned ID/hash/fingerprint match the ceremony screen and the pinned manifest.
- Receipt authenticity before anchor pinning is not trust. A cryptographically valid signature with a missing, mismatched, or unverified pin stays `pending/untrusted`; report the exact cause, never upgrade it by inference.

## Backup, recovery, and rotation

Backup and tested recovery are prerequisites to declaring the issuer ceremony operational. No backup is created by this proposal.

1. At key creation, make at least two encrypted offline backups of the same issuer private key on separate media stored separately. The Sovereign retains the passphrase separately; no rack account, service, or cloud backup receives it. The Sovereign chooses the physical custody locations in the anchor ceremony.
2. Validate each backup by restoring into an isolated, offline scratch environment and checking that its public fingerprint matches the issuer fingerprint in the reviewed manifest. Do not sign a real cédula during recovery testing. Record only success/failure, date, and fingerprint comparison result in a human-held receipt; never record the passphrase or private key.
3. If the rack dies, restore the same root from a validated backup onto a trusted replacement rack under an attended ceremony, re-establish permissions and separation, and verify the public fingerprint against the pinned manifest before signing. If no valid backup exists, the root is lost: stop signing and start a new root and anchor-rotation ceremony. Never silently generate a replacement under the old identity.
4. For planned rotation, generate a new root only in a separately approved ceremony. Require a transition manifest signed by the old root and proof of possession by the new root; review and pin the new fingerprint and manifest digest before using the new root. Define verifier overlap and old-root retirement in the anchor decision. Existing signatures remain historical evidence, not proof that the old key is currently trusted.
5. On suspected compromise, stop signing, isolate the rack, and treat the key as compromised. Revoke/replace it through an out-of-band Sovereign anchor ceremony; do not rely on the compromised rack to authorize its own replacement. A lost or compromised old root cannot authorize rotation by itself.

Recovery time, backup custody locations, verifier overlap, revocation semantics, and historical signature policy remain Sovereign decisions. The existing `firmar_rotacion` helper in `nodos.py:291-320` rotates device intent keys and does not implement issuer-root recovery.

## Anchor ceremony options still requiring a decision

The single issuer root is settled by ruling; these operational details remain open for the Sovereign's anchor ceremony:

- **Fingerprint comparison:** compare a short authentication string on the rack console against a separately displayed value on a trusted second device, or compare it with a signed/printed offline record. A second device is convenient but must not fetch its comparison value from the rack; a paper record is offline but needs secure custody and replacement handling.
- **Manifest digest pin:** show the full digest and a human-checkable grouped form; the Sovereign confirms both issuer fingerprint and manifest digest through the approved web governance action. A short display is easier to use but cannot replace checking the full value through an independent channel.
- **Backup custody:** choose two physically separate offline locations and a recovery witness/procedure. Convenient co-location improves access but leaves a common disaster risk; separation reduces that risk and complicates recovery.
- **Receipt channel:** choose a human-held offline ceremony record or a signed, privacy-minimal web receipt. Any web receipt must not be treated as an independent trust anchor merely because the same rack produced it.

No pinning channel, backup location, or receipt authenticity scheme is approved by this design.

## Valid, pending, and abort conditions

**Valid ceremony** requires all of the following:

- The Sovereign is physically present at the rack's local console and explicitly consents after seeing the node identity, canonical content, hash, and consequences.
- The ceremony process runs under the dedicated issuer account; key permissions and encryption are verified; the automatic service account cannot read or invoke the issuer key.
- A previously reviewed backup and recovery procedure has been exercised and the restored public fingerprint matches the intended issuer root.
- The passphrase is entered interactively by the Sovereign, the exact non-stale pending receipt ID/hash is verified, and the cédula body and node identity match the displayed request.
- The signature verifies under the same issuer root and expected cédula namespace; manifest signing uses the same root and its separately reviewed namespace.
- For trust/catalog admission, the issuer fingerprint and manifest digest are both pinned and independently verified. Until then the result is only signed-but-pending, never trusted.

**Abort without signing** if the Sovereign is absent or withdraws consent; invocation is automated, remote, or non-interactive; passphrase entry fails; the key is plaintext, broadly readable, mounted into the service, or fingerprint-mismatched; backup/recovery has not been validated; receipt/hash/body/node identity is stale, duplicated, malformed, or mismatched; or the signer/manifest namespace contract does not verify. Record a cause without secrets and leave the item pending or rejected as appropriate.

**Remain pending/untrusted** if the signature is absent or invalid, the receiver has not returned a verifiable receipt, either trust pin is missing, the manifest is unavailable or inconsistent, or the catalog cannot verify the anchored chain. Any unmeasured condition is `NO_DATA` with its cause; it is never a green result.

## Piece boundaries and review

- **Rack piece:** key custody controls, isolated ceremony executable, pending-object verification, signature and receipt. `REQUIRES_FIRMA` before any implementation or key generation.
- **Gateway piece:** bind and review `POST /api/v1/cedulas`, preserve exact pending object and receipt, and return signed status without treating it as trusted before pins. `REQUIRES_FIRMA` separately.
- **Web piece:** manifest publication, explicit pin ceremony, signature/identity verification, pending state, and catalog admission. `REQUIRES_FIRMA` separately.
- **Phone piece:** canonical preview, explicit local consent, submit pending cédula, and display pending/untrusted causes. It never signs. `REQUIRES_FIRMA` separately.
- **Sovereign ceremonies:** choose independent fingerprint/digest comparison, backup locations and recovery procedure, rotation/revocation policy, and approve each pin. Human decisions cannot be delegated to code.

This document revises the earlier “rack never holds the signing key” clause according to the newer registered ruling. The issuer root is now rack-held, while the automatic declaration remains unsigned. All controls above are design requirements; implementation, route reachability, physical ceremony behavior, backup validation, and anchor pinning are `NO_DATA` until separately measured and reviewed.
