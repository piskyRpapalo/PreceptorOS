# Capacity-based colony building plan

Status: propose-only. This is a plan, not a hardware measurement, node admission, installation order, or runtime change. It adds no app map: the one-map canon keeps the web as the sole state source and the app as its connector.

## Canon and boundary

The signed nine-object vocabulary is `boya`, `observatorio`, `lapidas`, `cristal`, `botella`, `monumento`, `vivero`, `baliza`, and `nombres` ([source at FIRMO commit `2ef4315`](https://github.com/piskyRpapalo/preceptoros-web/blob/2ef4315566b5af324e1be8d106ba10de36a74317/public/game/reef_building_lifecycle.js#L21), [migrated web canon at `97bf5d4`](https://github.com/piskyRpapalo/preceptoros-web/blob/97bf5d4403ed7172ed22fa6a13043ea0dbc5a39b/docs/canon-map-and-painter-2.md#L180); app schema: `data/edificio.schema.json`). The shared building contract makes the frame a pure function of its manifest and game tick. Its `carga` field is compute load; the colour canon reserves hue for life, saturation for measured compute load, and lightness for declared shield. A throughput result is not a `carga` measurement.

The type-to-capacity choices below are new candidates for review, not assignments found in the canon. IC4's current dome/tower/block silhouette is selected by building ID; it does not measure host capacity. The merged app preview in PreceptorOS#140 is still local-only and is not loaded by the PWA. The app poll and physical app rendering remain `NO_DATA`.

## Proposed table

| Node | Candidate building | Capacity / measured work | Cause and provenance |
|---|---|---|---|
| `beelink` | `observatorio` · heavy-tier candidate | Host RAM 57 GiB; local model class 30B, estimated 18–22 GB. Local tok/s this week: `NO_DATA`. | Candidate follows the measured host-RAM envelope. Do not attribute the station's 120B/64 GiB VRAM run to this node; that run used the remote station over a tunnel. [NEXO#16 benchcard](https://github.com/piskyRpapalo/hexelion-nexo/pull/16) and the Sovereign's 2026-10-30 correction in Buzon#30. |
| `la-torre` | `cristal` · bounded-tier candidate | Jetson CUDA ceiling about 6.5 GiB. The 1.5B sample ran on CPU at 25.43 tok/s after CUDA allocation failed; no CUDA fit is established. | Keep RAM and VRAM separate; do not add them. [NEXO#16 benchcard](https://github.com/piskyRpapalo/hexelion-nexo/pull/16) and the Sovereign's 2026-10-30 correction in Buzon#30. |
| `la-fragua` | `vivero` · medium-light candidate | 0.5B sample, median 24.69 tok/s; the response was partial/nonempty and had no calibrated typed fields. The source labels the arm 15 GiB. | Throughput and memory are distinct from runtime utilization. `carga` remains `NO_DATA`. [NEXO#16 benchcard](https://github.com/piskyRpapalo/hexelion-nexo/pull/16) and the Sovereign's 2026-10-30 correction in Buzon#30. |
| `el-vigia` | `boya` · light candidate | Raspberry Pi 5, 4 GiB RAM; one nonempty 0.5B smoke only. No multi-run measurement. | The smoke is not a heartbeat or an app-live seal. No further runtime installation is proposed. [NEXO#16 HS1b receipt](https://github.com/piskyRpapalo/hexelion-nexo/pull/16) and the Sovereign's 2026-10-30 correction in Buzon#30. |
| `doggee` | `baliza` · light candidate | Numeric memory, throughput, and workload utilization: `NO_DATA`. | Light tier is supplied by the commission; no current numeric benchcard was provided. Do not infer capacity from the web map row. |
| `onexstation` | No colony compute allocation; retain its node/building identity | Reserved for the lab. RAG and harness remain fleet-wide app duties there, as on other app nodes. Their current installation and use were not remeasured here. | Sovereign's 2026-10-30 station decree. Lab reservation excludes this node from the game-workload tiering; it does not exclude it from the app fleet. |
| `cabin` | Keep existing tutorial building `b-cabin` | Public web snapshot at [`preceptoros-web/main 97bf5d4`](https://github.com/piskyRpapalo/preceptoros-web/tree/97bf5d4403ed7172ed22fa6a13043ea0dbc5a39b) marks `cabin` `LIVE`; app poll and local capacity: `NO_DATA`. | The web seal belongs only to that pinned snapshot. It is not evidence of app liveness or a compute benchmark. |

The four canonical types not allocated by this candidate table are `lapidas`, `botella`, `monumento`, and `nombres`. Their type-specific workload and a type-to-tier source are `NO_DATA`; this plan does not assign them by analogy. Every candidate's current utilization, `carga` value, and app `LIVE` status remain `NO_DATA` until a source provides a measured receipt. No model is installed, started, or moved by this proposal.

## Rendering proposal

Keep one building row per canonical map node. Choose a candidate type from an explicit capacity-tier mapping only after review; preserve the existing canonical projection, deterministic frame rules, bounded frame size, and reduced-motion behavior. Render measured compute load only from a receipt for that node; until then use the canon's neutral `NO_DATA` treatment. Do not expose model names, remote endpoints, private paths, or node secrets in map frames. App services remain read-only declarations under `odd/tasks/building-service-authoring.md`.

## Review gates

- Confirm or change the proposed type-to-tier candidates before implementation. The nine-object canon does not define this mapping.
- Keep host RAM, CUDA memory, and throughput in separate fields. A CPU sample never proves CUDA placement.
- Reuse the one-map web state; do not publish app-side liveness or duplicate colony state.
- Split implementation into one PR per slice. A later PR must carry its own tests, seal if it changes served web files, and receipts. No installation or runtime claim follows from this plan.

Evolutionary north: help the system find its way to flow, free the Sovereign, and learn with him. This guides later slices; it is not an acceptance test for this plan.
