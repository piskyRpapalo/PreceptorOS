# Native terminal · piece A4 — the composer (EMPUJE A CODEX)

Cookable card served to codex under the decree EMPUJE (buzon#30 ·6648984550). Contract:
`odd/tasks/native-terminal-visual-contract.md` (merged, pull 173). One piece, one PR; cook
after the chat (A3) lands. Parakeet local voice and attachments: PROPOSAL after this, not
today.

## Objective
The composer becomes multiline with an honest stop and a mic that shows a PARTIAL transcript
FOR REVIEW before anything is sent. Nothing is submitted automatically — the a11y law stands.

## Measured recipe
- Baseline: today's input is single-line, maxlength 280, with a dictation toggle («Dictado
  apagado»); the browser-side partial dictation is NO_DATA with cause at the contract's
  pinned head (no browser bridge measured). Voice modules exist locally (`oido.py`,
  `voz.py`, `tono.py`, `canales.py`).
- Multiline: Enter sends, Shift+Enter newlines; the maxlength law of the channel stays
  measured and declared.
- Stop: while the orchestrator works, the stop aborts the run; a NEW message steers the
  run, never queues silently (steering is doctrine).
- Mic: the transcript lands in the input for review; the send stays the carbon's act.

## Gates
- `./bin/pruebas` green; `test_pwa` when served files change; served sheet version bump if
  the cache moves. `interface/` vocabulary laws intact (no rule-id-like marks, no unnamed
  policy words — the guardrails of the A1 cure).
- Receipts < 1,024 B with trailer; SCRUB; NO_DATA with cause; two passes, same seed.
- Propose-only; draft PR titled REQUIERE_FIRMA; FIRMA over the exact head.

## Checklist (stable IDs)
- [ ] A4-a: multiline composer, Enter sends, Shift+Enter newlines, maxlength declared.
- [ ] A4-b: Stop aborts; a new message steers the run.
- [ ] A4-c: mic partial transcript lands for review; nothing auto-submits.
- [ ] A4-d: keyboard reach on every control; screen reader announces states.

## Log
- 2026-11-05: served to codex by mesa-web under the EMPUJE decree; cooking order A1→A4.

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA
