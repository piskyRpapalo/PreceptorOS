# APP-NOTEBOOK-01 · Cuaderno operativo, no una segunda orquestación

**Codex App · GPT-6 · 2026-11-11.** Feature document under THE MARCH. **Proposal branch only; no FIRMO, merge or deployment.**  
**Mission vector:** F4/F7/B3/A6/I10 + ARTPLAY-08 (proposed). [Private Mesa swarm #12](https://github.com/piskyRpapalo/preceptoros-private-mesa/pull/12), [Mesa #3](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/3).  
**Read:** APP `AGENTS.md`, `interface/app.html`, `app.js`, `team.js`, `bin/preceptoros-pwa`, `bucles_edad.py`, APP-LIVE 01–05 handoff.

## Problem and source evidence

The original Notebook in APP `main` only contains captured chat prompts/answers and per-turn training consent. It is a legitimate privacy control but a poor window into Hexelion's actual work. `Harness` already has a `preceptoros.team/1` **style profiles** editor and `GET /api/harness` (timer view); neither proves that Claude Code workers are currently executing. The user explicitly asks that Notebook instead present their own configured agents, loops and WBR/MBR reviews and that the existing Notebook contents be removed from that tab.

## Design choice: one read-only projection over existing evidence

- Keep the nine-zone APP and existing routing: `cuaderno` stays the Notebook tab; no new app/port/scheduler.
- Move **training consent controls** into collapsed Settings, retaining current `/api/captura` POST/GET and per-turn withdrawal. Do not remove consent capability.
- Notebook loads only when its tab is opened (or Refresh pressed). Read-only `GET /api/notebook` is served by the existing APP PWA server; static `interface/notebook.js` uses textContent, keyboard-focusable Refresh and ARIA headings/status. Existing `GET /api/harness` is reused to show actual declared local timers without executing them.
- New pure `notebook_read.py` reads **only fixed local JSON filenames** from `Path(casa.raiz()) / notebook`, max 8 KiB agents and 4 KiB per review; rejects symlinks, duplicate JSON keys, invalid shapes and oversized content; no network, remote file path or subprocess.
- `OBSERVADO` means a *recent producer-declared heartbeat and referenced receipt*, **not process-live verified**; after 10 min mark `STALE`, future timestamps or absent input `NO_DATA` with cause.
- WBR/MBR entries remain `DECLARADO` until independent receipt verification is implemented. No automatic model-generated report is promoted to confirmed result.
- Backend never writes a report or starts an agent; Claude's own authorized writer/loop will supply sanitized records with explicit source provenance. This PR is UI+read-only contract, NOT the live swarm.
- No third-party fetch, analytics, microphone, remote memory, automatic signature, side effects or changed default port. JSON is no-store. App source stays self-contained and offline shell caches its new static module, never `/api/*`.

## Proposed producer files (source contract, not Babel authority)

`notebook/agents.json`:
~~~json
{
  "schema":"preceptoros.notebook-agents/0",
  "agents":[
    {"id":"claude-builder","name":"Claude Builder","role":"PR construction",
     "last_seen":"2026-11-11T10:00:00Z",
     "receipt_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
  ]
}
~~~
The hexadecimal example is synthetic, not a real verified receipt. Up to 12 agents, unique IDs, bounded role/name. Do **not** include source logs, prompts, repo paths, hostnames, emails or private identifiers. Producer should atomically replace file, mode 0600, after separate redaction and permission checks. A paused loop does not produce a fresh heartbeat.

`notebook/wbr.json`, `notebook/mbr.json`:
~~~json
{
  "schema":"preceptoros.wbr/1",
  "period":"2026-W46",
  "summary":"Example: one proposal accepted; independent checks pending.",
  "measured_at":"2026-11-11T10:00:00Z",
  "receipt_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
~~~
Use `preceptoros.mbr/1` with `period="2026-11"` for monthly. This file is a sanitized *display summary*, not the full cited report; a receipt ID without accessible backing proof is not sufficient to claim E2E. Missing report = `NO_DATA:file_missing`.

## Visual/audio/machine equivalence and native design

- HTML headings, cards and status use the existing APP tokens `--paper`, `--line`, `--ink`, `--warn` and grid; no extra icon set or competing Acho grammar.
- Machine reader receives `preceptoros.notebook-readonly/0` from one endpoint; UI uses exactly this payload plus the existing `/api/harness`, no narrative state store.
- A screen reader announces the status line, reads plain receipt field labels, navigates heading/Refresh; native voice may later narrate *these same IDs and causes*, but **spoken E2E is NO_DATA**. No sound without user gesture.
- The existing Harness tab continues to manage human-selected answer styles; do not conflate these with executable workers.

## Dependencies and collision / order

1. This branch was created against APP GitHub main `f1227e7` (SW cache v153), **not** against yet-unmerged local APP-LIVE patches 01..05, which reserve SW caches v154..v157. For that reason this PR deliberately reserves v158 and app.js?v19 / app.css?v15; it **MUST NOT MERGE** until rebased and retested after APP-LIVE-05 or its proven superseding equivalent. Do not force the patch stack.
2. User is independently commissioning Claude to configure real agents and report-generating loops; Claude should inspect current Nexo timers/Report generators before adding a writer. No second monitor or synthetic process state.
3. The former Notebook capture/consent card is deliberately preserved in Settings. If an alternative native Settings consent UI exists in a later APP patch, reconcile it before merge.
4. The existing Web welcome cleanup is already proposed in Web PR #794. This PR does not edit Web or remove its protected historic routes.

## Tests and evidentiary status

- `python3 -m unittest test_notebook_read -v` — seven pure reader tests + two static APP shell/route checks; synthetic only.
- `node tests/notebook_cases.cjs` — separate directed client projection checks; Node is not a mandatory dependency in the APP full Python gate.
- `./bin/pruebas` **twice** after rebase; the new test module is registered in `bin/pruebas`.
- `python3 -m unittest test_app_una_pestana test_pwa test_version` and interactive 360px/420px keyboard/a11y smoke, cache and consent withdrawal after merging to an isolated browser.
- Negative cases: missing source, duplicate JSON key, symlink, future/stale heartbeat, wrong schema, oversized file, malformed agent. A declared heartbeat must never be green `LIVE`.
- Evidence **currently:** GitHub code changes and test sources only. `NO_DATA: tests not executed in this connected GitHub session`; `NO_DATA: browser/hardware/device E2E not run`; `NO_DATA: real Claude producers not configured`; `NO_DATA: user has not accepted exact-head FIRMO`.

## Next concrete piece

Claude creates an independent **sanitized, atomic local writer** from actual existing WBR/MBR receipts and genuine runner heartbeats, with a declared source↔hash↔freshness contract and local read-only verification. Coordinate with Codex App in Mesa. Protect user data, avoid overwriting report history, and test loop stop/restart. This APP PR remains a rendering/reader PR, not loop control.

## Receipt log

- 2026-11-11 · Codex App design and code pushed to isolated GitHub branch; browser/live = NO_DATA; pending CI and independent BEACON. No deployment.
