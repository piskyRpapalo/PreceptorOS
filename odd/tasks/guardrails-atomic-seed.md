# The first policies.json is seeded atomically (APP-FLAKE · atomic seed)

THE MARCH feature document · Claude Code · 2026-11-13. Cell A, rounds 6–9, CLAIM in Mesa #3. Built on `main`
`18bf0d4` (branch `claude/guardrails-atomic-seed-20261113`, kept, never opened as a PR). Replayed in round 9 onto
`main` `0747a2d` in a fresh branch; the only conflict was the suite list in `bin/pruebas` (both lines kept).

## The defect (measured)

- `guardrails.ruta_politicas` seeded `policies.json` on first use with `exists()` and then a copy in place.
- Several first uses at once (`test_canales`: 8 writers in a fresh home) let a reader open the half-copied file:
  "configuración de políticas mal formada", the channel refused the write, and the test waited 120 s.
- A copy that failed mid-way left half a file in the policies' place.

## The rule

- A reader sees no file or the whole file, never part of one.
- The copy goes to a temp name reserved with exclusive create in the same folder, then is hard-linked into place.
  A link never overwrites: whoever seeded first stays, and a file the person already has is left alone.
- Any failure stops with `PoliticasInvalidas`, leaves no file in the policies' place and no temp file.
- Only `pathlib` and `shutil` (`IMPORTS_PERMITIDOS` is not widened). No test relaxed or excluded.

## Measured

| | Before | After |
|---|---|---|
| Suite failures, 15 runs each idle / 16 burners / 32 burners (16 cores, Python 3.14.4) | 7 of 45 on `60064d7` (1, 4, 2) | 0 of 45 on `3a85fe1` |
| Sabotage, one run per condition | 6/6 ×3 | 6/6 ×3 |
| Probe: 8 processes, fresh home, fork, 200 rounds | 1 round failed | 0 rounds failed |
| `test_siembra_atomica` on `main` `0747a2d` | 2 defects fail (half-copy read; failed copy leaves half a file) | 5/5 pass |

The fifth test (no hard links) pins the new behaviour; `main` never links, so it is not a defect there.

## Limits and NO_DATA

- 0 of 45 and 0 of 200 do not prove the intermittent failure is gone: they are consistent with it, and the
  deterministic test shows the measured cause can no longer happen. Another cause is not excluded.
- **Decision for the Sovereign:** on a filesystem without hard links, seeding now stops instead of copying. The
  alternative (rename into place) could overwrite a file that appeared in the gap. Not measured on such a
  filesystem: `NO_DATA(no_hardlink_filesystem_not_exercised)`.
