# PRECEPTOR.md · The contributor contract

> **Status: PROPUESTA · REQUIRES SIGNATURE** — not in force until the author signs.
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

## What you get

A working local-AI companion you can read end to end: plain-file local
memory, measured claims (each number with its command, machine, and date),
tools that measure rather than promise, and an ecosystem whose numbers are
honest even when the honest number is "we have not measured that yet."
