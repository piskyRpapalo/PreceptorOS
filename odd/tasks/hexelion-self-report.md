# The four questions (APP-P3 · self-report)

THE MARCH feature document · Claude Code (Opus 5.5) · 2026-11-13. Cell A, round 7, CLAIM in Mesa #3
(#issuecomment-6866246151). Base: APP `main` `18bf0d4`. Not chained to the Acho PR.

**«What are you doing, what have you achieved, how do you know, what do you need from me?»**

## What exists and what was reused

- **One projection:** `turnos_hexelion.self_report`, next to `mcp_summary`, over three things:
  - the shared thread's turns (`turnos_hexelion.project`, the same as `GET /api/hexelion/turnos`);
  - the tasks reading the route serves (`tareas_hexelion.live`, which the route now calls too, so both read one
    source);
  - the signature list (`hexelion_acciones._firmas`, the same as `/firmas`).
- **One door:** `/informe` · `/report`, or a phrase («¿Qué estás haciendo?», "What do you need from me?", …) in three
  languages. It is a local read: no model and no MCP, like `/firmas` and `/lab`.
- **One turn:** the answer lands in the shared thread. Talk shows it. The Notebook row, the reader line and the JSON
  are that same turn: the state ACTED (the read ran under its contract), its four answer states, and `report_ref`
  (the sha256 of the report body) in the thread's machine layer.
- No engine, dashboard, route, served asset or agent state of its own.

## Rules (pinned in `test_self_report`, 10 tests)

- **An answer it cannot read is NO_DATA with its source's cause.** Today "doing" is always
  `NO_DATA(p2_mirror_not_built)`, and it never says a process is running.
- **"Achieved" counts only requests closed with their own contract's evidence** (ACTED, ANSWERED, LOCAL_SENSOR).
  REPLIED (a proposal) and unchecked answers are not achievements. Unchecked answers are listed under "check yourself".
- **"Needs from you: nothing now (measured)" only over measured zeros:** a fresh, fully read signature list and a
  task reading with `counters.state = MEASURED`. Known decisions with an unknown remainder read as "at least N …;
  others unknown (cause)".
- **The report's own turns are not work.**
- **The four answers always fit the chat envelope uncut** (560 B). The quoted last request gives way first.
- **Acho:** a report with any NO_DATA answer is drawn as missing evidence (`empty` → silent), never the success
  mark. The sentence names the NO_DATA answers.

## Measured

| | Before (`main` `18bf0d4`) | After |
|---|---|---|
| "What are you doing?" | an ordinary question to the model (no phrase, no reader) | local read, no model |
| `test_self_report` | 10/10 fail (2 fail, 8 error) | 10/10 pass |
| Walk step 12b (headless Chrome, isolated server, temp home) | not present | Talk == JSON == Notebook row; Acho silent |

## NO_DATA

- **Harness:** the report is not shown there. It would be a second place for the same turn; proposed only if the
  Mesa wants it.
- **Live tasks:** `p2_mirror_not_built`.
- **Physical accessibility:** a screen reader in use, sound heard and a phone keyboard
  (`physical_accessibility_E2E_not_run`).
