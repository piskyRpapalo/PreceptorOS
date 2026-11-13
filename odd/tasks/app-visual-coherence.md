# App visual coherence · one truth, nine panels (VISUAL-COHERENCE)

THE MARCH feature document · Claude Code (Opus 5.5) · 2026-11-13. This document describes a delivery within the
existing missions A6/B3 (the PLAN-02 design round). It is not a new mission.
Rule: **one fact, one home.** Every panel shares the same state and references, but adds only what fits its own job.
No two live regions speak the same event.

## Responsibility matrix (nine panels + Acho)

| Panel | Owns (its job) | Shows of others | Never repeats | Announces (aria-live) |
|---|---|---|---|---|
| Command | where you are, the compass, where to go next | one line per panel | panel contents | compass notice only |
| Talk | the conversation, actions, the immediate answer | `#talk-tasks` only when something waits on you or the host | history beyond the thread, receipts | `#estado` turn line once; `#hilo` new messages once (thread copies of drafts arrive quietly) |
| Boundary | limits, authorisations, safety decisions (HITL) | — | turn or task wording | its own decision status |
| Notebook | history: requests and answers, delegated tasks, receipts, references, sequence | — | measured runs (points to Lab) | one status per section, only when its words change |
| Lab | measurements, experiments, results (benchmarks, rack readings) | — | requests and answers (points to Notebook) | one status per section, only on change |
| Harness | verified capabilities and connections (loops, preceptor cards per #278) | — | conversation, turns | freshness of its own reading |
| 3DFabrika | creating, reviewing, preparing to print | — | — | its own step line |
| World | the public OpenWorld view | — | private state | connection line |
| Settings | this device: privacy, energy reading, sound, voice, node identity | — | panel contents | each control's own result |
| Acho (cross-cutting) | the state as shape, motion and sound, derived from the same turn or task class | — | it is never a source: no class without a sentence | sound off until turned on |

## Measured and fixed in this piece

The walk runs in headless Chrome against its own server (temporary HOME, fake MCP, no model), never the live service.

1. **One turn, three announcers.** Before: your message and the reply each entered the live log twice (the window's
   draft, then the thread's copy), and `#conv-destinos` was rewritten three times with the same words. After:
   `hilo, hilo, estado, hilo`, which is your message, "thinking…", the turn line and the reply, each once
   (walk step 12; it fails on the parent branch).
2. **A contradiction on load.** With no memory file, `/api/estado` dropped the connection
   (`sqlite3.OperationalError`), so the header said "cannot reach the server" while every panel read fine from it.
   Now the server returns `NO_DATA(memory_db_unavailable_*)` and the header says that cause.
3. **Same view in two panels.** Lab "Last request to Hexelion" was the Notebook's latest request, and the Notebook
   "Benchmarks" were Lab's runs, painted by the same loader. Each now has one home, and the other panel has a
   one-line, non-live pointer.
4. **The same sentence twice.** An empty section showed its status line and also a NO_DATA card repeating that
   sentence under the heading again. The card is gone; the status line says it once.
5. **Spanish in the English app.** The first paint showed «comprobando…» and «Zona activa: Hablar.». The channel
   cause «el canal aún no tiene mensajes» reached four panels, and the creation-publish block was in Spanish.
   Now the first paint is English and the channel causes are codes (`channel_has_no_messages`,
   `channel_unreadable_<Error>`). Walk step 13 asserts that no Spanish prose is visible in any panel. `canal:<thread>`
   is `lab.py`'s source identifier: it is data, not prose.
6. **A tab announced twice.** A focused tab is already spoken by the screen reader. The zone line now speaks only
   when the zone changed some other way: a link, a swipe or the address.

## Inconsistencies not yet measured or fixed (each with its proposed control)

| Finding | Proposed control | Piece |
|---|---|---|
| Harness "Agent questions to Hexelion" is history (the cli thread) | move it to the Notebook as a filter of requests | PANEL-FLOW (needs review: the CLI-thread decree) |
| The Notebook heading reads "Notebook · Hexelion" in a public product (Hexelion is the private coordinator) | public build says Notebook; private instance only | naming review |
| Dark scheme is not offered (light only) | NO_DATA until designed; contrast measured per scheme | PANEL-FLOW |
| What a screen reader actually speaks | NO_DATA until Orca/TalkBack runs in an authorised environment | ACCESSIBILITY-PROOF |

## ACHO-EXPRESSION (delivered after VISUAL-COHERENCE)

- **Uncertainty has its own class: `uncertain`.** A claim that may have run is neither a failure (`exec_fail`) nor a
  silence (`empty`). It is used by `OUTCOME_UNKNOWN`, `NO_RESULT_RECORDED` (tasks) and `ACTION_UNVERIFIED` (turns),
  whatever the host acknowledged. Its sound is distinct: the highest degree with vibrato (`audio_feedback`). Sound
  stays off until the person turns it on.
- **One mark beside Talk's status line** (`#acho-estado`, `aria-hidden`: the words are already in `#estado`), drawn
  by `acho_motion.express` from the turn's own class and state. Seven expressions, each with its own form plus line
  (solid, double, dashed or dotted), so they read without colour and in forced colours: waiting, answer, verified,
  needs you, uncertain, refused, silent.
- **Nothing moves without evidence.** Waiting, uncertain and silent never move. The others move once, on change
  only. Reduced motion changes the shape without moving. Measured in walk step 14: waiting 0, uncertain 0,
  verified 1, verified again 0 animations. With reduced motion, 0 running.
- **Notebook cards carry the same line pattern** on their start edge. Uncertain is dashed, and the walk measures it
  on the real DOM.
- Not measured: the tone heard on a speaker (NO_DATA, Web Audio graph only) and what a screen reader says (NO_DATA).

## PANEL-FLOW (delivered after ACHO-EXPRESSION)

- **One voice per reading.** While a reading panel loads (opening it or pressing ↻), its section lines keep painting,
  visible and readable in place, but stay quiet. When the reading settles, the panel's own line speaks once
  (Notebook `notebook-status`, Lab `lab-estado`, Harness `harness-frescura`, Settings `ajustes-estado`). Later changes,
  such as a new task or a control just used, speak as before. Settings keeps one live line per control, and a line
  speaks only when its control is used.
- Measured in walk step 15, reopening each panel in headless Chrome. Before: Notebook 3, Lab 4 (the same "Checking the
  local Lab…" from two regions at once), Harness 2, Settings 4. After: 1 each. The other five panels: 0–1, unchanged.
- **Focus stays.** The Notebook's ↻ is marked busy (`aria-disabled`) instead of disabled, because a disabled button
  drops the keyboard focus to the page. It also runs through the same panel flow. After a refresh, focus is on the
  button in all four reading panels. The before state is NO_DATA: the old walk did not reach that button.
- English first paint for the Lab and Harness reading lines; " · Bucles:" became " · loops:".
- Arrows, Home and End are unchanged (walk step 7).

## Levels kept apart

DOM inspection (measured, headless Chrome) ≠ a screen reader in use (NO_DATA) · Web Audio graph ran ≠ sound heard
(NO_DATA) · synthetic tool (SIMULATED) ≠ live service (not touched).
