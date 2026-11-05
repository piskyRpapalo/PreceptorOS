# Native terminal · piece A3 — the chat (EMPUJE A CODEX)

Cookable card served to codex under the decree EMPUJE (buzon#30 ·6648984550). Contract:
`odd/tasks/native-terminal-visual-contract.md` (merged, pull 173). One piece, one PR; cook
after the anchor (A2) lands. Carril B (Hexelion's voice) mounts here: B1 consumes A3 as-is.

## Objective
One continuous conversation — no threads list (FUERA with cause, doctrine of both houses).
Streaming against `/api/orquestador` and the orquesta channel; activity rows collapse to one
line; ask-cards render INLINE when the agent asks — the HITL visible in silicon.

## Measured recipe
- Baseline: `main#dice` is the aria-live chat surface today over `form#escribir`; keep the
  live region contract intact (A11Y law: the screen reader hears every reply).
- Streaming: the reply paints as it arrives; the aria-live region announces the COMPLETE
  reply, not each chunk (chunk-by-chunk announcement is noise, measured as such).
- Activity collapsed: working states render as ONE line (today's activity rows), expandable
  on demand; never a wall of logs.
- Inline ask-cards: when the agent asks, the card renders in the conversation at that point;
  an OPEN ask-card is the only thing that turns the anchor amber (consumes A2's needs_you).

## Gates
- `./bin/pruebas` green; `test_pwa` when served files change; served sheet version bump if
  the cache moves. dashboard.js laws intact (it owns the language; it does not know new
  pieces exist — the A1 precedent of the inline module pattern).
- Receipts < 1,024 B with trailer; SCRUB; NO_DATA with cause; two passes, same seed.
- Propose-only; draft PR titled REQUIERE_FIRMA; FIRMA over the exact head.

## Checklist (stable IDs)
- [ ] A3-a: one conversation, streaming, aria-live announces the complete reply.
- [ ] A3-b: activity collapses to one line, expandable.
- [ ] A3-c: ask-cards render inline; an open card turns the anchor amber (A2 consumed).
- [ ] A3-d: nothing is submitted automatically; every send is the carbon's act.

## Log
- 2026-11-05: served to codex by mesa-web under the EMPUJE decree; cooking order A1→A4.

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA
