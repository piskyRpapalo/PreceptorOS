# STATE · PreceptorOS (APP)

> Status: PROPOSAL, unsigned. Measurement snapshot: 2026-10-17. This card
> records measured values and links to their source; it is not a promise.

## The ecosystem

- **WEB** · [preceptoros-web](https://github.com/piskyRpapalo/preceptoros-web), measured at `e1aafeeb`.
- **APP** · this local-first repository, measured at `3c39596`.
- **LAB** · [lab](https://github.com/piskyRpapalo/lab), measured at `2cb70d8`; it preserves benchmark records and counters.

## Measurements taken 2026-10-17

Machine for local test and file measurements: Linux x86_64, AMD Ryzen 7 255 with Radeon 780M Graphics, 16 logical CPUs.

- APP Python discovery: `python3 -m unittest discover` at APP `3c39596` — **867 tests: 856 passed, 11 skipped, 0 failed**. This is the Python discovery yardstick only; it is not the full `./bin/pruebas` suite.
- WEB Node suite: `node --test` at WEB `e1aafeeb` — **244 tests: 234 passed, 10 skipped, 0 failed**. This is separate from the Python `test_web.py` yardstick.
- WEB public-site weight: **1,237,121 B across 186 counted files**, recomputed read-only from `public/` with the exclusions `downloads/`, `counters.json` and `historial/` defined by WEB `contadores.py:55-65`. It matches the declared `peso_sitio` in WEB `public/counters.json`; that file was not changed.

## Current recorded LAB benchmarks

No inference was re-run for this card. The figures below are dated records, each with its own yardstick.

- Qwen 35B-A3B GGUF, 2026-10-16, `llama-bench`: Vulkan generation **20.760 tok/s** (two samples, SD 0.197); CPU generation **2.114 tok/s** (two samples, SD 1.747). Prefill: Vulkan **294.271 tok/s**, CPU **92.295 tok/s**. See [LAB benchmark and provenance](https://github.com/piskyRpapalo/lab/blob/2cb70d8/benchmarks/qwen36-35b-20261016/README.md), lines 3-19.
- Local role check, 2026-10-16: the unavailable-engine sabotage was rejected; two local responses matched by hash, each with 75 prompt-evaluation tokens and 33 output tokens. Timings: **14.698 s** (13.209 s load) and **1.037 s** (0.002 s load). This measures one narrow authority task, not general model quality. See [LAB G0 record](https://github.com/piskyRpapalo/lab/blob/2cb70d8/benchmarks/preceptor-g0-20261016/README.md), lines 3-15.
- H9 readability, 2026-10-16, synthetic fixtures: explicit map without dictionary **4/8** exact reads; dense stimulus **0/8** versus prose **2/8** exact reads. Length and content differed, so this is an observation, not an isolated causal estimate. See [LAB H9 record](https://github.com/piskyRpapalo/lab/blob/2cb70d8/benchmarks/h9-readability-20261016/README.md), lines 7-17.
- Embedding record, 2026-10-11: embeddinggemma-2 **6,459 tok/s** at prompt-pair 512, sanity cosine similarity **0.908**. See [LAB record and raw-data reference](https://github.com/piskyRpapalo/lab/blob/2cb70d8/benchmarks/bench_20261011/README.md), lines 3-18.

## Boundaries and missing measurements

- The WEB vector is described by the live contract `preceptoros.vector/1`; its current source is [`public/game/state_vector.js`](https://github.com/piskyRpapalo/preceptoros-web/blob/e1aafeeb/public/game/state_vector.js). This card does not copy a live vector or claim a current device reading.
- APP `./bin/pruebas` total, suite count and full-gate result: `NO_DATA` for this measurement; the requested `python3 -m unittest discover` command was measured instead. Do not compare or add those yardsticks.
- Current browser rendering, service-worker behavior, physical-device FPS, temperature, energy, sustained-load behavior and broad model quality: `NO_DATA` with cause — the measurements above do not exercise those sensors.
- LAB remote CI: `NO_DATA` / not configured, per [LAB agent contract](https://github.com/piskyRpapalo/lab/blob/2cb70d8/AGENTS.md); its local test yardstick is `python3 -m unittest discover -s tests -p "test_*.py"`, separate from APP and WEB.

*Measured 2026-10-17 from APP `3c39596`, WEB `e1aafeeb` and LAB `2cb70d8`. Historical benchmark dates remain attached to their records.*

## Reading and scope

- Counts describe the command named beside them. Skips remain visible and are not counted as passing checks.
- The APP discovery result covers `unittest` discovery only. It does not stand in for `./bin/pruebas`, remote CI, or live PWA rendering.
- The WEB Node result is the complete `node --test` run at the recorded commit. It is not the separate Python web gate.
- Site weight follows the public tree's declared counter exclusions; the calculation was repeated without rewriting the counter file.
- Archived LAB results retain their original measurement dates. They are not implied to be live throughput on the card's measurement date.
- The older `tg32` throughput figures remain in the LAB archive, but the session log is absent; command, exact date, machine details and repetition count are `NO_DATA` (`benchmarks/tg32/README.md:8-15`).
- No browser session, physical-device FPS run, thermal probe or broad model-quality corpus was run as part of this refresh.

## Refresh rule

- Replace a figure only after measuring it again with its own command and source; keep historic benchmark dates and yardsticks attached to their records.
- Do not infer status from a skipped test, an archived result, a model tag or a public web page.
This line is a stable deep-link target from the APP's `llms.txt` index; its destination is this dated state card, not a separate live sensor.
