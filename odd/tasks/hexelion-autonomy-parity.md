# Hexelion autonomy parity · one event, one sentence (HEXELION-PLAN-02 · P3)

Commission: Sovereign 2026-11-13 «HEXELION · CLAUDE CODE · PLAN-02». Coordinator: Codex GPT-6 Web.
Lane: AUTONOMY-PLAN-02 §P3 (private Mesa PR #22) — visual / audio / machine parity. Owner: Claude Code (APP).
Missions reused, no new ID: A1/A3/A6/A8, B3/B4/B8, C8/F7 (private Mesa index).
Private Hexelion only. The public mini-orchestrator (`orquestador.py`, `audio_feedback.project`) is out of scope.

## Explore · measured 2026-11-13, rack p0x, read-only, APP main `f01ed25`

| # | Fact | Source |
|---|---|---|
| F1 | Native MCP: the live server file equals its `.bak-20261113` byte for byte (same SHA-256); its mtime is one minute after Grok's 8-tool install receipt; its `TOOLS` list has 6 entries; no `mcp_project_tools.py` in the home tree (depth 4). Live state = 6 tools. | `sha256sum`, `stat`, `grep -n TOOLS` |
| F1′ | Who restored the file, and whether 8 tools ever answered a client: NO_DATA(no_audit_of_file_restore). | — |
| F2 | `turnos_hexelion.py` already gives one `sentence` / `next` / `reader` per request (`preceptoros.hexelion-turns/1`); Notebook and Lab read it through `GET /api/hexelion/turnos`. | `turnos_hexelion.py:70-145`, `interface/notebook.js:178-255` |
| F3 | Talk does not read that projection: after `POST /api/hexelion/chat` it words the action itself (`done` / `refused or failed`). Same event, two wordings. | `interface/app.js:957-963` |
| F4 | `_close` says ACTED when `maquina.ok is True`, without looking at `rc`: `ok:true, rc:null` or `rc:1` would be told as success. | `turnos_hexelion.py:83-87` |
| F5 | No turn → audio path: `audio_feedback.py` projects only public orchestrator verbs; speech lives in `interface/native_voice.js`; `acho_motion.js` keeps Acho at NO_DATA. | code |
| F6 | Grok #20: `acho_from_action` uses `bool(r.get("ok"))` (string `"false"` → True); `mcp_receipt` sets `ok` when `rc in (0, None)`. | private Mesa main, `tools/` |
| F7 | Grok #20 `pending_queue.make_item`: the ID hashes `ts` and `status`, so the same task gets a new ID each time. | private Mesa main, `tools/pending_queue.py` |
| F8 | A fake native MCP fixture already exists for tests (`fake_s3.py` in a temp dir). | `test_hexelion_acciones.py:72-90` |

## Contracts (proposals; nothing here grants anything)

**One visible history, not the recovery store** (Sovereign correction, 2026-11-13). The shared thread (`canales`,
threads `orquesta` / `cli`) is the visible, auditable history every surface reads. It is not proof that a task can be
recovered: which store keeps pending tasks across a restart, bounds retries and prevents a second execution is for
Codex CLI to measure and choose (H3). That store mirrors each transition into the thread, so the surfaces can tell it;
a reader never treats the thread as the queue. **One judge.** `turnos_hexelion` is the only place a state
and its sentence are decided; Talk, Notebook, Lab, screen reader, Acho and machine JSON copy, never re-word.
**One door for authority.** A grant is the Sovereign's message through the person door (voice `soberano`); a
model, agent or replied message can never make one.

**C-TURN · `preceptoros.hexelion-turns/2`** (superset of /1): per turn `state, cause, sentence, next, reader,
evidence, author, asked_by, task{id, attempt, grant_ref} | null, acho{class, tone}`; each turn ≤ 1,024 B UTF-8.
Lifecycle states added to /1: AWAITING_GRANT · AUTHORIZED · VERIFIED (only with an independent `check_ref`) ·
INTERRUPTED (no completion receipt after the attempt's TTL; never «running») · RESUMED · EXPIRED_GRANT.
ACTED only when the tool's own contract confirms it (Sovereign correction, 2026-11-13: never `ok: true` alone, and
not `rc = 0` for every tool). Measured contracts: `exec` → `rc` is the integer 0; `write_file` → bytes written +
SHA-256, no rc; `state` → services read; `capabilities` → allowlist version; `audit_last` → `n` equal to the rows
read; local reads → the source file read. Missing proof, a contradiction or a tool with no contract is
ACTION_UNVERIFIED with its cause; a no from the fence or the tool stays ACTION_REFUSED.

**C-TASK · handoff to P2 (Codex CLI / Hexelion own it).** Machine fields a queue writes into the thread:
`task_id` (stable: hash of normalised intent + scope, never time or status), `attempt`, `grant_ref` (thread n of the
grant), `grant_version`, `ttl_s`, `transition` (created · authorized · started · completed · failed · resumed ·
expired), `check_ref`. The durable store itself is theirs to verify: survives a restart, recovers pending tasks,
bounds retries, executes a task at most once. Until measured: NO_DATA(recovery_store_not_verified). The projection
only reads the mirrored transitions.

**C-ACHO.** Class ∈ {ok, fence, exec_fail, bridge_down, empty, help, waiting}, derived from the turn's state; the
spoken text is the turn's `reader`. Grok's corrected `acho_from_action` becomes a cross-check test, not a second mapper.

## Slices (one PR each, draft, title `HITL`)

| Slice | Waits for | Files | Result |
|---|---|---|---|
| S0 | — | this document | contracts and handoffs on record |
| S1 | S0 | `turnos_hexelion.py`, `hexelion_acciones.py` (`evidencia`), `bin/preceptoros-pwa` (door records it), `interface/notebook.js`, versions, tests | F4 closed per tool: ACTION_UNVERIFIED when the proof is missing, turn < 1,024 B |
| S2 | S1 | `bin/preceptoros-pwa`, `turnos_hexelion.py`, `interface/app.js`, `app.html`, `sw.js`, `version.py`, tests | Talk paints the turn's own sentence (F3 closed) |
| S3 | S2 + P1 (Grok) | `turnos_hexelion.py`, `audio_feedback.py` (new `cue_for_turn`, `project` unchanged), `notebook.js`, `native_voice.js`, `app.js`, versions | schema /2, Acho cue + spoken reader |
| S4 | S3 + P2 C-TASK | `turnos_hexelion.py`, `app.js`, `notebook.js` | lifecycle and «needs your authorization», told the same everywhere |
| S5 | Sovereign decision + P1 | none in APP | read-only `turns` over MCP; until then MCP parity = NO_DATA(read_tool_not_granted) |
| S6 | S4 | `test_hexelion_autonomia_e2e.py` | create → grant → act → verify → interrupt → resume once, six surfaces identical |

## Handoffs (recorded, not implemented here)

- H1 · Codex CLI: federated negatives (catalog NO_DATA → VERIFIED; node identity mismatch).
- H2 · Grok: F6 coercions, public allowlist and 1,024 B ceiling, APP envelope normalisation.
- H3 · P2 (Codex CLI): choose and measure the recovery store (restart, pending recovery, retry ceiling, at-most-once),
  F7 stable identity, C-TASK fields mirrored into the thread.
- H4 · native server owner: a provenance log for changes under the server's directory (F1′) before any S5.

## Accessibility acceptance

One `reader` sentence per turn: who asked, what happened, the cause, what to do next. Status lines are
`role=status aria-live=polite` and announce a turn once. State is never colour alone (evidence chip: shape + word).
AWAITING_GRANT is keyboard-reachable without stealing focus. An audio cue never plays without the sentence.
Unmeasured until exercised on a device: screen-reader order, physical audio, voice grant.

## Check

S0 is docs-only (standing THE MARCH FIRMO). Each later slice: directed tests, `python3 -m unittest discover -p
"test_*.py"`, `./bin/pruebas` × 2, version alignment for served assets, exact-head CI.

## Log

- 2026-11-13 · PLAN-02 approved by the Sovereign in session; S0 and S1 built; S2+ wait for review.
- 2026-11-13 · Sovereign corrections folded in: S1 judges per tool, never `ok` alone; the thread is the visible
  history, the recovery store is Codex CLI's to verify.
- 2026-11-13 · Sovereign FIRMO S0 #273 / S1 #274 (merged); build authorised without stopping per slice.
- S2 Talk parity: the chat reply carries the projected turn; Talk's aria-live line is notebook.js `turnLine`. The
  1,023 B reply envelope holds: the turn gives way (`cut: envelope`), never the answer.
- S3a Acho: class per turn decided with its sentence (`waiting` renamed `unanswered`: nothing is said to be running);
  `audio_feedback.cue_for_turn` speaks the reader's words. Sound playback: NO_DATA(sound_opt_in_not_built) → S3b.
  Grok's mapper not imported: NO_DATA(p1_contract_unstable).
- S4a tasks: `tareas_hexelion` tells LAB #182 `meta-receipt/1` records; route and Notebook section say
  NO_DATA(p2_mirror_not_built). Who hands the journal's records to the APP is Codex CLI's (H3).
- S6: deterministic walk, EVIDENCE LEVEL SIMULATED (fake MCP + journal test double). Service, real journal, device
  screen reader and audio: NO_DATA.
- S3b turn sounds: Settings switch, off by default, kept in this browser only; Talk plays the turn's motif only when
  the turn has its sentence. Physical audio heard on a device: NO_DATA(not_exercised).
- NEXT-C mirror contract: `test_p2_mirror_contract.py` is the yardstick for Codex CLI's adapter (known, uncertain,
  permission, restart, duplicate, absent, contradictory, interruption before authorisation). A run handed twice is not
  believed; claims without a known result are `blocks_new_work` and the Notebook says new tasks wait. Still
  NO_DATA(p2_mirror_not_built): the APP is not connected to the journal.
