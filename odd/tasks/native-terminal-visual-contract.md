> Nota 2026-11-07: queda **DEPRECIADO por decreto 2026-11-07** todo lo relativo a acentos visuales derivados de pieles y al skin switch del dashboard. La terminal del norte lleva los colores del OpenWorld. Archivo histórico; no borrar.

# Native terminal — visual contract (Carril A)

## Objective
Declare the visual contract for the terminal BEFORE any implementation, as decreed by DECRETO · LA CADENA NATIVA (buzon#30 ·6647622152, served verbatim). Carril A acquires the visuals of the reference terminal for the app, piece by piece, each its own PR against `/api/orquestador` and the orquesta channel. This card is the contract Carril B consumes; later pieces contradict nothing here, they cite it.

## Why (NORTE 14)
The app is the mini-orchestrator with LoRAs, a telemetry laboratory, and the plug&play home where Hexelion lives. The terminal is the surface where the carbon talks to the local orchestrator (A1–A4) and where Hexelion will speak and act (Carril B mounts on A3). A piece that does not serve this is declared noise and does not ship.

## Reference (measured, never pasted)
Inspiration cited per decree: Gentleman-Programming/gentle-dot (MIT), no affiliation implied. Measured from its public tree on 2026-11-06; its values are REFERENCE MEASURES to re-derive ours — never code, never assets, never marks (Gentle AI™, Engram™, the rose).
- Panel: 420×640 px reference; translucent header (glass 0.82, 12px blur); dark-only tokens.
- Anchor: a 72pt window around a 66pt glyph; states idle · thinking · working · needs_you (amber + badge) · starting · error; only dashoffset/opacity/filter animate; reduce-motion respected.
- Chat: one continuous conversation; streaming; activity collapsed to one line; ask-cards inline.
- Composer: multiline; Enter sends, Shift+Enter newlines; Stop while working; a new message steers the run; mic shows a PARTIAL transcript that lands in the input FOR REVIEW before sending.

## Our tree (baseline, measured 2026-11-06, pinned to app main head `a27aef5df89e37050f66bc77a2e39ccbbe3ef014`)
- `interface/dashboard.html` — 17,903 B. Dark by default (`data-tema="oscuro"`, theme-color `#1a1225`); the bust ("Busto de mármol con un ojo encendido") is the current anchor; chat is `main#dice` (aria-live) over `form#escribir` with a single-line input (maxlength 280) and a dictation toggle ("Dictado apagado").
- `interface/face/basic.html` — 13,005 B. Skin tokens are named in the `#skin` JSON (`ui.accent` = `cyan` for basic); the node chooser names the aesthetics (Node Hexelion · the underwater world; Node Doggee · the survival terminal); `a.terminal-link` points to `/hexelion.html` ("Hexelion session") — the live surface Carril B mounts on.
- Voice modules exist locally (`oido.py` = microphone/transcription; `voz.py`, `tono.py`, `canales.py` = narration/channel). Browser-side partial dictation today: NO_DATA with cause (no browser bridge measured at this head; the a11y law — nothing is submitted automatically — stays).
- ODD law: `odd/README.md` (779 B) — English, no date in file names, stable checklist IDs, `./bin/pruebas` gates.

## The contract (each piece ships later, one PR per piece, in order A1→A4)
### A1 · The panel
- Geometry re-measured in OUR tree and declared against the 420×640 reference (the reference is the measure; our values are re-derived for the app's surfaces, mobile first).
- Translucent header over the chat; dark tokens RE-DERIVED from our own base (our measured dark is the `#1a1225` family — ours stays, theirs is never pasted).
- The accent is a CSS variable (`--acento`): each node paints its terminal with its aesthetic (basic = `cyan`, measured; zombie and atlantis measured from their skins in A1), and the user can change it (decreto LA TERMINAL); persisted locally; no accounts.
### A2 · The anchor
- NOT the reference's rose. The node glyph born in Acho/lore; candidates for the carbon's eyes, sentenced at FIRMA: la boya (the State Buoy, ideas13oct · LOS 9 OBJETOS) · el faro (the lighthouse, atlas/faro.py) · el hexágono (the HEX at {0,0}, the map's own seat). A2 ships the chosen one; the marble bust with the lit eye stays until it lands.
- States: idle · thinking · working · needs_you (amber `#f5a524` + badge = FIRMO pending of the carbon) · starting · error. Reduce motion respected: when the user asks for none, nothing moves.
### A3 · The chat
- One continuous conversation (no threads list — FUERA with cause). Streaming; activity rows collapse to one line; ask-cards render INLINE when the agent asks — the HITL visible in silicon. An open ask-card is the only thing that turns the anchor amber.
### A4 · The composer
- Multiline (Enter sends / Shift+Enter newlines) — today's input is single-line (measured above, declared).
- Stop button while the orchestrator works; a new message steers the run, never queues silently.
- Mic: PARTIAL transcription lands in the input FOR REVIEW before anything is sent; nothing is submitted automatically.

## FUERA with cause (today)
- computer-control (nodes are Android/Termux; distant candidate for the station) · OAuth multi-provider · threads list (one continuous conversation is doctrine in both houses).
- Parakeet local voice model and attachments: PROPOSAL after A4, not opened today.

## Constraints
- Propose-only; one piece = one PR; FIRMA/FIRMO over the exact head; the 405 fence rules; silicon never merges itself. Draft PRs carry REQUIERE_FIRMA; app AGENTS law (no merge/sign/deploy) intact.
- Vanilla JS, no build. Receipts <1,024 B UTF-8 with trailer. SCRUB. NO_DATA with cause, never zero; red before green; two passes, same seed; `./bin/pruebas` gates when a piece touches served files.
- Carril B consumes this contract as-is and does not reinvent it; B1 (Hexelion's voice from the panel) mounts on A3.

## Tasks (stable IDs)
- [x] C1: serve the decree verbatim (buzon#30 ·6647622152) and declare this contract in odd/ BEFORE cooking.
- [ ] A1: panel + re-derived tokens + `--acento` per node (own PR, own card section filled with measurements).
- [ ] A2: the anchor glyph, chosen by the carbon's eyes from the three candidates (own PR).
- [ ] A3: continuous chat + collapsed activity + inline ask-cards (own PR).
- [ ] A4: composer (multiline, Stop, steer, mic partial-for-review) (own PR).

## Evidence
- Decree served verbatim: buzon#30 ·6647622152 (4,874 B).
- Reference measured from Gentleman-Programming/gentle-dot (MIT) public tree, 2026-11-06 (its design doc §6 panel/tokens/anchor states, §4 composer/voice). Cited as inspiration; no affiliation.
- Our baselines pinned to app main head `a27aef5df89e37050f66bc77a2e39ccbbe3ef014`: dashboard.html 17,903 B · face/basic.html 13,005 B · odd/README.md 779 B.

## Log
- 2026-11-06: contract declared by mesa-web under the decree; FIRMA pending on the exact head of this PR.
