# Acho is the flag of verifiable truth (APP-P1-ACHO)

THE MARCH feature document · Claude Code (Opus 5.5) · 2026-11-13. Cell A, round 6, CLAIM in Mesa #3
(#issuecomment-6865305579). Base: APP `main` `60064d7`. Independent of the P0 PR (not chained).

## The defect (measured on `60064d7`)

- **A simulated task looked verified.** Its receipt basis was `synthetic`; it passed its check, and its words said
  "Simulated run". It still had class `ok`, so Acho drew `verified` (double line, ok tone, moving) and the cue took
  the MEASURED motif. Eye and ear told a success the evidence does not support.
- **An unchecked reply looked like a success.** A turn REPLIED (another voice's own words, checked by nobody here)
  was class `ok`: the ok-toned, moving `answer` expression and the MEASURED motif.

## The rule

**SIMULATED != VERIFIED.**
- The success class (`ok`) needs MEASURED evidence.
- A proposal or simulation is the new class `proposed`, added to the existing closed tables:
  - `audio_feedback.ACHO_CLASSES`: degree 3, PROPOSED motif;
  - `acho_motion` expression `proposed`: `ask_me` form, dashed line, quiet, still;
  - the class lists in `notebook.js` and `acho_sonido.js`.
- A claim whose evidence cannot be named is silence (`empty`).
- No new framework, backend or speech service. The class is decided with the sentence on the server, as before.

| Fact | Class | Expression (form · line · tone · moves) | Motif |
|---|---|---|---|
| Verified (MEASURED evidence, check passed) | ok | easy · double · ok · yes | degree 0 · MEASURED |
| Proposed or simulated | proposed | ask_me · dashed · quiet · no | degree 3 · PROPOSED |
| Missing evidence | empty | key_points · dotted · quiet · no | degree 3 · NO_DATA |
| Unknown outcome | uncertain | free · dashed · warn · no | degree 4 · PROPOSED (vibrato) |
| Human intervention required | needs_you | steps · solid · warn · yes | degree 2 · PROPOSED |
| Rejected or unsafe | exec_fail / fence | tips · solid · stop · yes | degree 3 or 2 · STALE |

Every pair differs in form and line, in words, and in motif, so nothing depends on colour. Sound stays off until the
person turns it on. Reduced motion changes the shape without movement. A Web Audio failure is NO_DATA and silent.
The words are always on screen and in the reader line.

## Measurements

`test_acho_truth`, against the base:
- adversarial rows reaching the success class: 1 of 12 before (the simulated passed check; the other shapes were
  already not `ok`), 0 after;
- REPLIED reaching `ok`: before yes, after no.

- `test_acho_truth` on the base code: 7 of 8 fail (the one that passes pins MEASURED evidence reaching `ok`); 8/8
  after.

Expression and motif uniqueness are pinned. Walk step 11b renders both marks in headless Chrome: proposed (dashed,
quiet) and verified differ in their drawn line. A screen reader in use and sound heard stay
NO_DATA.

## STUDY-MATH-GAP-01 · display and parity contract (proposal, no code, no endpoint)

Cell B's 32-case study needs a way to *show* a LAB result. This maps it onto fields APP already serialises: a task row
of `preceptoros.hexelion-tasks/1`, plus the projection's `limits`. Nothing new is served.

| Study field | Existing field | Rule |
|---|---|---|
| state | `state` (closed table) and `acho.class` | MEASURED evidence + oracle accepts → DONE_CHECKED / ok. Simulated or model-only → `proposed`. Abstain or invalid input → NO_DATA with cause. |
| cause | `cause` (snake_case, ≤ 64) | LAB's own code: `MULTIPLE_ELIGIBLE_REQUIRES_HOST_CHOICE` → `multiple_eligible_requires_host_choice`; `leakage_unverified`; `oracle_rejects`. |
| evidence_ref | `evidence {origin, ref}` | origin from LAB's `confidence_basis`: `synthetic` → SIMULATED. Oracle or receipt sha256 as `ref`. No ref → NO_DATA. |
| limits | projection `limits` + row `next` | What the result does not prove: no dispatch, no grant, no extrapolation beyond the 32 cases. |
| human_action | `next` (and `needs_you` / `decisions_for_you`) | Example: "Several options; nobody ran the task; choose one on the host." `dispatch_authorized` stays false. |

Worked example (B's): two eligible nodes give LAB `ABSTAIN(MULTIPLE_ELIGIBLE_REQUIRES_HOST_CHOICE)`.
- APP shows NO_DATA with that cause, class `needs_you`, and the words "several options; nobody has run the task; an
  authorised choice is missing".
- The JSON keeps `dispatch_authorized: false`. Acho shows caution, never `verified`.

A mathematically correct answer from a model with no oracle receipt is `proposed`, never `ok`.

The model comparison has not been run: `NO_DATA(Hexelion_math_E2E_benchmark_not_run)`.
