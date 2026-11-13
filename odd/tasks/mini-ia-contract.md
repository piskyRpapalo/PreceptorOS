# Mini-AI contract for the APP · PROPOSAL (APP-MINI-IA-01)

Commission 2026-11-13, section 5: «study `public/game/web_node_brain.js` and propose a mini-AI contract; do not
build, install weights or train». This file is that proposal. It changes no code. The bench beside it is
`mini-ia-router-bench.py` (run: `python3 odd/tasks/mini-ia-router-bench.py`).

## What the web brain is (read 2026-11-13, web `origin/main`, `public/game/web_node_brain.js` 11,148 B)

- SmolLM2-135M-Instruct + LoRA on the map's facts (2026-11-09), Q4_K_M, **105,453,984 B in 5 chunks < 25 MiB**,
  wllama 3.8.1 (MIT; js 382,633 B + wasm 8,763,949 B), CPU/WebAssembly, no WebGPU. Strict eval 19/32 (base 2/32).
- Every byte that runs is pinned by SHA-256 in `/models/web-node/manifest.json`; mismatch → NO_DATA.
- `load({consent:true})` only: nothing downloads without explicit consent. `n_ctx 1024`, 1 thread.
- `reply()`: greedy (temp 0, top_k 1, seed 1), `max_tokens 56`, input ≤ 600 B, two sentences max, then
  `groundAnswer()` **overrides the model** with page-measured text for controls and missions. The file itself
  records that the model «has repeatedly invented obsolete movement controls».

Lesson: on this rack a 135M model is trusted to *phrase*, never to *know*. Facts come from the page.

## Measured gap in the APP (2026-11-13, this tree, bench above)

Talk already answers the six questions from receipts with no model (`lectura_local`, `mcp_nativo`). The gap is
**routing**: a person's own words rarely hit an exact phrase.

| router | routed (80 paraphrases, 8 read intents, es/en/pt) | misrouted | false positive (30 non-read) | weights |
|---|---|---|---|---|
| exact grammar (today) | **16/80** | 0 | 0/30 | 0 B |
| lexical, read-only (bench) | **76/80** | 1 | 1/30 («should i sign 266» → /firmas, harmless read) | 0 B |
| SmolLM2-135M router | NO_DATA (not run: the commission forbids installing weights from APP) | | | 105 MB |

Caveat: corpus and rules have the same author; corpus written first, rules after. 95% is an upper bound, not
an independent result. Real phrasing = NO_DATA until measured on the person's own turns (counts only).

## Proposed contract `preceptoros.mini-ia/1`

1. **Role.** The mini-AI is a *router*, never a source of facts. Its whole output space is the closed set of
   read commands (`/estado /capacidades /registro 5 /firmas /lab /preceptores /dispositivos /modelos`) or
   `NONE`. It can never emit `/ejecuta`, `/escribe`, a signature, a merge or a device action. The answer always
   comes from the existing local read, labelled with its `via`; the route is labelled `route: lexical|model`.
2. **Tier 0 — lexical (0 B).** Ships first. Topic word required; an action/explanation verb vetoes («install»,
   «delete», «sign the», «explain», «why»…) so those go on to Hexelion as ordinary questions. Deterministic,
   ~µs, testable with sabotage.
3. **Tier 1 — on-device model (optional, later, HITL).** Only if Tier 0's measured miss rate on real turns
   stays above a threshold the Sovereign sets. Reuse the web's pinned manifest *by hash* (one model, not a
   second copy); APP_CLIENT phones download only with consent; greedy, `max_tokens ≤ 8`, output must parse to
   one command or it is `NONE`. No training, no new weights.
4. **Visibility.** Before running a routed read, Talk shows «I read this as /firmas» so a deaf or blind person
   (screen reader) hears the interpretation, and the person can undo it.
5. **Evidence.** Each routed turn records `route`, `command`, and `confidence: rule|model`; the Notebook counts
   misses (`NONE` then the person typed a command) — the only honest yardstick for Tier 1.
6. **Budgets.** Input ≤ 600 B (as the web); route ≤ 5 ms Tier 0; Tier 1 latency on S110/TANK 3 = NO_DATA until
   measured with consent; memory budget per device = NO_DATA (RAM not observed).

## NO_DATA (cause)

- Model routing accuracy: weights not loaded (forbidden in this commission).
- S110 / TANK 3 RAM, latency, battery: not measured; needs a consented session on the device.
- Real-user phrasing: not collected; would be computed locally from the Talk thread, reported as counts.

## Log

- 2026-11-13 · Next lawful step if he signs this proposal: Tier 0 as one slice (router + «I read this as» +
  tests + sabotage), stacked after #269. Tier 1 waits for real-turn misses.
