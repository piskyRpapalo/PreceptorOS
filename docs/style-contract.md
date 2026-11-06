# Shared web and app style contract

**schema:** `preceptoros.shared-style.v1`
**source_revision:** `683d875274dc7cf9e75580569d2c0b135ac43187`
**Stage 2 receipt:** `source_revision: 683d8752` · pin ratificado por la FIRMA SOBERANO de esta pieza. The
web landing/style head is measured below; no value is inferred from a capture.

```yaml
schema: preceptoros.shared-style.v1
source_revision: 683d875274dc7cf9e75580569d2c0b135ac43187
palette:
  canvas: "Canvas" # public/assets/landing.css:6 --bg:Canvas
  surface: "Canvas" # public/assets/landing.css:6 --bg:Canvas
  surface-raised: "" # NO_DATA: no distinct raised-surface token in landing.css or openworld.css
  ink: "CanvasText" # public/assets/landing.css:6 --fg:CanvasText
  ink-muted: "color-mix(in srgb,CanvasText 72%,Canvas)" # public/assets/landing.css:9 --soft
  border: "color-mix(in srgb,CanvasText 20%,transparent)" # public/assets/landing.css:9 --line
  accent: "" # NO_DATA: no shared accent slot is defined by the measured landing styles
  accent-ink: "" # NO_DATA: no accent contrast foreground is defined
  success: "" # NO_DATA: no semantic success role in measured style sources
  warning: "" # NO_DATA: no semantic warning role in measured style sources
  danger: "" # NO_DATA: no semantic danger role in measured style sources
  focus: "" # NO_DATA: openworld focus uses currentColor; no distinct focus token
  overlay: "" # NO_DATA: no shared overlay token in measured style sources
type:
  family-ui: "system-ui,-apple-system,Segoe UI,sans-serif" # public/assets/landing.css:13
  family-display: "" # NO_DATA: no distinct display family in landing.css
  family-mono: "" # NO_DATA: no mono family in landing.css
  size-caption: "" # NO_DATA: no shared caption token
  size-small: "" # NO_DATA: no shared small token
  size-body: "16px" # public/assets/landing.css:13 font-size:16px
  size-subhead: "" # NO_DATA: no shared subhead token
  size-heading: "" # NO_DATA: no shared heading token
  size-display: "" # NO_DATA: no shared display token
  line-body: "1.55" # public/assets/landing.css:13 line-height:1.55
  weight-regular: "" # NO_DATA: no shared regular weight token
  weight-emphasis: "" # NO_DATA: no shared emphasis weight token
  weight-strong: "" # NO_DATA: no shared strong weight token
spacing:
  1: "4px" # public/assets/openworld.css:7 .topbar gap 4px
  2: "6px" # public/assets/openworld.css:64 .cats gap 6px
  3: "8px" # public/assets/openworld.css:25 map/chat gap 8px
  4: "12px" # public/assets/openworld.css:15 map/chat padding 12px
  5: "16px" # public/assets/openworld.css:15 map/chat padding 16px
  6: "" # NO_DATA: no sixth shared spacing step established
  7: "" # NO_DATA: no seventh shared spacing step established
radius:
  control: "8px" # public/assets/landing.css:6 --radius
  card: "8px" # public/assets/landing.css:6 --radius
  panel: "8px" # public/assets/landing.css:6 --radius
  pill: "" # NO_DATA: no shared pill radius token
border:
  width: "2px" # public/assets/openworld.css:1,6 radio-chat and controls
  width-strong: "" # NO_DATA: 3px at openworld.css:6 is an outline, not border width
  style: "solid" # public/assets/openworld.css:1,6
  focus-width: "3px" # public/assets/openworld.css:70 :focus-visible
  focus-offset: "2px" # public/assets/openworld.css:70
voice:
  principle: "" # NO_DATA: no editorial voice slot in the web source
  sentence-length: "" # NO_DATA: no sentence-length rule in the web source
  action-label: "" # NO_DATA: no shared action-label rule
  status-message: "" # NO_DATA: no shared status-message rule
  error-message: "" # NO_DATA: no shared error-message rule
  uncertainty-label: "" # NO_DATA: no shared uncertainty-label rule
```

## Stage 2 measurement receipt

Pinned source: web `main` at `683d875274dc7cf9e75580569d2c0b135ac43187`, ratified by
the Sovereign's FIRMA for this piece. Citations are source paths in that exact
revision. Palette roles are taken from `public/assets/landing.css:6,9`; type values from
`public/assets/landing.css:13`; spacing declarations are from
`public/assets/openworld.css:7,15,25,64`; border/focus from
`public/assets/openworld.css:1,6,70`.
The semantic color/status bands used by the app portada are separately supplied
by its own Acho cores and are not exported as web shared-style tokens.

## Compatibility

The app's adopted portada maps its screen-local CSS roles to the named bands from
`interface/face/bubble/tabla_semantica.js`, `comic_tokens.js`, and
`comic_accents.js`. The shared contract remains additive; other screen groups
retain their existing mappings until their own migration pieces.
