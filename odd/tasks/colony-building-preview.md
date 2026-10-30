# Cabin building preview · app proposal

## Scope

Prepare the app-side IC4 building frame and a local visual review fixture. The fixture is not loaded by `interface/app.html` or the face pages; it does not change the shipped app, poll a node, create a service, persist state, or claim app liveness.

The pinned source is web main `0977f4c` (2026-10-30), `public/openworld/estado.json`: `cabin` is the sole LIVE row; `b-cabin` is its authored building row. The other declared rows are NO_DATA and their buildings must stay hidden. They are represented by generic fixture IDs here; no device identifiers are copied into the app tree. The app poll is NO_DATA. The building silhouette and six explicit growth steps adapt the signed web IC4 piece (`web#410`, source `public/game/colonia_edificios.js`). The app uses its canonical `ColonyProjection` convention. App/web pixel parity remains NO_DATA because their projection implementations differ.

The building's frame inherits the pinned web node seal only inside this labeled fixture. It is not evidence of app-side liveness. Service source, digest, and execution remain NO_DATA; resolving a building service is still the read-only contract in `colony/services.js`.

## Checks and evidence

- `node colony/building_frames_cases.cjs` exercises the pinned one-LIVE-node snapshot, hidden NO_DATA buildings, missing building rows, ownership mismatch, six-step growth, reduced motion, determinism, frame size, and forbidden clock/network inputs.
- `colony/building_preview.html` is a local visual fixture with explicit step controls and text equivalents; no timer or network. Its screenshot is evidence of this fixture only, not the shipped app or a device.
- Device poll, app deployment, services, building approval, and app/web bitmap parity remain NO_DATA.

## Log

- 2026-10-30: prepared one cabin candidate from the public web snapshot. No other app node is asserted LIVE. Preview and PR are propose-only for human review.