- NEXT-A/B browser walk: `tests/autonomia_a11y.browser.cjs` starts its own server (throw-away HOME, port 18740,
  fake MCP, no model), checks served assets byte-equal to the checkout, keyboard reach of Talk, focus kept, Talk =
  Notebook = machine sentence and Acho class, state in words, no repeat on refresh, sound off, reduced motion. Run:
  `NODE_PATH=<playwright-core dir> CHROME_PATH=/usr/bin/google-chrome node tests/autonomia_a11y.browser.cjs`.
  2026-11-13 rack: PASS at 492ff58 · levels: synthetic tool SIMULATED · headless Chrome MEASURED · screen reader and
  audio NO_DATA. Findings: arrows moved from the open panel, not the focused tab (fixed: app.js v33, one press from
  Command to Talk); Talk's status changed 4 times = 3 at page load + exactly 1 per turn (now asserted). Open, not
  fixed: the load text flashes Spanish «comprobando…» before English, and a fresh home without memory.db shows
  «cannot reach the server» although the server answers.
- S5 proposal (NOT activated; needs a specific Sovereign decision): one read-only `turns` tool in the native MCP
  server, empty input schema, answering `turnos_hexelion.mcp_summary(turns, tasks)` = last turn's own state, cause
  and sentence + counts + tasks state, always under the 1,024 B MCP line (sentence gives way first). Prerequisites:
  allowlist version bump by its owner, H4 provenance log for server-file changes, the 6-tool baseline re-measured.
  Synthetic tests: `test_mcp_turns_proposal.py`. Server, permissions and tool list unchanged.
