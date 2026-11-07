# App World as a packaged mini surface

## Scope

Carry the visible app shell from the mini-window work into the trunk that starts at the current main head. The shell layout, typography, tab row, settings controls, and their scripts are app assets served locally and included in the app cache.

## Visible behavior

- The World panel uses the available space between the app header and composer.
- The app uses a smaller type scale while retaining 44 px tab targets.
- Boundary remains a node-policy surface with an honest NO_DATA state; the redaction filter lives in Settings.
- Device storage persistence is requested only after an explicit click and reports the browser result.
- The app document served at `/` and `/app.html` remains byte-identical.

## Network boundary

The OpenWorld map is an optional, separately hosted activity loaded only when its tab is opened. If it cannot be reached, the app reports the cause and keeps retry and fallback access available. The shell and its styling do not depend on the OpenWorld service or on a particular local window wrapper.

## T1 invariants

Keep the current app trunk and route policy: legacy face, dashboard, and standalone chat pages remain retired; the existing API routes and protected behavior are unchanged. The service worker precaches the current app assets and does not restore retired page routes.

## Verification

The full app gate is required for the draft. Record measured test results in the PR and do not treat an unrun gate as green.
