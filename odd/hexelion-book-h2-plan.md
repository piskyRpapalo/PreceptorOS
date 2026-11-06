# H2 · THE BOOK · implementation plan

Source revision measured: `ad12b565c527042a18f19c642e4b55b662f9393c` (`origin/main`, 2026-11-06).

## 1. Reuse the memory search contract

Keep `POST /api/hexelion/search` as the sole search route. Extract or call one shared server-side operation backed by `memory_lookup.buscar()` so both search and chat use the same read-only FTS retrieval, `preceptoros.memory-search/1` schema, 50-candidate ceiling, and source hashing. Do not make an HTTP self-call and do not create a parallel search implementation. Relevant code: `bin/preceptoros-pwa:878-910`; `memory_lookup.py:10-19,27-67`.

For chat, query with the just-submitted turn after its existing append to the Sovereign voice. Accept only `MEASURED` results with at least one source; check each source has a positive integer ID, `updated_at`, 64 lowercase hex SHA-256, text, and a recomputed matching hash. Select no more than three sources, preserve each source whole, and cap their combined `texto` at 768 UTF-8 bytes. If the existing search response is `NO_DATA`, empty, malformed, or has no eligible complete source within the bounds, return an honest `NO_DATA` receipt and do not call the station. Do not send the entire append-only thread as context; indexed memory is the evidence surface, and absent indexed history stays `NO_DATA`.

## 2. Bound and constrain the station prompt

Construct a prompt from a fixed instruction, the selected source IDs and exact source text, and the current turn. The complete UTF-8 prompt must remain at or below 4,096 bytes. Measured sizing fixture: 3 × 256-byte source texts plus a 1,000-byte turn produced 2,352 bytes with the proposed envelope; the source text budget and turn ceiling leave margin under 4,096. The station's measured native context is 131,072, but H2 deliberately uses this smaller application cap.

Ask the existing model for a strict JSON object containing only up to three `{id, quote}` entries, with each `quote` copied verbatim from the cited source. The server parses a duplicate-key-safe shape, rejects unknown IDs, and verifies each quoted UTF-8 string is an exact substring of that source. Reject empty evidence and all malformed or non-extractive output as `NO_DATA`; do not fall back to a freeform answer. This extractive response shape makes the displayed claim verifiable against the cited text rather than relying on a model's self-reported citation.

Keep `think:false`, `stream:false`, model selection, probe, and generation options in `hexelion_proxy.py:12-16,66-106` unchanged except for the prompt content and a 320-byte accepted quotation budget. Keep the station URL exclusively in the service environment; do not expose it in HTML, JavaScript, receipts, or logs.

## 3. Preserve the append-only thread and public receipt

Append the returned extractive answer through the existing Hexelion voice in the existing `orquesta` channel. Attach the verified source IDs, timestamps, and hashes as citation metadata to that new event and response body. Never edit old records or reinterpret existing un-cited frames. If memory or citation verification fails, keep the already-appended Sovereign turn and return `NO_DATA` with a concrete cause; append no fabricated assistant answer.

Keep the response schema compatible with `interface/hexelion.js:20-49,76-95`: model, generation milliseconds, separately measured browser wait, cause, and citations. For an absent station call, model and duration are explicit `NO_DATA` values with causes. Bound the exact serialized response below 1,024 UTF-8 bytes; the synthetic sizing fixture with three citations and a 320-byte quote measured 886 bytes. Do not truncate text to force it under the ceiling; reject with `NO_DATA` if actual metadata makes it exceed the budget. The existing AbortController still aborts only browser waiting; a server-side append remains append-only.

## 4. Tests and gates

Add directed tests for:

1. Chat invokes the same memory lookup contract as `/api/hexelion/search`, using the current turn and the configured local database.
2. Valid source hashes and exact excerpts yield cited output; changed hash, foreign source ID, fabricated/altered quote, empty evidence, malformed JSON, and duplicate keys fail closed.
3. No search matches or unavailable index returns caused `NO_DATA` and makes no station generation call.
4. At most three sources and 768 text bytes enter context; full prompt is at most 4,096 bytes; 1,000-byte turn + maximum source fixture remains within budget.
5. Citation-bearing response stays below 1,024 bytes at the 320-byte quote ceiling; actual oversize fails with cause.
6. Station request still uses `think:false`, `stream:false`, `num_predict:160`; browser code contains no station endpoint; append-only event citations do not mutate prior records.
7. Every successful and `NO_DATA` page receipt names model, generation duration, total browser wait, and cause honestly.

Run `python3 -m unittest test_pwa` and `./bin/pruebas`, then SCRUB the exact diff. Commit the implementation as one unit, push only `mesa/hexelion-book-h2-20261106`, open a draft PR to `main` with `HITL` in its title, and stop for review. No merge and no signature.

## Approval status

Approved by the Sovereign on 2026-11-06. The implementation and required gates have been completed in the worktree.
