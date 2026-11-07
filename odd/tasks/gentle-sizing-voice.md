# COMMISSION · VOICE · measured chat proportions

## Problem
The proposed app anatomy does not yet match the documented Gentle Dot reading
width and its conversation composer scrolls with the messages.

## Outcome
Use the documented web reading width (780 CSS pixels) and dot size (72 CSS
pixels), with a separately scrolling conversation and anchored composer.

## Affects
The proposed single-page app, on top of app #186.

## Constraints
Retain the existing native transition and accessible controls. This is a web
layout; the separate 420 × 640 native floating window is not implemented here.

## Open questions
The canonical Acho drawing and native desktop window need separate integration
and visual verification on real devices.
