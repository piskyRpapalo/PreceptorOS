# App public-naming inventory and gate

## Objective
Inventory public App names against THE LEXICON, Rosetta and collision law; add a gate that fails on unallowlisted public-name entries and proves red-on-sabotage. Subsequent renames land one piece per draft PR.

## Scope
- Enumerate shipped route names, user-facing surface names, asset labels, package/install names and Bubble/Rosetta terms; distinguish proper/public names from translated sentences.
- Pin each source revision and search expression; preserve aliases/history and never rewrite signed lore.
- Define a reviewed allowlist of exact canonical English or approved house names. Unknown entries fail closed; no silent auto-translation.
- Record proposed replacements and collision evidence, then split actual name changes into independent PRs.

## Constraints
- Base `origin/main`: `5b6c24f129c2f651b16190c45ac3c57d99c51aea`; branch `mistral/app-public-naming-20261028`.
- `CONTRIBUTING.md` reserves signed doctrine and says proposals belong in an issue; no canonical Lexicon/Rosetta/LORE edits here.
- The official-name source `docs/lexicon.md` on WEB main is itself `PROPOSAL / REQUIRES_SIGN-OFF`; treat non-signed rows as candidates only.
- App main has no `odd/` tree: `NO_DATA · ODD source absent from this checkout`; this card is written before implementation.
- `INTANGIBLE` is proposal-only in a separate private receipt; never make it a public canonical name.
- Each number carries revision, date, command and scope. Public artifacts contain no private identifiers.

## Work strategy
Feature-branch-chain. First PR is only the inventory + automated gate. Actual renames are later, one source-name family per draft PR.

## Tasks
- [x] N1: Capture and hash the static route/name inventory from pinned main; dynamic runtime surfaces remain explicitly NO_DATA.
- [x] N2: Classify measured rows against pinned Lexicon, Rosetta and collision law; preserve unresolved rows and the proposal-only status.
- [x] N3: Implement exact allowlist gate and label/route sabotage cases.
- [x] N4: Run App gate twice; keep runtime gaps explicitly NO_DATA.
- [x] N5: Open a draft PR and publish scrubbed receipts in the PR and buzon#19.

## Evidence
See `docs/naming/app-public-name-inventory-20261028.md` and `docs/naming/app-public-names-allowlist.json`. Directed check: `python3 -m unittest test_public_names` → 3/3; `python3 test_public_names.py --sabotaje` → 2/2 injected changes detected. Full App pass 1 and pass 2: each `./bin/pruebas` → 1,161/1,161, 90 suites, 6 runners; 10 skipped checks; sabotage batch 47/47. Gate n=2 is green. Allowlist SHA-256 `1029547c677d4e5dd6158aa109055fa0dfe1f643f1f933f1228fa77e51895f4b`. Static count on Linux x86_64, Python 3.14.4, 2026-10-28: 68 static routes, 26 literal API path strings, 13 executable commands, 68 name-bearing labels. Runtime-generated names, response bodies, dynamic assets and CLI output are explicitly NO_DATA; see inventory causes.
