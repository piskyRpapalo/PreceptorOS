# PRECEPTOR.md · The contributor contract

> **Status: FIRMO del Soberano** — signed by the architect, David Pecero Caballero, 2026-10-12.
> One page. Tool-agnostic: any ingestion method your AI uses is fine.

---

## What this is

PreceptorOS is a local-first companion application: local memory, local
inference, no cloud, no telemetry. This repository is the **APP** part of a
three-part ecosystem — **WEB** ([preceptoros-web](https://github.com/piskyRpapalo/preceptoros-web),
the public gateway) · **APP** (this repo) · **LAB** ([lab](https://github.com/piskyRpapalo/lab),
measured benchmarks). Your node as a contributor **is this app**: it installs
on the device as blocks under a size ceiling plus a checksum manifest,
assembled locally. The path for a new human — step-by-step guides — lives at
[preceptoros.org](https://preceptoros.org), not here.

## The doctrine, in one line

**Silicon proposes, carbon signs.** No autonomous execution of value
operations. A machine may prepare, suggest, and measure; a human signature
precedes every consequential action.

## The two things we ask

1. **Respect the ceilings.** Pure standard library where possible. No
   telemetry. No external requests at load. Human-in-the-loop before any
   consequential action. Files stay under the size ceiling, and the test
   suite must be able to fail — a suite that cannot go red proves nothing.
2. **Share back.** If you build a tool that adapts natively to the app, it
   belongs here next to the rest. That is the whole social contract.

## How to contribute

Pull requests, not issues: a PR carries its own measurement; an issue only
carries an opinion. Before your first PR, read `CONTRIBUTING.md` (language
policy, sabotage-tested suite, how to run it) and `SECURITY.md`. A missing
datum is reported as `NO DATA` with its cause — never invented, never padded.

## Interaction contract · FIRMO addendum · 2026-10-15

Treat every participant as an interactor: the person using the system, an AI
model or agent, the app, a device or node, an automation, and an outside
visitor or tester. A participant may be absent; show `NO DATA` and why instead
of implying a live connection or capability.

For each consequential interaction, make the source, requested action,
available evidence, and next responsible actor clear. Models and automation
may explain, measure, and prepare proposals; the person with the relevant
authority approves consequential actions, and the local app reports whether
the action actually ran. A device or node reports only what it measured
locally. Never infer a shared state, delivery, or agreement from a listed
identity or an attempted message.

Keep interaction usable across touch, keyboard, assistive technology, and
machine-readable interfaces where the feature supports them. Expose the same
state and reason through each supported channel; do not make one interactor's
view silently authoritative over another's. Preserve local data boundaries,
and do not add network traffic or telemetry to make an interaction appear
live.

## What you get

A working local-AI companion you can read end to end: plain-file local
memory, measured claims (each number with its command, machine, and date),
tools that measure rather than promise, and an ecosystem whose numbers are
honest even when the honest number is "we have not measured that yet."
