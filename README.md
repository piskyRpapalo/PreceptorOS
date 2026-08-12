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
```

Default location: `~/.aurelius/memory.db`. Change it with `--db RUTA`. Copy that
file and your memory comes with you.

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
