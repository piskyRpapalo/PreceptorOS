# App public-name inventory · 2026-10-28

**Status: PROPOSAL · inventory and fail-closed gate only. No public name is renamed or promoted by this artifact.**

## Pinned sources and method

- App base: `origin/main` `5b6c24f129c2f651b16190c45ac3c57d99c51aea`.
- Route table: `bin/preceptoros-pwa` blob `f5de9ca548e621c77006c44b388cf25079adff82`.
- Manifest: `interface/manifest.json` blob `fc577f703ceee4bafa2f90cff57abacc221467e6`.
- App shell: `interface/app.html` blob `94f347d85249decc41a721013e1a39a6843d25fb`; `interface/dashboard.html` blob `76d5b17335d6a34c92ddddd970e129a736e18d8b`.
- Language registry: `textos.py` blob `acb855c3aca53d00bcd0a27c7c979c50cdbc7ff7`; `textos_lenguas.py` blob `e1e0a570d2342697c1e55e62abca7dc1812d332f`.
- THE LEXICON (proposal, not signed): WEB `origin/main` `07df88e7e1195bc95a1f61dfd8bcc4b15359a695`, blob `4b1952925b7d5bb7583ec12cc611bc50f7674afc`.
- Rosetta: Study `origin/main` `379981243031f0bcdaf808cbe1989a4e42a66f11`, blob `09e8ecf5d5ffb038ca118d17bd3dab9002d4b339`.
- Collision law: same Study revision, `10-collisions.md` blob `326b769ce55b836b85831518d543c078133b7fe6`.

Search expressions/commands: `git show origin/main:bin/preceptoros-pwa | rg -n 'ESTATICOS|/api/'`; `git show origin/main:interface/manifest.json`; `git show origin/main:textos.py | rg -n 'DEFECTO|IDIOMAS|TEXTOS'`; `python3 bin/auditar_nombres_publicos.py`. The command loads the pinned checkout's route table, records each static route, extracts literal `/api/...` paths, executable names under `bin/`, and title/heading/button/label/accessibility names from served HTML plus manifest name fields. Every collected name is bound to its source file in the catalog. The exact allowlist is `app-public-names-allowlist.json`.

## Measured coverage and limits

On this checkout, 2026-10-28, the inventory found **68 static routes**, **26 literal API path strings**, **13 executable command files**, and **253 source-bound title/heading/button/label/accessibility/manifest entries**. These counts are from `python3 bin/auditar_nombres_publicos.py`; they are not counts of all runtime strings.

The gate fails closed if a static route, literal API path, executable name, or collected name-bearing label is added, removed, or changed without updating the allowlist. The two sabotage cases inject a new label and a new route; both must be detected. It does not translate or rewrite content.

**NO_DATA:** names assembled at runtime inside JavaScript/Python, names in API response bodies, image/SVG text, generated creation packages, CLI output, and every asset loaded dynamically outside `ESTATICOS` are not parsed by this gate. Cause: the first gate is intentionally restricted to a deterministic source index plus server-rendered HTML structure; no complete runtime capture was made. These remain explicit follow-up inventory work, not implicitly clean.

The App declares nine language columns in `textos.py`; language content is not classified as a public name here. A bilingual content audit is separate from naming labels and needs its own mapping. No source row is rewritten as part of this tranche.

## Corpus-backed classifications

| Observed source/value | Corpus anchor and exact phrase | Status | Decision / unresolved rule |
|---|---|---|---|
| `PreceptorOS` · manifest and page titles | THE LEXICON §A: “The professional and literary evolution of the Sovereign.” Its method says every piece is proposed under its official English name. | `in use` in Lexicon; Lexicon itself is `PROPOSAL / REQUIRES_SIGN-OFF` | Keep as observed brand; do not infer that draft Lexicon status is a new FIRMO. |
| `Preceptor` · page labels | Collision list §Third wave: “PreceptorOS stays the brand; the bare word is a GREY AREA in education contexts.” | `KEPT · GREY AREA` in Study | Keep the compound product name; use qualified context for bare label. |
| `The Path` · App mode label | Rosetta §world-name resolution: “tronco (UI concept, cara.py) → the core of the Path; NOT the Trunk; homonym resolved by Mesa audit 2026-10-23.” | `resolved` for that concept | Do not substitute “Trunk”; exact App label reuse remains a proposed rename candidate. |
| `Zombie terminal` · face title | Rosetta's historical rows resolve “Zombis → the Risen”; another appended note preserves “zombie” as an informal alias. | `CONTRADICTION OPEN` for this displayed compound: game skin vs canonical people-name | Needs a per-piece choice; no automatic string replacement. |
| `Atlantis for children` · face title | No matching canonical row in the pinned Lexicon/Rosetta/collision files. | `NO_DATA` · no corpus name/collision row found by the pinned searches | Keep inventoried; collision result and replacement name need evidence. |
| `Mando`, `Hablar`, `Frontera`, `Cuaderno`, `Zonas`, `Modelos`, `Ajustes`, `Puerta pública` · labels | Rosetta rule: “Resolve Spanish to the English official (rename-winner).” It also says “History is append-only: an old folio speaks with the names of its date.” | `RENAME CANDIDATES`; not a corpus-backed winning-name set | One UI family per proposal. The proposed “front door” row is explicitly `RENAME-SUGGESTED; pending FIRMO with web seal G3`, so do not use it as settled canon. Generic English labels need collision checks before changing routes/IDs. |
| `comic_tokens.js`, `combate_ticks.js`, `tabla_semantica.js`, `taller.js`, `escuadron.js` · served asset/file names | Rosetta single-house rule: “The Rosetta points, never duplicates.” Collision law: official English winner; old name remains historical alias. | `RENAME CANDIDATES`; filenames are measured in served route inventory | Bubble trunk filenames are shared with WEB and pinned by exact hashes. App-only rename would break byte parity; each is a coordinated cross-repo proposal, not an App-only edit. |

The corpus contains no `INTANGIBLE` canonical entry in the pinned Lexicon/Rosetta/collision sources. **NO_DATA** · no entry found by searching `INTANGIBLE` in those revisions. Its status remains `PROPOSED`; this inventory does not coin or canonize it.

## Proposed sequence · one draft PR per piece

1. App navigation label family: `Mando/Hablar/Frontera/Cuaderno/Zonas/Modelos/Ajustes`; settle exact English house terms and preserve Spanish history/translation content.
2. Public-door labels: separate decision because Rosetta's “front door” is still pending.
3. Face variants and world labels: `Atlantis`, `Zombie terminal`, node labels; resolve collisions and distinguish theme names from canon people.
4. App-owned route/command names: rename only after the one-name decision per route family; compatibility aliases need explicit expiry and a redirect measurement.
5. Shared Bubble asset filenames: coordinated WEB+App proposal with parity tests; never rename only one copy.
6. Runtime-generated and API names: close the stated NO_DATA through an observed inventory, then add those rows to the gate.

No rename is included in this inventory PR. A changed catalog row alone is not authorization to alter a live name.