- Uncertain tasks (HUMAN-UNCERTAINTY-01, LAB #186, presentation only): a record may carry the journal's read-only
  proposal (`preceptoros.lab.uncertainty-ack/1`). JSON row, Notebook card + status, Talk line (#talk-tasks, shown
  only when something waits) and Acho cue (`needs_you`) tell: UNKNOWN, exact task/evidence/proposal refs, budget
  reserved, no retry, the decision is the Sovereign's, outside the app. Signature, budget return and worker stop are
  `not_visible` (NO_DATA). No ACK/authorise control. Changed terms, forged fields, a proposal on a known outcome →
  NO_DATA. Per-task bound 1,536 B (measured 1,198 B worst case; MCP lines and thread messages keep 1,024 B).
  The proposal's hash is the journal's check, not the APP's. Route still NO_DATA(p2_mirror_not_built).
- Accessibility measures (same walk, 2026-11-13 rack, headless Chrome): nine tabs by ArrowRight/Left (wrap),
  Home, End, roving tabindex, every panel named · contrast 232 text elements, light, min 5.01:1 after the agent
  badge glyph fix (was 1.36:1; app.css v21, cache v186); dark NO_DATA(app_declares_light_only) · sound switch by
  keyboard (Enter opens the group, Tab, Space) on → Web Audio graph ran, off → silent · 420×680: no sideways
  scroll, Send 60×44 px, box on screen, `interactive-widget=resizes-content` present; on-screen keyboard NO_DATA.
  Screen reader: NO_DATA until an authorised environment exists.
- Uncertain task in a real DOM (walk step 11): the browser is handed the fixture projection (route intercepted; the
  server route still answers NO_DATA(p2_mirror_not_built), asserted). Talk's #talk-tasks = Notebook status, word for
  word; card shows the three exact refs; Acho needs_you; no button. Level: SIMULATED data, real DOM.
- Open for others: P1 Acho/MCP contract (Codex Web, interim) · P2 mirror of journal records into the APP (Codex CLI) ·
  S5 read-only MCP tool (Sovereign decision).
- NO_DATA register: persistent_recovery_E2E(P2_not_built) · recovery_store_not_verified(H3_open) · physical_voice_E2E(not_exercised) ·
  screen_reader_on_device(not_exercised) · mcp_8_tool_window(no_audit_of_file_restore) ·
  federated_semantic_integrity(H1_open) · grok_receipt_fail_closed(H2_open).
