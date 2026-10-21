# M8 · Local coder console proposal

**Status:** draft proposal; blocked by PreceptorOS issue #59. This document does not authorize execution, service startup, network access, or a downloadable runner.

## Measured starting point

The current `main` contains reusable local surfaces: `empieza_aqui.py` exposes a guided entry point (`documento`, `responder`; lines 213–292); `canales.py` provides append/read operations (`di`, `lee`; lines 222–277); `consola.py` reads and validates local model and rack state (`verificar_blob`, `modelos_pc`, `instantanea`; lines 163–204, 408–466); `herramientas.py` retrieves bounded context (`_cabe`, `recuperar`; lines 300–302, 391–473); and `estado_compacto.py` validates and serializes compact state (lines 43–128). These are candidate adapters, not permission to expand their authority.

Issue #59 remains unanswered. It asks whether a downloaded local cell only checks requirements or may start the existing service after an explicit confirmation. Until that contract is decided, the execution adapter and download artifact remain unspecified and the M8 execution path is blocked.

## Proposed structure

1. **Commission surface:** a narrow app entry point accepts a human-authored study request and presents its bounded plan before execution. Reuse the guided entry and compact-state readers where their existing contracts fit.
2. **Policy gate:** validate the request against a fixed allowlist, declared byte and resource ceilings, and an explicit execution mode. Unknown fields, missing authority, or an unresolved mode fail closed.
3. **Execution adapter:** keep this as an interface only. Its implementation depends on issue #59; do not launch a process, download code, or select between its options before the decision.
4. **Receipt:** return status, result count, payload digest, and cause. Preserve the distinction between proposal, execution, and human approval; no model output signs or changes authoritative state.
5. **Storage boundary:** use the existing append-only channel only for an explicitly approved receipt. Do not write authority records or infer that a channel event grants permission.

## Contract boundary

The console may read local state and prepare a proposal. Any consequential execution requires a separate human gesture after preview. A receipt reports what happened; it does not authorize the next action. Exact downloadable-file behavior, launch semantics, and the request schema are **NO_DATA: issue #59 has no answer**.

## Tests required before implementation

- Missing execution-mode decision is rejected before any process launch.
- Unknown request fields, oversized request, and disallowed operation are rejected with a cause.
- Cancellation after preview produces no launch and no state write.
- A successful dry run returns a stable receipt with status, count, digest, and cause fields.
- Receipt creation cannot write the authority store or turn model output into approval.
- The approved mode, once decided, gets separate tests for its exact side effects and a sabotage case proving the other mode cannot run.

## Gate proposal

First demonstrate red with a missing-mode fixture and assert zero launches/writes; then make that case pass by rejecting it closed. Run the focused tests twice and the repository Python suite plus `./bin/pruebas` twice in separate invocations. Record skipped checks separately. Do not claim M8 complete until issue #59 is resolved and the selected execution contract has measured tests.
