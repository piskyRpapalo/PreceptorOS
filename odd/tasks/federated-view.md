# Federated view · one app, many nodes (APP-FEDERATED-VIEW-01)

Commission 2026-11-13 «Corrección arquitectónica multidispositivo», Entrega C. Owner: Claude Code (APP).
CLAIM: Mesa #3 comment 6849913995. Stacked after #267 (cache v174 → v175). Contract owner: Codex CLI (LAB #178).

## Explore

- LAB #178 (draft) publishes one manifest per node backend, `preceptoros.lab.node-metadata-parts/1`: header +
  model parts pinned by SHA-256 + `snapshot_ref` = sha256 of sorted-key compact ASCII JSON of header + models.
  LAB's ceiling is 120 s; its own consumer judges age with its ceiling, never the receipt's.
- APP already reads LAB receipts with `lab_bench.from_git` (git ls-tree/show at a ref, never the working tree).
  With #178's head, `lab_bench` keeps its 2 runs and rejects 19 foreign files as `not_a_bench_file`: no
  Notebook regression when #178 merges.
- No producer exists for mobile roles, client heartbeats or Acurast state. Those stay DECLARED.

## Implement

- `federado.py`: rebuild each snapshot, re-check part hashes + `snapshot_ref`; VERIFIED ≤ 120 s, else STALE; a
  rack node without a receipt is NO_DATA(no_lab_receipt). Join with the private registry
  `<casa>/federado/dispositivos.json` (`preceptoros.device-registry/1`; names never in the repo; anonymous
  example in `federado_dispositivos.example.json`). Roles: APP_CLIENT · LOCAL_AI · MODEL_SERVER · SENSOR · BENCH_WORKER ·
  ACURAST_EXTERNAL. Only MODEL_SERVER on a rack node has a producer. Acurast = reserved, never a worker;
  Core = do not install; Lite = needs bounded test + owner consent.
- Talk: `/dispositivos` («what devices are connected?») and `/modelos` («what models do we have?»), local
  reads in the same grammar; the reply carries `datos` (the projection) for machines and Acho.
- Source: `PRECEPTOROS_LAB_REPO` (default the local LAB clone) at `PRECEPTOROS_LAB_REF` (default
  `origin/main`). The APP never fetches. Until #178 merges: NO_DATA(lab_federated_not_on_ref).

## Log

- 2026-11-13 · Not built: selector, telemetry, pings, device access, Acurast anything, a second inventory.
- 2026-11-13 · «Is the Jetson busy?» is answered only as «N loaded at the snapshot, last seen X ago»: a STALE
  snapshot is never «busy» or «free».
- 2026-11-13 · The real registry (ten devices with the person's names) is written to casa only with his OK.
