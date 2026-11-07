# COMMISSION · VOICE · local app window

## Problem
The existing desktop launcher opens the application as a browser tab; the
requested small window is not available through that launcher.

## Outcome
Offer an explicit local launcher for the existing app in a Chromium-family
app window, requesting a 420 × 640 window on the user's display.

## Affects
A new optional local launcher. The existing install and service remain intact.

## Constraints
No package installation, browser download, credential access or remote URL.
Window-manager sizing is a request, not a guarantee. This is not an always-on-
top window or an independent desktop dot.

## Open questions
Real desktop behavior, display scaling and the separate always-visible pixel
head need a test on the user's system and a native host design.
