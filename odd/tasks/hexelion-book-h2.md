# H2 · THE BOOK · memory-grounded Hexelion chat

## Cause

Measured at source revision `ad12b565c527042a18f19c642e4b55b662f9393c` on 2026-11-06: `/api/hexelion/chat` accepts only `{texto}` and calls the station with that turn alone (`bin/preceptoros-pwa:821-876`, `hexelion_proxy.py:87-89`). The append-only channel records the Sovereign's turn and Hexelion's reply, but the station receives neither that thread nor cited house memory. Its honest answer can therefore be “no recuerdo.”

The local `POST /api/hexelion/search` already returns `preceptoros.memory-search/1` sources with `id`, `updated_at`, `sha256` and `texto`; `memory_lookup.buscar()` is read-only and keeps its complete result under 1,024 UTF-8 bytes (`bin/preceptoros-pwa:878-910`, `memory_lookup.py:10-19,27-67`). The route and lookup are the existing evidence contract; H2 adds no search endpoint.

## Intended result

Each chat turn searches the existing local memory using the current turn, verifies the returned source hashes, and gives Hexelion only a bounded set of verified evidence. The model returns exact quotations with source IDs; the server accepts a quotation only when it is an exact substring of the verified source. The page shows those citations with the answer. Missing memory, invalid hashes, absent/invalid quotations, or a station failure produce `NO_DATA` with a cause and never a freeform unsupported answer.

The existing `PRECEPTOROS_HEXELION_ENDPOINT` remains server-only and loopback-validated (`hexelion_proxy.py:12,24-41`). `think:false`, `stream:false`, and `num_predict:160` remain unchanged (`hexelion_proxy.py:87-89`). Existing append-only voice records remain authoritative; no historical frame is edited. A failed or stopped browser wait does not retract a server append.

## Measured bounds and receipt

- Station facts supplied with this commission, measured by `ollama show` on 2026-11-06: `hexelion:latest`, base `gpt-oss` 116.8B, native context 131,072; completion, tools, and thinking capabilities; default thinking medium. This is station measurement supplied by the commissioner, not a repository measurement. H2 keeps thinking disabled.
- Existing search response ceiling: `<1,024 B`; search candidate ceiling: 50; current retriever call requests `presupuesto=240` (`memory_lookup.py:27-67`).
- Local data measurement: the configured memory index has 4 rows. Two non-sensitive query-shape probes returned zero sources; source text was not inspected or copied. Live source-size distribution is therefore `NO_DATA` (cause: probes had no matches).
- Proposed injected-memory bound: at most 3 verified sources and 768 UTF-8 bytes of source text; complete model prompt hard-capped at 4,096 UTF-8 bytes. A synthetic sizing fixture with three 256-byte source texts and a 1,000-byte turn measured a 2,352-byte prompt. This fixture is a sizing measurement, not a station response.
- Proposed reply cap: 320 UTF-8 bytes of extracted quotation text. A synthetic serialized receipt with 3 citations, model, duration, cause, and a 320-byte quotation measured 886 bytes. The server still checks the actual complete receipt is `<1,024 B` and fails closed if it exceeds the ceiling.
- Every page receipt retains `model · generation ms · total browser wait · cause`; unavailable values remain `NO_DATA` with cause. Existing page rendering measures the browser wait separately (`interface/hexelion.js:20-26,35-49`).

## Gates

- `python3 -m unittest test_pwa`: existing PWA suite plus tests for source reuse, hash mismatch, exact-quote enforcement, absent memory, source and prompt caps, receipt `<1,024 B`, append-only citations, `think:false`, and no station URL in browser code.
- `./bin/pruebas`: full repository gate; report total, suite count, skips, sabotage results, and any unavailable check separately.
- SCRUB: no private paths, local database text, secrets, non-loopback station addresses, or historical-thread rewrites.
- One implementation commit; push only the H2 branch; draft PR titled with `HITL`. Stop there for independent CI review and the Sovereign's exact-head signature; never merge or sign here.

## Approval and completion

Approved by the Sovereign on 2026-11-06. Implementation is complete in the approved worktree; gates and SCRUB are recorded in the PR receipt.
