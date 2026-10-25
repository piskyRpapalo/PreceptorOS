# Shared web and app style contract (proposal)

**Status:** propose-only. This contract defines names and responsibilities; all visual values are deliberately empty. Stage 2 begins only after the web landing piece has merged with its required human signature. At that point the app lane reads the exact signed web-main revision and fills the slots from measured web values.

## Goals and boundaries

- One semantic token vocabulary consumable as CSS custom properties by both web and app.
- One source of approved values, exported to each lane by a later, separately reviewed integration piece.
- Preserve semantic state, accessible contrast, reduced motion, and per-screen behavior while sharing the visual language.
- Do not copy screen-specific layout, animation, game geometry, or component markup into the token contract.
- Do not use current app values as defaults. Empty slots mean no shared value has been approved yet.

## Token schema

The canonical schema is a CSS custom-property contract. The YAML view below lists each slot once; values are empty until Stage 2. The same names map directly to `:root { --style-...: ...; }` in either codebase.

```yaml
schema: preceptoros.shared-style.v1
source_revision: ""
palette:
  canvas: ""
  surface: ""
  surface-raised: ""
  ink: ""
  ink-muted: ""
  border: ""
  accent: ""
  accent-ink: ""
  success: ""
  warning: ""
  danger: ""
  focus: ""
  overlay: ""
type:
  family-ui: ""
  family-display: ""
  family-mono: ""
  size-caption: ""
  size-small: ""
  size-body: ""
  size-subhead: ""
  size-heading: ""
  size-display: ""
  line-body: ""
  weight-regular: ""
  weight-emphasis: ""
  weight-strong: ""
spacing:
  1: ""
  2: ""
  3: ""
  4: ""
  5: ""
  6: ""
  7: ""
radius:
  control: ""
  card: ""
  panel: ""
  pill: ""
border:
  width: ""
  width-strong: ""
  style: ""
  focus-width: ""
  focus-offset: ""
voice:
  principle: ""
  sentence-length: ""
  action-label: ""
  status-message: ""
  error-message: ""
  uncertainty-label: ""
```

## CSS export names

| Schema slot | CSS custom property |
|---|---|
| `palette.<name>` | `--style-color-<name>` |
| `type.family-*` | `--style-font-<suffix>` |
| `type.size-*` | `--style-type-<suffix>` |
| `type.line-body` | `--style-line-body` |
| `type.weight-*` | `--style-weight-<suffix>` |
| `spacing.<n>` | `--style-space-<n>` |
| `radius.<name>` | `--style-radius-<name>` |
| `border.width`, `width-strong`, `style` | `--style-border-width`, `--style-border-width-strong`, `--style-border-style` |
| `border.focus-width`, `focus-offset` | `--style-focus-width`, `--style-focus-offset` |

Voice fields are editorial rules, not CSS values. Both products use them for visible action, status, error, and uncertainty copy. The contract does not make a visual state look successful when its data is absent; existing `NO_DATA`, pending, blocked, and error distinctions remain explicit.

## Slot rules for Stage 2

1. `source_revision` is the exact web-main commit that contains the human-signed landing/style piece. No web branch or unsigned preview supplies canonical values.
2. Fill each value from the merged web implementation and cite the measured source path in the Stage 2 receipt. If the web does not define a slot, leave it empty with `NO_DATA` and a cause; do not infer a value from a screenshot.
3. Palette values include their semantic role. Success, warning, danger, and focus remain distinct even if the approved visual system uses related hues.
4. Responsive sizing, motion, and layout stay in screen stylesheets. They are not silently folded into spacing or type tokens.
5. Each adopting screen group keeps a compatibility mapping until its own reviewed migration removes its local variables. The shared names are additive during migration.
6. Both lanes pin the same schema version and source revision. A later change to the contract or source values is a new reviewed piece.

## App adoption order

The app inventory identifies three distinct shipped shells and two auxiliary surfaces. The least costly adoption order is:

1. **Privacy prototype** (`interface/privacy_toggle.css`): map its duplicated semantic colors to shared names first; it is not served and has a compact state matrix for checking token meaning.
2. **Face trio** (`interface/face/face*.css`): adapt shared semantic colors, type, radius, and borders while retaining the deliberate quiet/zones/terminal layout overrides. Review all three variants together because they share styles and scripts.
3. **Command app** (`interface/app.css`): migrate its shared tab shell and all panels in one screen-group PR; preserve status states, dark mode, and focus treatment.
4. **Dashboard plus console** (`interface/desnuda.css`, `interface/consola.css`): map semantic colors and typography after an explicit decision to move away from native system colors. Keep console layout rules local.
5. **Creation reader** (`assets/creation-view/creation.html`): replace inline visual constants with shared tokens while retaining the read-only verified-creation layout.

Each numbered group is a separate `REQUIRES_FIRMA` piece with its own before/after inventory and style checks. This stage creates no token values and changes no screen.
