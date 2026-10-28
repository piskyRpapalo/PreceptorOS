# App Bubble audio accessibility

## Objective
Make the App's shared `preceptoros.bubble/1` world audibly operable, with explicit user consent, keyboard controls, screen-reader-readable status, deterministic narration and honest missing-voice causes.

## Scope
- Audit current `interface/face/` radio/speaker route and the existing local voice modules (`voz.py`, `tono.py`, `oido.py`, `canales.py`).
- Extend the existing world surface; preserve byte parity of the pinned Bubble trunk unless the task proves a necessary coordinated change.
- Add source-level tests that can go red for speech consent and accessible status, plus a sabotage case. Exercise the real browser through a local isolated PWA session; retain NO_DATA for untested assistive technology.
- Update the offline/PWA inventory and version fingerprint if served files change.

## Constraints
- Base `origin/main`: `5b6c24f129c2f651b16190c45ac3c57d99c51aea`; branch `mistral/app-bubble-audio-a11y-20261028`.
- App AGENTS: no merge/sign/deploy; draft PR `REQUIERE_FIRMA`; zero network reporting; no private IDs; report browser/device behavior only when exercised.
- Public labels and new names are English/approved house terms. Existing multilingual message bodies remain language content; this feature does not erase translations.
- No sound before an explicit user action. No mic capture unless a separate, explicit user gesture permits it; no voice transcription is submitted automatically.
- `origin/main` has no `odd/` tree (`NO_DATA · no ODD source tracked in this checkout`). Record this local feature card before implementation and follow the commissioned explore → implement → proportionate checks loop.
- Doctrine changes are proposed only; signed lexicon, Rosetta, collision law, LORE and ARQUETIPO remain untouched. `INTANGIBLE` status stays proposal-only in the private note.

## Work strategy
One coherent audio surface/test PR; `feature-branch-chain` is selected for unattended work. No delegation.

## Tasks
- [ ] A1: Capture source fingerprints and baseline state from pinned App/WEB/Study revisions.
- [ ] A2: Add explicit consent and accessible speech/status behavior on the existing Bubble surface, keeping fixed text and local-only voice.
- [ ] A3: Add keyboard/screen-reader, no-consent, missing-voice and sabotage tests.
- [ ] A4: Run directed and full App gates twice; measure browser proof or keep browser behavior `NO_DATA` with cause.
- [ ] A5: Produce scrubbed receipt, draft PR, and buzon#19 receipt.

## Evidence
- Source tree fingerprint: App `origin/main` `5b6c24f129c2f651b16190c45ac3c57d99c51aea`; baseline `face.js` blob `a420df5ddaf822e5cc6671e2073c037d1f74421e`, `face_hud.js` blob `ef0800803448299ff824401be9d41bde7c13b637`, `basic.html` blob `109b51cb021d65986050622831dba9e7289b3a8e`, `test_face.py` blob `2fc6fdecd378ac4edb8da9a2eb1c76777e8ae601`.
- Source audit: `voz.py`/`tono.py` are local CLI narration components; `oido.py` is microphone/transcription and deliberately remains outside this change; `canales.py` is the local message channel, not an audio bridge. No browser bridge from these modules is present at the pinned base. Microphone capture/transcription remains absent.
- Implementation: native button activation must have `Event.isTrusted === true` before sound or speech actions; external `act('sound'|'read')` calls do not grant consent. Voice is local browser speech synthesis when available; spoken text is fixed and deterministic, but the native voice/timbre is device-dependent and not deterministic. Missing local voice retains visible `NO_DATA` cause. The radio line is an announced status in all three pages.
- Service-worker route inventory already includes the three face pages and their scripts; `test_face.py` verifies linked resources are served and cached. The changed served pages/scripts are now included in `version.py`'s armazon fingerprint.
- Directed check on Linux x86_64 (host identifier scrubbed), Python 3.14.4, 2026-10-28: `python3 -m unittest test_face test_version` → 14/14 pass.
- Full App pass 1 on same environment/date: `./bin/pruebas` → 1,160/1,160, 89 suites, 6 runners; 10 skipped checks reported by their suites; runner sabotage batch green (45/45 detections). Working tree was uncommitted during this measurement.
- Browser measurement: Chrome `155.0.8059.39`, headless, Linux x86_64, 2026-10-28, local loopback PWA and temporary database. A public API call and synthetic `.click()` left audio off; trusted Space-key activation exposed the radio with `role=status` and `aria-live=polite`; the read action returned `NO_DATA` because Chrome exposed zero local English voices; the sound control toggled on/off by keyboard. No live deployment or physical device was used.
- Screen-reader/assistive-technology behavior: `NO_DATA`, cause: no AT runtime was exercised. Semantic status and button properties were measured in the browser DOM only.
- Full App pass 1 and pass 2 on the same environment/date: each `./bin/pruebas` → 1,160/1,160, 89 suites, 6 runners; 10 skipped checks; sabotage batch 45/45. The required gate n=2 is green.
