# Isometric colony: app core

Law: the feature document and commission comments at https://github.com/piskyRpapalo/preceptoros-web/pull/387. IC1 and IC2 are a portable proposal; this slice does not assert that a node is live.

## Contract

`colony/core.js` creates detached `colony/1` state with node, building and unit rows. Axial integer coordinates use a fixed projection: x = 48q + 24r, y = 12r. The complete serialized state must be strictly below 1,024 UTF-8 bytes. The tutorial base resource is named mana; its amount remains NO_DATA until a source supplies a measurement. Rendering a building requires its state row; this core does not render buildings.

## Log

- 2026-10-28: NO_DATA: the precise shared projection and vector/1 bitmap are not specified in the feature law. The integer projection and synthetic bitmap are a portable proposed convention pending coordination; they do not establish web/app bitmap parity.
- 2026-10-28: NO_DATA: live node poll endpoints, freshness policy and mana measurement are not established by this slice. A fixture is not a live reading.
- 2026-10-28: NO_DATA: eye fidelity and first motion on the weakest live fleet device have not been measured. The synthetic raster gate is not a browser or device measurement.
