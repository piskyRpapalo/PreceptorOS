# No zero is tranquillity (APP-P0-TRUTH)

THE MARCH feature document · Claude Code (Opus 5.5) · 2026-11-13. Cell A, round 6, CLAIM in Mesa #3
(#issuecomment-6865305579). Base: APP `main` `60064d7` (#292 merged). Delivered under the autonomy-parity mission.

## The defect (measured on `60064d7`)

`tareas_hexelion.project` serialised `needs_you=0, blocks_new_work=0, decisions_for_you=0` for readings in which no
zero was observed. Talk then hid its task line, which tells the ear the same thing: nothing needs you.

These readings never observed a zero:
- an absent source;
- an unreadable list;
- an empty reading nobody attested;
- a window that cut tasks off;
- unreadable rows;
- uncertain rows whose projection could not be used;
- an acknowledgement whose authority is unverified.

The signature reader had the same fault: a day-old empty list said "STALE: Nothing waits for your signature now."

## The rule

- **A positive count is what was seen:** at least that many.
- **A zero is said only when `counters.state` is MEASURED.** That needs the host's completeness witness
  (`complete_ref`, hex64) for the reading, no records beyond the window, every row readable, and every uncertain row's
  projection usable.
- **Otherwise the zero is null.** `counters` = `{state: NO_DATA, cause, complete_ref: null, known_counts_are: at_least}`.
- Causes, most specific first: the source's own cause, `records_beyond_window`, `rows_unreadable`,
  `uncertainty_unread`, `completeness_not_attested`. An empty unattested reading is `no_task_in_this_reading`;
  the old wording, "no task recorded", read as a clear.
- An acknowledgement the host cannot verify (`AUTHORITY_NOT_VERIFIED`) is a decision still yours. It is counted in
  the JSON and said as "Decision for you" by the eye.
- **One cause everywhere.** JSON, the MCP summary (`counters` travels with the counts) and the Notebook status (the
  reader text) all carry it, and Talk says it in the same words. Talk is quiet only over a measured zero; a failed
  reading is said there too.
- **A newer reading always wins.** A reading that started earlier never repaints over one that started later. The walk
  found this race once Talk stopped hiding its line.
- **Signatures:** a stale or partly unreadable list says "I cannot confirm that your signature list is empty"
  (`signatures_rows_unreadable` for the second case).
- **No host supplies a completeness witness yet.** The live route stays `NO_DATA(p2_mirror_not_built)`, and APP never
  makes a witness up. `complete_ref` is APP's proposed consumer field. Codex CLI / the host decide whether and how
  the mirror attests a complete reading (handoff).

## Measurements (`scratchpad/p0_baseline.py`; base vs this head; same 9 machine fixtures plus a lost reading)

| Metric | Before | After |
|---|---|---|
| Unobserved zeros in the machine JSON (27 counters) | 25 | 0 |
| Talk silent without a measured zero (10 readings) | 8 | 0 |
| Signature list saying "nothing waits" while stale or partly unread | 2/2 | 0/2 |
| `test_false_clear` (16 tests) | 0/11 pass (first 11; 9 error on the new parameter, 2 fail on wording) | 16/16 |
| Older reading repainting a newer one (client test) | yes (Talk and Notebook, 0 rows) | no |
| Measured zero still said, Talk quiet | not reachable | yes (positive fixture) |

Walk (headless Chrome, isolated server), step 10b on the live route: counters null, `counters.cause`
p2_mirror_not_built, Talk == Notebook status, polite, no clear words.

## Still NO_DATA

- A host completeness witness (no producer).
- Acho has no expression for the summary line: rows keep their own class, and nothing new was built.
- A screen reader in use, sound heard, a phone keyboard.
