# Guardian followup · the sabotage follows the agent rules that remain

## Objective
The retirement of CLAUDE.md (pull 174, decree: every agent is a preceptor) left the privacy
guardian's sabotage test demanding a file that no longer exists. Every run of `./bin/pruebas`
went red on main and on every branch. This piece retargets the sabotage to `AGENTS.md`, the one
agent-rules file that remains.

## Measured
- Main red since `497c8e29` (run 41959063744, all five python versions of the matrix).
- Failing assertion, `test_privacidad_arbol.py`: «el guardián no lista CLAUDE.md» — the
  guardian lists tracked files, and the file was retired from the tree.
- Jail verification with a simulated `git ls-files` over the cooked tree: 3/3 green
  (1 skipped, NO_DATA · privacy secret not mounted); the marker is planted in `AGENTS.md`,
  found exactly once, restored byte-identical.
- In a jail without git the failure is masked (the tree listing raises before the assertion):
  that is why the red only appeared in CI. Contrast with pristine main always.

## Change
- `test_privacidad_arbol.py`: the sabotage of the agent rules plants its marker in
  `AGENTS.md` and expects `AGENTS.md` — nothing else changes.

## Constraints
Propose-only; one piece = one PR; FIRMA over the exact head; silicon never merges itself.
`./bin/pruebas` gates: the sabotaje must stay a real catch — a tree that silently stops
listing agent rules must stay red.

## Checklist (stable IDs)
- [x] G-a: the guardian lists `AGENTS.md` (tracked, present).
- [x] G-b: the sabotage is planted, found and restored on `AGENTS.md` (jail, simulated listing).
- [x] G-c: no other file changes; no vocabulary or interface file touched.

## Log
- 2026-11-05: claimed under acta buzon#53 ·6649405976; cooked by mesa-web; FIRMA pending on
  the exact head of this pull.

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA
