# Talk E2E · Hexelion answers the six questions (APP-TALK-E2E-01)

Commission: Sovereign 2026-11-13 «HEXELION · CLAUDE CODE · APP & RUNTIME», P0 «Hexelion real en Talk».
Mission: META-HARNESS-01 (APP #255). Owner: Claude Code (APP). Claim: Mesa #3 comment 6849005961.

## Explore

The chain `voice or text → Talk → Hexelion → authorised tool → result → receipt → Notebook` already existed for
three questions (#263 actions, #264 exact phrases, #265 Notebook mirror). Live check 2026-11-13 09:20Z on :8742
(main 2991684): «¿Cómo está el rack?», «What can you do?», «¿Qué has hecho?» → ACCION_LOCAL in 25–48 ms,
model not invoked, thread turns written, Notebook receipt `hexelion state DECLARED`.

The other three questions had no route, but each already had a producer:

| Question | Existing producer | Read through |
|---|---|---|
| What awaits my signature? | `bin/firmas-scraper` → `<casa>/firmas/pendientes.json` | same checks as `GET /api/firmas` |
| What results do we have from the Lab? | `lab_bench.py` → `<casa>/notebook/bench.json` | `notebook_read.read` (rechecks fingerprints) |
| Which preceptors are working? | `notebook/agents.json` (heartbeats) + `notebook/receipts.json` | `notebook_read.read` |

## Implement

- `hexelion_acciones`: `/firmas`, `/lab`, `/preceptores` (and English names) join the same grammar as LOCAL reads.
  No MCP, no model, no network, no new daemon. Exact phrases in es/en/pt name them. They take no arguments.
- A stale or missing source is said, never hidden: `signatures_stale` (> 30 min), `scraper_not_run`,
  `file_missing`, `agents_file_missing`. A STALE receipt never counts as «working».
- The door records `via: lectura_local` and the source file; the turn projection says «read from the rack's own
  records; no model ran».
- Talk «?» lists the three commands and phrases (buttons, keyboard reachable). Cache v173 (shell only).

## Check

Directed tests, sabotage and gate figures are in the PR receipt.

## Log

- 2026-11-13 · `preceptors` is NO_DATA on this rack: no producer writes `notebook/agents.json`. The heartbeat
  producer belongs to the CLI builders (Codex CLI, LAB/meta-harness). Not built here.
- 2026-11-13 · The native MCP audit records `state` but not `capabilities` or `audit_last` (live check). That
  server is p0x/Codex scope; reported, not changed.
- 2026-11-13 · Harness check G (`preceptoros-app-arnes`) measures the WEB /openworld/ chatbot, not APP Talk.
  APP Talk answered a free question in 22.2 s from a cold station model. G stays a WEB finding.
