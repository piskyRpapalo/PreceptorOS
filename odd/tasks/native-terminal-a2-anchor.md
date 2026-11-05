# Native terminal · piece A2 — the anchor (EMPUJE A CODEX)

Cookable card served to codex under the decree EMPUJE (buzon#30 ·6648984550). Contract:
`odd/tasks/native-terminal-visual-contract.md` (merged, pull 173). One piece, one PR, in order
A1→A4; do not cook this until the panel (A1) has landed.

## Objective
Replace the current anchor (the marble bust with the lit eye) with the node glyph the carbon
sentences at FIRMA. Candidates declared by the contract: la boya (the State Buoy, ideas13oct ·
LOS 9 OBJETOS) · el faro (the lighthouse, atlas/faro.py) · el hexágono (the HEX at {0,0}, the
map's own seat). The carbon chooses; silicon ships the chosen one.

## Measured recipe
- Reference (never pasted): a 72pt window around a 66pt glyph; only dashoffset, opacity and
  filter animate; reduce-motion respected. Re-derive in OUR tree, mobile first.
- States: idle · thinking · working · needs_you (amber `#f5a524` + badge = a FIRMO pending of
  the carbon) · starting · error. Needs_you is the ONLY amber; the badge is the HITL made
  visible (never color alone — aria-label carries the state).
- Paint with the A1 tokens (`--acento`, the dark family) — the anchor inherits the node's
  accent, it does not hardcode colors.
- The bust stays until this piece lands; nothing is removed before.

## Gates
- `./bin/pruebas` green on CI (ten runs); `python3 -m unittest test_pwa` when served files
  change; version bump of the served sheet if the cache must move.
- Receipts < 1,024 B UTF-8 with trailer; SCRUB; NO_DATA with cause; two passes, same seed.
- Propose-only; draft PR titled REQUIERE_FIRMA; FIRMA over the exact head.

## Checklist (stable IDs)
- [ ] A2-a: the glyph is drawn in bubble language from the tree's own values (no imported asset).
- [ ] A2-b: the six states render and announce (aria), needs_you amber + badge only.
- [ ] A2-c: reduce-motion leaves nothing moving when the user asks for none.
- [ ] A2-d: FPS on the reference device measured by the carbon, or NO_DATA with cause.

## Log
- 2026-11-05: served to codex by mesa-web under the EMPUJE decree; cooking order A1→A4.

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA

## Commission · Codex · 2026-11-05

### Problem
The app dashboard still exposes a marble bust as its visual anchor; the commissioned
native terminal calls for a node glyph with accessible, truthful status.

### Outcome
A reviewable hexagonal node anchor uses the existing accent and reports only states
supported by evidence. Six display states, keyboard and screen-reader accessibility,
and reduced-motion behavior must be demonstrable without inventing live activity.

### Affects
The existing app dashboard, its anchor styling and state bindings, and corresponding
service-worker delivery. Claim: buzon#53 ·6652132076.

### Constraints
One piece and one draft PR; preserve existing chat and node behavior; no external
assets, telemetry, or unmeasured runtime claims. Report physical-device FPS as
NO_DATA until measured. Mesa assigns any required seal; silicon does not merge.

### Open questions
Which existing runtime events support each of the six states? Which state should
be presented while there is no authoritative status source? Inspect before binding;
use NO_DATA for missing evidence.

Decision: the Sovereign delegated routine decisions and requested a hexagonal app
esthetic. The hexagon from the signed A2 candidate list is the proposed anchor.

2026-11-05 · Candidate: inline hexagonal SVG replaces the hidden legacy bust
in the dashboard. Existing chat submission reports pending and error through a
visible live status; idle does not claim a model is running. No animation or
external graphics. Local `python3 -m unittest test_pwa`: 66 passed;
`python3 -m unittest test_guardrails`: 38 passed, 1 skipped. Remaining:
localization of the initial status, independent accessibility review, authoritative
sources for the other states, physical FPS, and Mesa-assigned service-worker seal.
This candidate is incomplete and not ready for deployment or signature.
