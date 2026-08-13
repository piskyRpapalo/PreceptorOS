# Aurelius · M2 · the Water

> Your memory, in one file you can carry. It starts empty and says so.

Aurelius wakes up with no memory. Instead of pretending otherwise, it tells you
what it does not have and asks you to help build it. What you write stays on
your machine, in a single file, in your own words.

## What it does

- Starts in one of three honest states: **no schema**, **empty**, or **with data**. Those are three different things and it never confuses them.
- Guides you through a memory field by field: `what`, `why`, `where`, `learned`. Each question shows the field it is filling.
- Writes `NO_DATA` where you have no answer, and shows it. Never a blank cell.
- Shows your memory three ways: a table, an indented tree of links, and a count of how many gaps are left.
- Exports to markdown **redacted at the border**.

## What it does not do

- It does **not** redact what you store. Your machine, your data, your words. Redaction happens only when something leaves.
- It does **not** delete. Archiving is a column, not a folder.
- It does **not** need the network, a GPU, or any dependency beyond Python 3 and its standard library.
- It does **not** search yet. With a handful of memories, search is a solution to a problem you do not have.

## Use

```
python3 aurelius.py                # the seven-step session
python3 aurelius.py --view         # just look
python3 aurelius.py --export       # markdown, redacted
AURELIUS_RITMO=0 python3 aurelius.py   # same session, no pauses
```

Default location: `~/.aurelius/memory.db`. Change it with `--db RUTA`. Copy that
file and your memory comes with you.

## Install, from nothing

```
git clone https://github.com/piskyRpapalo/aurelius.git && cd aurelius && python3 aurelius.py
```

That is the whole installation. There is no package to add, no service to start
and no account to make: Python 3 and its standard library are the only
requirements, and both are already on most machines. The first run asks your
language, then offers to create your memory — nothing is written before you say
so.

Voice is optional and separate. Without it, everything works and the Speak
button says plainly that this copy has no voice.

## The face

```
python3 cara.py                     # writes cara.html from your memory
python3 cara.py --aplicar aurelius-formulario.json
```

`cara.py` reads your memory and writes **one HTML file**: the sprites, both
languages and your own memories are inside it. Open it with a double click —
there is no server to start, and it makes no network calls at all. Copy it to a
USB stick and it says exactly the same thing on a machine with no cable.

That forces one honest asymmetry, worth stating out loud: the face **reads**
your memory at the moment it is generated, and to **write** it hands you a form
file that you save and apply yourself. Nothing is written from the browser
behind your back — you can open the form and read it before it touches
anything.

Inside: the Slate (everything your memory holds, gaps declared, and two ways to
take it with you) and the Path (the eight steps). Frame maps and the animation
contract are in [ASSETS.md](ASSETS.md).

## Language / Idioma

The first question of the session is which language to speak — English or
Español — and it is asked in both, because at that point you have not chosen
yet. Everything after it, including the questions, the views and the closing,
is in the language you picked.

The answer is kept in your profile next to `device` and `name`, so a second
session does not ask again. Not answering is an answer too: it stays `NO_DATA`
and the session runs in English. `NO_DATA` here means *nobody chose*, which is
a different thing from *chose English* — the profile keeps them apart.

## Pace: `AURELIUS_RITMO`

Aurelius speaks with a cadence — it types at a readable speed and pauses at
punctuation. That is a default, not a requirement. Set `AURELIUS_RITMO=0` and
every wait disappears; `1.0` is the normal pace, and any number in between
scales it.

```
AURELIUS_RITMO=0 python3 aurelius.py
```

Turn it off if you are in a hurry, driving Aurelius from a script, or reading
with a screen reader — a pause that helps one person is noise to another. **The
text is identical in both modes.** Cadence can change *when* something is said,
never *what* is said; a tone that alters the content is not tone. The pace also
switches itself off when output is not a terminal, so piping and scripting are
byte-for-byte reproducible without setting anything.

## Border: redaction is required, not optional

`--export` looks for a `guardrails` module providing `redactar_salida(text) ->
(text, [{policy, count}])`. **If it is not there, export is blocked** and
nothing is printed. Failing closed is deliberate: a filter that breaks and lets
the text through is worse than no filter, because you would believe you were
protected.

The findings report **class and count only** — `API_KEY x1` — never the matched
value. A report that echoed the secret would put it back in the place the
redaction just removed it from.

## Status (real, not aspirational)

- [x] Three states, distinguished and tested
- [x] Round-trip byte-identical, accents and newlines included
- [x] `NO_DATA` stored, shown and counted
- [x] Table, tree and gap count
- [x] Archive without delete
- [x] WAL journal: an interrupted write leaves no half rows
- [x] Store raw / export redacted, tested in both directions
- [x] Export blocked with no filter
- [ ] `guardrails` module shipped in this folder — comes from the product, injected not copied
- [ ] Full-text search — out of M2 on purpose
- [ ] Manifest signature — belongs to the close of M2

12/12 tests green: `python3 test_memory.py`

## License

Apache-2.0.
