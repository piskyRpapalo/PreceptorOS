# Harness · how verified preceptor capabilities are shown (presentation contract, proposal)

THE MARCH feature document · Claude Code (Opus 5.5) · 2026-11-13 · **docs only, propose-only**.
Extends PRECEPTOR-CAPABILITY-01 (Mesa #3, comments 6852189871 and the identity correction 6852467034) and the
existing missions A6 / B3. It does not open a new mission, catalog, router or dispatcher.

## Ownership (from PRECEPTOR-CAPABILITY-01, not changed here)

- **Codex CLI** owns the schema, probes, policy, receipts and negatives (`preceptoros.preceptor-capability/1`,
  provisional name). **Claude** only consumes those receipts to draw one card per preceptor, with the same words
  for eye, ear and machine. The frontend never discovers or infers a permission.
- The public coordinator that will read these contracts is the **mini-orchestrator**. Hexelion is the Sovereign's
  private rack coordinator and may be named only on private surfaces. Public strings, the manifest, onboarding and
  public APIs never say Hexelion.

## Measured starting point (2026-11-13, read-only)

| Fact | Source |
|---|---|
| No capability schema exists in the APP (`preceptor-capability`, `identity_assurance`, the three class names: 0 hits outside this doc) | `grep -rlE` over `*.py *.md *.js *.json` of APP `51298bc` |
| `GET /api/harness` reads only the Nexo timers (`127.0.0.1:8765/api/timers`), with `NO_DATA` + exception class on failure | `bin/preceptoros-pwa` `_harness_leer` |
| `team.py` (`preceptoros.team/1`) holds up to six **answer styles**, not identities, grants or tool access | `team.py:1-8`; Mesa 6852189871 |
| Native MCP S-3: 6 tools, allowlist `s3-2026-11-12`. A stdio handshake proves the transport, not who the actor is | Mesa 6854230572 |

## What a card may say (one card per preceptor)

Input: one receipt from Codex CLI's prober. Output: a card whose every claim cites a check in that receipt.

| Field on the card | Comes from | When absent |
|---|---|---|
| Name and role | `agent_id`, `role` (declared) | `NO_DATA(not_declared)` |
| Class: **Local CLI** / **Connected MCP** / **Public observer** | `interface_kind` | `NO_DATA(class_unknown)`; never guessed from the name or the provider |
| Who it is | `identity_assurance` ∈ DECLARED / OBSERVED / VERIFIED / NO_DATA, said in those words | NO_DATA |
| What it can do now | each `capability_checks[]` row with `state` = PASS, `mode` ∈ read / propose / write, `scope`, and `expires_at` in the future | not shown as a capability |
| What it claims but nobody checked | `capability_claims[]` with no matching passing check | listed under "Claimed, not verified" |
| Expired or failed | checks past `expires_at` or not PASS, with their `cause` | listed under "Not available: <cause>" |
| Cost and quota | `quotas/cost` | `NO_DATA(cost_not_measured)` |
| Receipt | `receipt_sha256` (12-hex prefix shown, full value in JSON) | the whole card is NO_DATA |

The classes are **transports, not a ladder**. A Connected MCP preceptor with no passing scope can do less than a
Public observer, and the card says so. The card never ranks preceptors or providers and never shows a global score.

### Never evidence (the card refuses these as sources)

- A `.md` manifest, `CLAUDE.md` or `AGENTS.md`: a declaration only.
- A `team.py` style card: an answer style.
- A `voz` declared on loopback.
- A tool that is present (`SENTINELX_HAS_TOOL`) without a scope check for this client.
- A login to one service standing in for API access to another.
- Model prose of any kind.

### Words, ear and machine (same rule as turns and tasks)

- Each card has one `reader` line: `<name>, <class>. Identity <assurance>. Can <read/propose/write list> until <time>.
  Not available: <causes>. Next: <step>.` The Notebook/Harness card text, its aria-live status, the Acho cue and the
  JSON carry the same line. Acho classes reuse `ok` (a passing, current scope), `needs_you` (expired, or consent
  missing) and `empty` (NO_DATA). Sound stays off until the person turns it on.
- The state is never shown by colour alone. Each state is a word plus a shape (`evidence_chip.js`).
- No button grants, connects, logs in or spends. A "check again" control may only ask the house prober to rerun
  an inert read probe, and only once a signed decision allows that probe.

## Proposed slices (each a draft HITL PR; none starts before Codex CLI's schema lands with its negatives)

1. **Fixtures + pure projector** (`capacidades_harness.py`, Node `projectCapabilities` in notebook.js). Three
   synthetic receipts, one per class, plus negatives: impersonation (manifest says VERIFIED, no check), expired
   scope, lost quota, a check for another client, a write claim without a write check, and a team.py style card
   fed as a receipt. Route `GET /api/harness/capacidades` returns `NO_DATA(capability_prober_not_built)`.
2. **Harness section "Preceptors"**: cards with aria-live and keyboard reach. Measured with the existing isolated
   browser walk (`tests/autonomia_a11y.browser.cjs`), contrast and focus included.
3. **Measured E2E** (Codex CLI's step two): 1 local CLI, 1 authorised MCP, 1 public reader, through the prober.
   Only then is a card ever drawn from live data.

## Open questions for the Mesa (lawful default in brackets)

- Final schema name and whether an equivalent already exists in LAB or the companion repo. [Wait for Codex CLI;
  no APP schema is invented.]
- How a card tells the author's signature, a connection attestation and the Sovereign's FIRMO apart. [The card shows
  only what the receipt attests and never shows a FIRMO.]
- Whether the mini-orchestrator's public Harness and the private rack Harness share the card code. [Shared pure
  projector, separate routes. The private instance may show private names only on private surfaces.]

## NO_DATA register

capability_prober_not_built · mcp_actor_authentication(not_measured) · provider_api_not_connected (per provider) ·
screen_reader_on_device(not_exercised) · cost_per_preceptor(not_measured).
