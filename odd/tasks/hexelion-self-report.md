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

## Rules (pinned in `test_self_report`, 15 tests)

- **An answer it cannot read is NO_DATA with its source's cause.** Today "doing" is always
  `NO_DATA(p2_mirror_not_built)`, and it never says a process is running.
- **"Achieved" counts only requests closed with their own contract's evidence** (ACTED, ANSWERED, LOCAL_SENSOR).
  REPLIED (a proposal) and unchecked answers are not achievements. Unchecked answers are listed under "check yourself".
- **"Needs from you: nothing now (measured)" only over measured zeros:** a fresh, fully read signature list and a
  task reading with `counters.state = MEASURED`. Known decisions with an unknown remainder read as "at least N …;
  others unknown (cause)".
- **A window is not a census** (Mesa #3 round 8, Cell A review). The task queue is counted only when
  `counters.state` is MEASURED (an attested complete reading, every row read). Otherwise "Doing" and "How" are
  NO_DATA with the counters' cause.
  - When rows are visible, they are said as "at least N task(s) visible; completeness NO_DATA (cause)".
  - With none visible, it is "no task visible", never "0 tasks".
  - A legacy projection with `state=MEASURED` but no `counters` is `counters_not_stated`.
- **The report's own turns are not work.**
- **The four answers always fit uncut** in `REPORT_TEXT_B` (480 B), including the longest wording (a partial window).
  The quoted last request gives way first, then the reference to it, then lists of message numbers become counts
  (the refs stay in `refs.turns`), then the standing "I never say a process is running".
- **The reply always fits the door's 1,023 B envelope** (found by walk step 12b: on a thread with earlier turns the
  reply measured 1,084 B with no turn at all, and Talk said "did not reply" while the thread held the report).
  - The door's existing rule: the turn gives way first (to state, cause and ref), never the answer.
  - Then the reply's copy of the evidence gives way to its `report_ref`. The thread keeps the whole evidence.
  - Talk then says "ACTED: the full sentence did not fit this reply; the Notebook shows it for request N".
  - The row keeps the person's question: the report's next step is "Read the four answers in the thread." (a report
    proposes nothing to merge), and its sentence is shorter.
- **Acho:** a report with any NO_DATA answer is drawn as missing evidence (`empty` → silent), never the success
  mark. The sentence names the NO_DATA answers.

## Measured

| | Before (`main` `18bf0d4`) | After |
|---|---|---|
| "What are you doing?" | an ordinary question to the model (no phrase, no reader) | local read, no model |
| `test_self_report` | 10/10 fail (2 fail, 8 error) | 15/15 pass |
| Round 8 fixtures on `747971d`: 12 visible done + a 13th unresolved; MEASURED without `counters`; positive control | 3/3 fail ("doing" MEASURED; "0 task(s) recorded") | 3/3 pass |
| Envelope fixtures on `20baf2e`: three firmas reads then the report; a report at its full budget | 2/2 fail (no turn in the reply; a 503 "outside the envelope") | 2/2 pass |
| Walk step 12b (headless Chrome, isolated server, temp home) | not present; on `20baf2e` FAIL ×2 (Talk: "did not reply") | PASS: Talk state + ref == JSON == Notebook sentence; Acho silent |

## NO_DATA

- **Harness:** the report is not shown there. It would be a second place for the same turn; proposed only if the
  Mesa wants it.
- **Live tasks:** `p2_mirror_not_built`.
- **Physical accessibility:** a screen reader in use, sound heard and a phone keyboard
  (`physical_accessibility_E2E_not_run`).
