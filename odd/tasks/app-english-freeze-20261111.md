# APP-EN-FREEZE-01 · English-only active APP renderer

**Owner:** Codex GPT-6 · 2026-11-11 · THE MARCH · PROPOSE-ONLY.
**Source:** Sovereign directive in the Mesa: APP/WEB interfaces stay English-only until further notice. Existing LAB/GitHub benchmark titles are a separate 11-language exception. [Mesa claim](https://github.com/piskyRpapalo/preceptoros-private-mesa/issues/3#issuecomment-6800652500).
**Branch base:** APP main ac26118bb5fc12169b943071dadf3ff0e3a4c984, after energy #244/#245 merged. Notebook #236 belongs to a separate owner.

## Problem and evidence

Current APP shell declares lang=es and app.js selects the Spanish dictionary before GET /api/perfil. Failure to fetch the profile preserves Spanish. Headless Chrome via SentinelX with fresh isolated browser profile: normal GET selected English; blocking only /api/perfil yielded lang=es and visible title 'Modelos locales'. This violates APP English-only policy and misstates the active document language for assistive technology.

## Adaptation, not duplication

Keep all nine dictionaries and persisted profile preferences as dormant historical data. Pin only the active PWA renderer to the English dictionary and document lang=en, with no profile-GET dependency to paint the shell. The CLI's separately tested language behavior is unchanged. Align the app.js resource version and service worker cache. No new panel, model, daemon, socket action, WEB or user database changes.

## Measurable gates

- Static negative test: reject lang=es, a non-English default dictionary, a stale precache, and profile GET dependency for rendering.
- Isolated Chrome on a temporary source server: ordinary boot and deliberately blocked profile GET both render lang=en and English labels.
- Python, canonical bin/pruebas with sabotage checks, exact-head CI, preferably two independent runs. Separate actual measurements from NO_DATA.

## Limits and next step

NO_DATA: complete elimination of every historical non-English fallback when JavaScript is disabled, physical Android TalkBack/speaker, Vercel deployment revision, separate WEB English-only rendering. These need their own source/device evidence, not automatic claims. A no-JS HTML audit can be a separately reviewed follow-up.

## Collision fence

Energy #244/#245 already merged. Notebook #236 pre-dates newer app/SW versions and must be rebased by its owner. Human FIRMO gates merge; no preceptor may forge a signature.
