# app-tray-ancestor-symlink

Date: 2026-11-10
Law: THE MARCH, existing local tray reader and [Mesa audit](https://github.com/piskyRpapalo/buzon/issues/61)

## Objective
Reject a local tray where the `data/` ancestor is a symlink. Incremental hardening, not a new reader.

## Problem and why
The original reader checked the file and immediate `bandeja/` directory, but not the `data/` ancestor. An ancestor symlink could redirect the local read.

## Scope
One ancestor check and one synthetic adversarial test. No networking, permissions or format changes.

## Constraints
No private tray files, no merge, no service deployment. Not a comprehensive TOCTOU-proof traversal.

## Checklist
- [x] S1: Reproduce bypass: unchanged base RED with valid JSON symlink fixture.
- [x] S2: Reject ancestor symlink as NO_DATA.
- [x] S3: Target tests GREEN twice on the Beelink.
- [ ] S4: Full APP CI and run (NO_DATA until verified).
- [ ] S5: Human FIRMO on exact PR head.

## Verification evidence
Synthetic adversarial case failed against unchanged base and passed with fix in two runs. Runtime and physical device: NO_DATA. Race between checks and read remains a separate threat.

## Standing signature
Requires human head-specific FIRMO for merge.

## Log
Codex GPT-6 · isolated fixture, no mutation of operator working checkout.

## Next step
Run the full suite and review CI.
