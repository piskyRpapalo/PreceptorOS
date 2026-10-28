# Isometric map twin

Commission: [one-map decree](https://github.com/piskyRpapalo/preceptoros-web/pull/387). The app must replace its old island world with the web colony, preserve node content as shared catalogue entries, keep theme separate, and measure identical render bytes. The existing app captures are in [app #120](https://github.com/piskyRpapalo/PreceptorOS/pull/120).

The app's current `colony/projection.js` maps axial `(q,r)` to `(48q+24r,12r)`. The current web `global_map.js` instead calls `isometric_floor_projection.js` with its own coordinates and scale. They are not the same numerical projection; a byte-identical visual cannot be asserted by merely sharing their names. The web map accepts a static `nodes` array and treats membership as liveness; a poll contract is not established. These are implementation facts to resolve in coordination, not a claim that either surface is live.

## Log

- 2026-10-28: NO_DATA: a common pixel fixture, actual polling source, weakest-live-device ranking, three shared skins, and after screenshot do not yet exist in this slice. Current web core is recorded as a pinned comparison fixture; it is not a served app render.
- 2026-10-28: authoring proposals app #122 and #123 remain open. Their signatures and landing are not inferred. Further work may be built as proposals without merging them.
- 2026-10-28: reference sources pinned from web main `26433860537588cf11c8236cb78d2bde937061b8`: `global_map.js` SHA-256 `c7769e8c7858211ea18f64c37c29ec6dd2e2652ecab1ab1e4674e0d142ef7191`; `isometric_floor_projection.js` SHA-256 `56bec1e57cbc68d9e3803139e9a49ff55a487147f0dd6d4113c5d029669e16f7`. The fixture judge checks source bytes, frame ceilings and repeatable scene serialization. It does not test pixels, retirement or actual liveness.
