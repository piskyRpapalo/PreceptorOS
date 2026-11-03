# Existing identities and the aula boundary · body phase 1.1

## Explore

Reading depth: identity creation/signing, visitor lifecycle, app account and
entry verification, companion architecture, and the aula account summary.
No whole-repository security review or browser/device measurement is claimed.
Authority: Sovereign backend commission, 2026-11-03; single firmas book and
DECISIONES_MAIN consulted. Alignment: roadmap/NORTE.md §§1–4, ROADMAP.md
DESTINO; the body phases are a separate implementation sequence.

Sources pinned for review:

- Web 72d99b3c0b20aa2bbd4004f2ac32894fc2604997:
  `public/game/visitor_account.js:6–32`, `visitor_play.js:7,31`,
  `visitor_eggs.js:24–49`; separate persistent identity in
  `public/assets/auth.js:107–175`.
- App 0900d858081eb4679b209e7b1b70c81dc88913e1:
  `cuenta_cangrejo.py:35–57,109–198`, `customs_agente.py:52–80`,
  `odd/tasks/external-sign-channel.md`.
- Companion `GROUNDTRUTH.md`, blob e280f9dce75de125c5d455e53805961800471afc;
  README blob 79257689db2afbaefd57282a6b713f5746c2b80b.

## Implement · one identity crosswalk

| Existing piece | Identity/evidence | Role in the joined flow |
|---|---|---|
| Web ephemeral cangrejo | Raw Ed25519 public key, derived visit seed/pseudonym | The visitor principal; preserve it |
| Persistent web Identity | Separate IndexedDB CryptoKey pair | Existing separate lifecycle; never silently replace the visitor |
| PreceptorOS app | Executable door and local verifiers | Verify visitor evidence, host terms and consent before access |
| App cuenta-cangrejo helper | SSH-format key fingerprint and SSHSIG account authorization | Existing app contract, not evidence of browser compatibility |
| Fleet node identity | Provisioned canonical public node ID | Host/node identity, not a visitor or an aula login |
| Aula restricted login | Revocable technical access associated with verified visitor evidence | Access handle, never a new sovereign principal |
| Aula admin | Existing administrative account | MANOS configuration only; cannot represent a visitor |
| preceptoros-companion | Docs-only declarations and host conditions | Architectural record; no executable app |

The ephemeral private key is generated on-device with extractable=false,
held by the page closure, and dropped on end/pagehide. Public key export is
expected; non-extractability does not prevent same-origin code from invoking
the signer while the visit is active. There is no claim of hardware custody.
The account requires explicit creation/signing consent, exact fields, matching
public key, and a frame below 1,024 bytes. Adopted records can persist without
restoring signing authority. Returning to a page creates a fresh visit.

Important compatibility boundary: visitor_account.sign currently accepts only
atlas.invocacion/2 and atlas.adopcion/1. Its transition method explicitly
returns NO_DATA. It cannot sign an arbitrary aula challenge. The app helper
hashes an SSH public-key text representation and verifies SSHSIG namespaces;
that is not the browser's raw-key representation or signature format. Similar
hexadecimal lengths are not an identity join. Do not call generar_par, create
another principal, export a private key, or wrap a browser signature as SSHSIG.

## Proposed join · before enabling access

1. Keep the visitor's existing raw public key as the subject. The host app
   presents its conditions with a stable content digest, scope, destination,
   expiry and revocation policy; no credential is offered beforehand.
2. Adapt the closed atlas.sobre/1 and atlas.paquete_mp/1 contracts in a reviewed
   slice. Establish the permitted signed payload and exact canonical bytes,
   host/audience binding, nonce, session, expiry and durable replay rejection.
   The current visitor allowlist and app verifier do not yet implement this.
   No new ad-hoc public REST ingress or silent signing fallback is proposed.
3. Verify the browser Ed25519 signature and host terms acceptance on the APP
   side. Consent must name the exact scope and payload; a recognized phrase,
   pseudonym or hash alone never proves signature or authorization.
4. Only after a measured binding exists, MANOS may associate the restricted
   aula access handle with that subject and scope. Keep its revocable API key
   separate from the visitor signing key and outside browser/model context.
   Transport to aula goes through the app; the visitor never calls Ollama.
5. Persist only the necessary public binding/replay/revocation evidence. End
   of visit, expiry, withdrawal or human STOP denies further access. Explicit
   revocation disables the technical credential as well as the app session.
   Another model's response cannot extend any grant.

No aula user is created by this audit. The existing admin is retained.
The signed payload adaptation is a construction question recorded here, not
an authorization inferred from older coverage. D2 authority/enrollment belongs
in firmas; this crosswalk is neither a signing book nor a signature.

## Check and remaining evidence

2026-11-03, local app checkout at the head above: directed existing account
tests are recorded in the receipt. These synthetic cases check app record
shape only; they do not demonstrate a browser→APP→aula join. Source inspection
establishes the lifecycle/format boundaries, not physical-device behavior.

Read-only aula observation: Open WebUI 0.11.1, one admin, no non-admin account,
no groups/access grants. This proves no existing restricted aula login in that
database snapshot, not the absence of every external identity provider.

Required future cases: raw-key/signature mismatch, altered terms/destination,
no consent, expired/replayed challenge, lost page, concurrent replay, persisted
revocation across restart, direct foreign-model 403, and valid authorized LoRA
completion. None is reported PASS by this document. Operational identity join,
typed payload adaptation and physical browser behavior remain NO_DATA.
J-* mapping: NO_DATA, no specific code established for this slice.
