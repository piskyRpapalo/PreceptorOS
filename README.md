# A meter for your own AI

This repository holds a desktop and phone application. It measures what an AI
model actually does on the machine you own, and it turns what you tell it into
a memory you can read back.

## Why a meter

Model quality is usually a claim. A page says a model is fast, or good at
code, or small enough for your laptop. On your hardware, with your files, the
claim may be true or not, and there is no easy way to tell.

This application answers that in numbers you took yourself: tokens per second
on your processor, tokens per second on your graphics chip, how much memory
was left, how long the first word took. Same prompt, same file, same machine.
The result belongs to you and never leaves the machine unless you send it.

## Why self-knowledge

The second half is quieter and matters more. Everything you ask it is kept on
your disk, in files you can open with any text editor. Over weeks that becomes
a record of what you were working on, what you kept getting wrong, and what
you already solved. The application reads it back to you when it is relevant.

This is the part that is normally sold as a subscription and stored on someone
else's server. Here it is a folder.

## Why this exists, in my own words

I write this part first person, because the rest of the file is the project
speaking and this bit is me.

**This repository is written for two readers.** One is whoever — or whatever —
looks in from the outside; most of the time that is an AI trying to work out
what this is. The other is me. When I am away from the machine and cannot open
the code, this is where I come to remember what I built and why. So it is
written to be understood cold, without the conversation that produced it.

**Sovereignty includes the electricity.** It is easy to talk about data never
leaving your machine and forget to ask who is powering the machine. Mine runs
on solar panels. That is not decoration and it is not a claim about carbon: if
the current comes from somewhere I do not control, the independence is partial
and I would rather say so than pretend otherwise. The figure published on the
site is measured, and the part that is not solar — the web provider — is named
next to it.

**The rack is a laboratory, not a server.** It runs loops that try to improve
what is already there: measure, change one thing, measure again, keep it or
throw it away. Nothing is accepted because it sounds right. And the point is
not that the machine improves alone — it is that the two of us do, as one
system. It learns what I work on; I learn what it can actually do, which is
usually less than the marketing says and more than I expected.

**I build what I need, and then I share it.** Not as a favour. Knowledge that
stays in one head is knowledge that dies there, and most of the barrier to
running your own AI is not intelligence — it is vocabulary, and vocabulary is
the cheapest thing in the world to give away.

## Where this is going

Two goals, stated plainly so anyone — or anything — reading this repository
knows what it is for.

**A community.** Not a user base. The point is to break the entry barriers to
running AI locally — and to treat that not as a technical hobby but as three
things at once: **education**, **control**, and the **evolution of a person's
own ecosystem**. Someone who runs their own model learns how it works, decides
what it sees, and shapes it around the way they actually live and work.

Alone, that is a slow climb. Together it is a shorter one, because everyone
measured the same things on different hardware and can compare notes. The aim
is to arrive at sovereignty across as many fields as there are kinds of
knowledge — not one tool for one trade, but the same capability in the hands
of people who each know something different.

**Small models trained on private data.** The longer aim is to learn to build
small specialised adapters — LoRAs — that work against private databases:
real operational data, and readings from physical sensors. Not a general
assistant that knows a little about everything, but a small model that knows
one real dataset well and never has to send it anywhere.

That is why this application is a meter first. You cannot train a small model
on data that must not leave the building and then trust a number somebody
else published about how it performs. You measure it, on your machine, and
you keep the measurement with its date.

## Two ways to take part, and both count

**Use the tools.** Install it, run it on your own machine, and say what
happened — what was slow, what broke, what your hardware measured. That is
already a contribution: the numbers here mean more the more machines they
come from, and there is no way to get them without people running this on
hardware nobody here owns.

**Build tools.** The helpers are small and specialised on purpose, so adding
one is a normal amount of work rather than a project. If you build something
that fits — a helper for a trade nobody has covered, an adapter trained on a
dataset you know well — it belongs here next to the rest.

Neither one is the price of the other. Somebody who only ever uses this is not
a lesser participant; they are the reason the tools get better.

The reason any of it is public is simple. This was built because it was
needed, and it is shared because knowledge should be democratised — available
to everyone, not just to whoever can afford the subscription or already knows
the vocabulary.

## What it does from the first minute

- Creates your memory and asks the questions it needs to start.
- Shows you **the border**: the filter that removes keys, paths and addresses
  from any text before it leaves your machine. You can read what it removed.
- Measures models and keeps the measurements with their date.

## What it does not do yet

- **The engine is not included.** It is executable code written by others, and
  this project signs data, not programs. You choose it and you fetch it. The
  binary this code actually calls is `llama-completion`; it is named here on
  purpose, because a page that promises one engine and runs another sends
  you to install the wrong thing.
- **There is no single-click installer.** You clone the repository and start
  it yourself. Nothing asks for a password and nothing downloads behind your
  back.

## Requirements

- 8 GB of memory is enough for a small model.
- No graphics card required. It runs slower on a processor alone, and the
  application tells you how much slower, because it measured it.

## Tests

    bin/pruebas

The suite is large on purpose. Anything that reports a number is checked
against the case where the number is missing, because a meter that invents a
reading is worse than no meter.

## Licence

See `LICENSE`.
