# Isometric map twin

Commission: [one-map decree](https://github.com/piskyRpapalo/preceptoros-web/pull/387). The app must replace its old island world with the web colony, preserve node content as shared catalogue entries, keep theme separate, and measure identical render bytes. The existing app captures are in [app #120](https://github.com/piskyRpapalo/PreceptorOS/pull/120).

The app's current `colony/projection.js` maps axial `(q,r)` to `(48q+24r,12r)`. The current web `global_map.js` instead calls `isometric_floor_projection.js` with its own coordinates and scale. They are not the same numerical projection; a byte-identical visual cannot be asserted by merely sharing their names. The web map accepts a static `nodes` array and treats membership as liveness; a poll contract is not established. These are implementation facts to resolve in coordination, not a claim that either surface is live.

## Log

- 2026-10-28: NO_DATA: a common pixel fixture, actual polling source, weakest-live-device ranking, three shared skins, and after screenshot do not yet exist in this slice. Current web core is recorded as a pinned comparison fixture; it is not a served app render.
- 2026-10-28: authoring proposals app #122 and #123 remain open. Their signatures and landing are not inferred. Further work may be built as proposals without merging them.
