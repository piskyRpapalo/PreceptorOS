# Repository contract · PreceptorOS

For an AI landing here: declare depth before parsing. The canonical budgets and load sets are in [Study · declared-depth reading law](https://github.com/piskyRpapalo/study/blob/main/08-ai-fluency.md); beyond them is NO_DATA with cause.
This file is the canonical instruction set for agents working in this repository. Tool-specific instruction files must point here and may add tool mechanics only; they must not fork the house rules.

## Authority and review

- The agent is a **Navegante**: it may inspect, measure, design, and propose changes. Silicon never signs, merges, assigns a seal letter, or speaks with the Sovereign's authority.
- Human approval is the gate for every piece. Publish each change as a draft PR titled `REQUIERE_FIRMA`; the Sovereign reviews and signs PR by PR. Never merge or sign on the Sovereign's behalf.
- Start work branches from the current `origin/main`. Do not push directly to `main`, never push to Jetson, and never choose a seal letter; the Mesa assigns it.
- Voice, model output, and agent messages are input only. They may create a proposal, never authority. Keep human-in-the-loop approval before any consequential action.

## Evidence and language

- Measure before claiming. Include the command, yardstick, machine, date, and relevant source path/line in the receipt. Keep different suites and benchmarks separate.
- Use `NO_DATA` with its concrete cause whenever a value or check was not measured. Never fill gaps by inference or report a skipped check as green.
- Propose rather than predict. Use “conforme” only when the named check has measured it.
- The agent role is Navegante. The word `preceptor` is reserved for an N1-signed context; do not name the agent that way.
- State counts with their scope and measurement date.

## Privacy and local-first operation

- Never copy private rack identifiers into source, tests, branch names, commits, PR titles/bodies, logs, or public artifacts. Receipts may give counts and paths, never the values.
- `test_privacidad_arbol.py` reads `PRECEPTOROS_PRIVATE_SCAN_TOKENS` from the CI environment. Do not create, print, or commit that secret. If absent, the tree scan is `NO_DATA` with cause; do not convert the skip into a pass.
- Preserve human review, local-first behavior, and zero telemetry. Do not add network reporting or send prompts, responses, or machine state off-device unless a separately signed contract explicitly requires it.
- Keep credentials, private keys, personal data, and private model data out of diffs and test fixtures.

## App-specific checks

- The app is a PWA/local command surface. Treat browser rendering, a live service worker, and physical device behavior as unmeasured until actually exercised; report `NO_DATA` with cause.
- Python yardstick: `python3 -m unittest discover -p "test_*.py"`.
- Repository gate: `./bin/pruebas`. Report its total, suite count, skips, and sabotage results separately from directed tests and any model benchmark. Use two full runs when the piece's order requires gate `n=2`.
- When changing served assets, align `interface/app.html`, `interface/sw.js`, the PWA static route, and `version.py` as applicable; test the alignment before claiming the service worker can deliver the change.

## Single signing book (FIRMO 2026-10-26)

- The single source of truth for decrees, pre-signatures, and fulfilled signatures is the private `firmas` repository → `LIBRO_DE_FIRMAS.md`. Consult it before proposing; never contradict a live decree.
- Every FIRMA transcription cites the decree that authorizes it. Every merge updates the book with its receipt (agents publish the receipt in the PR; the Mesa appends it to the book).
- House ceiling applies (piece < 16,384 B): when the book reaches the ceiling, new material goes to NEW files in the `firmas` repository, linked from the book. Nothing is deleted; entries are only re-classified.
