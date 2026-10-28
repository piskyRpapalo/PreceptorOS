# Colony ground layers fixture

This fixture-only iteration is stacked on the density proposal at `3c3aaa79e9bc0f398e8778532376d4b627a9ae5a`. It explores a repeated fine patch, a world-coordinate value field and coordinate-hashed scatter. The clearing and edge band are explicit inputs. Props and inhabitants are ordered by screen y; their motion continues only on explicit cycle input. The preview is rendered from the same ground function at reference size, then scaled down and cached.

Technique source: [terrain code at pinned revision](https://github.com/androoAGI/starnet/blob/8e8311987eaf2ddc49cfc1e31f2dc3a7dcba3bec/frontend/app/terrain.js). The implementation here is independently written with native primitives; it imports no external assets, identity or character. Before evidence is app #132; the PR must carry the reference and after captures. The fixture remains disconnected from production.

NO_DATA: weakest-live-device identification, 30/60 fps, measured reduced-motion behavior and cross-surface bitmap parity. A local headless repeatability check does not establish those measurements. No live nodes or dialogues are represented.

The preview is explicitly the ground layer before the floor mask, not a preview of inhabitants or the entire map. Scatter is computed from world cell coordinates without a stored map, with a bounded viewport and an explicit supported origin range of ±1,000,000 reference units; the fixture does not prove a mathematically infinite field. A cached crown uses hard interior 2-pixel marks and transparent holes. Visual fidelity and canopy readability await human review.
