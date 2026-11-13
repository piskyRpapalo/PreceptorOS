# Talk keeps the person's place (APP-A11Y-FOCUS-01)

Commission 2026-11-13 P1 «Accesibilidad nativa» (APP accessibility is Claude's direct responsibility).
Stacked after #268 (app.js v28 → v29, cache v175 → v176).

## Explore (measured 2026-11-13, headless Chromium at 360×716, side port, this tree)

Keyboard-only walk of Talk: tab selected · «?» summary 44×44, label «Hexelion commands» · Enter opens it ·
11 command buttons, all 320×44 · Tab ×7 reaches /dispositivos, 3 px solid focus outline · Enter writes it in
the box and focuses it (label «What you say») · Tab → «Say it» · Enter sends · answer in the thread
(`aria-live=polite`) and in the status line (`polite`): «Hexelion action · devices · done · model not invoked».

Two defects:
1. After the turn, focus was on `<body>`: the submit handler disables the focused «Say it» while waiting.
   Same in the preceptor-thread path (`@name …`).
2. The waiting bubble said «pensando… en un teléfono esto son minutos»: Spanish inside the English MVP UI.

## Implement

- `devolverFoco(volverA)`: the handler remembers `document.activeElement` first; after each re-enable, if
  focus was lost to `<body>`, it goes back to where it was (or to the box). It never steals focus that moved
  elsewhere on purpose.
- The waiting bubble is English and marked `lang="en"`.

## Check

`test_app_foco.py` (source checks; the live walk is in the receipt). Live after the fix: focus after the turn
= `BUTTON#enviar` (before: `BODY`).

## Log

- 2026-11-13 · Screen reader (TalkBack) on the S110: NO_DATA — switching it on is a device setting; needs his
  OK. Audible output: NO_DATA (not exercised). With audio blocked before a gesture the app keeps working
  (console warning only).
