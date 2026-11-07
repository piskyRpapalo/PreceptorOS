# COMMISSION · VOICE · Hexelion in the app chat

## Problem
The proposed app chat calls the Lab orchestrator instead of the existing
Hexelion station chat. Its model voice is therefore not Hexelion.

## Outcome
Send explicit turns through the existing Hexelion endpoint and show its
attributed answer, verified memory citations and unavailable causes.

## Affects
The app conversation surface on top of the proposed anatomy and sizing.

## Constraints
Reuse the existing local proxy and source-verification contract. Do not expose
credentials, invent a model identity, or retry an uncertain request.

## Open questions
Actual station availability and end-to-end behavior on the rack are NO_DATA
until tested there. A floating native desktop host is a separate piece.
