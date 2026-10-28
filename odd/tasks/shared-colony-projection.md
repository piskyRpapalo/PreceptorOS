# Shared colony projection

The [twin commission](https://github.com/piskyRpapalo/preceptoros-web/pull/387) requires a single projection contract before claiming web/app parity. Proposed `colony-projection/1`: axial integer `q,r`, reference origin `(0,0)`, reference pixel position `x = 48q + 24r`, `y = 12r`, as already implemented in app `colony/projection.js`. Consumers apply the same explicit viewport transform after this reference position; the transform and raster conditions must also match for bitmap parity. Negative coordinates are valid. Unsafe input or projected coordinates are rejected. Node appearance still requires independently observed liveness.

The current web map uses `isometric_floor_projection.js` with `(col-row)*28,(col+row)*14` and then a scale of 1.5. This is not the proposed axial formula. Its old coordinates are not silently reinterpreted: the web owner must explicitly migrate the node layout and renderer and measure their output. This app slice proposes a contract and judge, not an already shared web implementation. The existing app screenshots in [app #120](https://github.com/piskyRpapalo/PreceptorOS/pull/120) are before evidence; after bitmap, web/app parity, live polling and weakest-device motion are NO_DATA because this slice renders nothing.

## Log

- 2026-10-28: `colony/projection.js` was in app main before this proposal. Choose it as the proposed shared reference, reuse it rather than reimplement it, and publish the test vectors for the web seam. The web's migration and exact visual match remain unmeasured.
