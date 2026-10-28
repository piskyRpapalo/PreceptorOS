# Walking colony render fixture

This proposal renders the landed `walking_frames.js` fixture with `colony-projection/1` as native CSS bubbles. Input cycles are explicit; a button advances a cycle, and reduced-motion removes the transition. The fixture has a map above a separate chat panel; it does not connect a model, account, reward, real node, or production app route. The three synthetic figures use house styles, not reference characters or assets.

Before: the locally captured app surface in [app #120](https://github.com/piskyRpapalo/PreceptorOS/pull/120). The reference visual-check capture is a comparison of technique and visual feel only. It is not a parity target or evidence of an adapted asset. Compare the screenshots in the PR: the fixture is sparse and lacks the reference's terrain detail and density.

30/60 fps budgets and weakest-device motion: NO_DATA until measured on the weakest live device. A headless screenshot comparison is not a frame-rate measurement. Web/app deployed parity, audio, service polling, dialogue, reward flow and first fight also remain NO_DATA. No imported reference assets are used.

Reference capture: locally cloned reference commit `8cd9d76b3bf5eddaec7d4ba88f0d1c0547a312dc`, synthetic `tools/visual-check.html`, headless Chrome with software WebGL. Screenshot is attributed to Jarren Rocks / Station-Sciences, whose repository carries the MIT license; it is evidence only, not part of the fixture or a copied character. The two webp evidence images are resized, lossy copies and cannot establish bitmap parity.
