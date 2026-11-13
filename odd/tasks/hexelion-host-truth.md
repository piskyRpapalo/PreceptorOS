# Hexelion host truth · what it knows, what it ignores, what it can prove (HOST-TRUTH-TO-APP)

THE MARCH feature document · Claude Code (Opus 5.5) · 2026-11-13. A delivery under the existing autonomy-parity
mission (`odd/tasks/hexelion-autonomy-parity.md`), not a new mission. Base: APP `main` `b7937ce` (#290 merged).

## Preconditions read (2026-11-13)

- APP #290 is merged (`b7937ce`, which contains `afacb6f`).
- LAB `main` `51782ea` (#198 merged) holds Codex CLI's P2 pieces:
  - `meta_harness/readonly_mirror.py`: an in-process, allowlisted, read-only host adapter;
  - `uncertainty_views.py`: one record, viewed as text, speech and machine under one `projection_ref`, TTL 0;
  - `host_witness.py` and `recovery_readiness.py`.
- LAB's own doc (`odd/tasks/p2-readonly-mirror-01.md`) says what is still missing:
  - a host-supplied local-source witness (default `NO_DATA(local_source_not_attested)`);
  - a WAL-safe snapshot;
  - real human and fence witnesses;
  - an **authenticated APP transport**, a deployment review and a live E2E.
- **Owners:** Codex CLI owns the journal, the mirror, the witnesses and provenance (H3/P2). APP owns only the consumer.
- **Lawful default:** no accredited adapter exists, so APP builds the consumer and its contract tests. The live route
  stays `NO_DATA(p2_mirror_not_built)`. No fictitious source, no synthetic callback as authority, no database or
  process access from APP.

## What changed (one projection, no new engine)

`tareas_hexelion.project` is still the only place a task state is decided. Talk, the Notebook, Acho and the JSON copy it.

1. **LAB's packet is read as LAB produces it.** `text`, `speech` and `machine` must bind the same `state_ref`
   (= `projection_ref`) and the same words. Otherwise the row says `views_bind_different_refs`,
   `views_say_different_words` or `views_fields_unknown`.
2. **The host's cause is the cause.** A NO_DATA projection (`task_ref: null`) passes its own code through:
   `local_source_not_attested`, `source_busy_or_wal_not_supported`, `source_unavailable_or_unsafe`,
   `source_not_allowlisted`, `host_clock_invalid`. Before, all of these read "another task".
3. **UNKNOWN stays UNKNOWN.** When a projection cannot be used, the receipt's own uncertainty stands: the row keeps
   OUTCOME_UNKNOWN, keeps blocking new work, says why the projection was set aside, and says "Do not retry".
4. **TTL 0 means read now.** A projection observed more than 5 s from the read (clock skew) is
   `uncertainty_projection_stale`, and none of its details are shown as current.
5. **Evidence travels.** Every row carries `evidence: {origin, ref}`, using the receipt contract's own words:
   MEASURED (`public_deterministic_reference`, `protocol_roundtrip`), SIMULATED (`synthetic`) or NO_DATA (no
   measurement), with the full `receipt_ref`.
   - A simulated run says so in its sentence, so the eye, the ear and the machine all get it.
   - A receipt whose basis or ref can't be named, or that has a measurement without a basis, is NO_DATA.
   - The card shows the evidence under "Receipt and references".
6. **A failed reading names who failed.** "Answered http 500" is not "did not answer", in the Notebook's tasks,
   requests and benchmarks.
7. **Bytes kept apart, budget unchanged.** The constant Acho terms are said once per projection (`acho_terms`). The
   spoken next step no longer reads a hex prefix aloud; the full ref is in the machine row and the card's details.
   The worst row is 1,015 B, under the 1,024 B row budget.

## Measurements (directed, Python yardstick plus headless Chrome; baseline = `main` `b7937ce`)

| Metric | Before | After |
|---|---|---|
| LAB packets read in their real shape (8 produced) | 0/8 (`uncertainty_fields_unknown`) | 8/8 |
| Host NO_DATA causes reported correctly (bare record, 6) | 0/6 ("another task") | 6/6 |
| Rows hiding an UNKNOWN when the projection is unusable (blocks_new_work 1 → 0) | yes | no |
| Old projection shown as current | yes | no (`uncertainty_projection_stale`) |
| Rows without an evidence ref | every row | 0 (a claim with no receipt says NO_DATA) |
| Simulated receipt told as a real run | yes | no ("Simulated run:") |
| False successes on the adversarial set | 0 | 0 |
| Valid LAB packets refused (false rejections) | 2/2 | 0/2 |
| Adversarial cases detected (`test_host_truth`, 16 tests) | 5/16 | 16/16 |
| Contradictions Talk vs Notebook vs machine (walk step 11, LAB packet) | not measurable (packet unread) | 0 |
| Announcements of one task reading read twice (client test) | 1 | 1 |
| Worst task row | 1,005 B (without evidence) | 1,015 B (with evidence) |
| Task route read, isolated server | NO_DATA | 78 ms (headless walk; not the live service) |

## E2E levels

- **Synthetic source:** MEASURED. LAB's real producer ran on a synthetic journal, then APP's projection, then Talk,
  the Notebook, the disclosure opened by keyboard, Acho's class and the machine JSON (walk step 11).
- **Real, verifiable receipt:** NO_DATA (no attested host source and no APP transport).
- **Authentic operating service:** NO_DATA. The route is unconnected, and port 8742 was not touched.

## Still NO_DATA

A screen reader in use · sound heard on a speaker · a real phone keyboard · the private tree scan (no credentials).

## Next (proposed, not started)

- **"What are you doing, what have you achieved, how do you know, what do you need from me?"** One status line built
  from the existing turn and task projections (`turnos_hexelion.mcp_summary`), shown in Talk, the Notebook and
  Harness with the same refs. No new projector.
- **The transport** belongs to Codex CLI and the host. APP will read it only once the Sovereign has signed an
  authenticated adapter.
