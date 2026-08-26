# M2 · closing the Water · the memory manifest

> Prove your memory has not changed, without writing down a single word of it.

A manifest is the list of what was in your memory at one instant. It does not
store your memories: it stores their **fingerprint**. You can hand someone the
manifest and they can check nothing was altered — and still learn nothing about
what you wrote.

## Use

```
python3 manifest.py --sign --out my-manifest.txt   # generate and sign
python3 manifest.py --verify my-manifest.txt       # check it still holds
python3 manifest.py                                 # print, unsigned
```

Default database: `~/.aurelius/memory.db`. Change it with `--db PATH`.

## What a verification means

**VALID** — two things at once: the manifest was not tampered with
(*integrity*), and your memory is still exactly as it was when you signed
(*currency*).

**INVALID · integrity** — someone edited the manifest file after it was
generated. The declared hash no longer matches its own body.

**INVALID · currency** — your memory moved on. **This is not a failure.** It
means you kept living: you added, archived or edited something after signing.
The manifest is history, not state. Sign a new one whenever you want a new
snapshot.

## Four rules this module does not negotiate

1. **The hash covers the body only.** The signature goes outside it, so signing
   cannot invalidate the seal it is signing.
2. **Signing never touches your memory.** Not a row, not a timestamp. This
   module opens the database to read.
3. **No name is a valid signature.** With nothing in your profile it writes
   `signed_by: NO_DATA`, and the manifest verifies. An anonymous signature is a
   signature; an invented one is not.
4. **Verifying is recalculating.** Nothing is trusted because it says so.

## Status (real, not aspirational)

- [x] 8/8 tests green · `python3 test_manifest.py`
- [x] Sabotage 3/3 detected · `python3 test_manifest.py --sabotaje`
- [x] Signing does not mutate the memory — asserted against every row
- [x] The manifest contains no memory text — asserted with a known secret
- [x] Empty memory signs and verifies: signing that there is nothing is legitimate
- [x] Header inside the signed region, so counts cannot be falsified
- [ ] Cryptographic signature with keys — deferred on purpose. This is a hash
      and a name, not a certificate. It proves *unchanged*, not *who*.

`manifest.py` imports `memory.py` from the product tree. It is not a copy of it.

---

## Sovereignty layers / Capas de soberanía

The product ships at **level 0** and never raises itself. A level above 0
exists only because a person signed it. The moment that signature is withdrawn
— or the level cannot be read — the product is back at 0.

🇬🇧 Two realities, one switch, and the person holds it.
🇪🇸 Dos realidades, un interruptor, y lo tiene la persona.

| Level / Nivel | It may / Puede | It may not / No puede |
|---|---|---|
| **0 · Sanctuary / Santuario** — the default | standard library, local disk, deterministic logic, the memory you already carry · biblioteca estándar, disco local, lógica determinista, la memoria que ya llevas | open a socket, of any kind, to anywhere · abrir un socket, de cualquier clase, a donde sea |
| **1 · Harness / Arnés** | run a model file that lives on this machine · ejecutar un fichero de modelo que vive en esta máquina | leave the machine · salir de la máquina |
| **2 · Expansion / Expansión** | reach services outside the machine, each one consented separately · alcanzar servicios fuera de la máquina, consentidos uno a uno | consent once for everything · consentir una vez para todo |
| **3 · Ecosystem / Ecosistema** | talk to local hardware and devices, as a separate add-on · hablar con hardware y dispositivos locales, como complemento aparte | change what levels 0–2 do · cambiar lo que hacen los niveles 0–2 |

Level 0 is not a degraded product. It is the whole product minus the parts
that need someone else. Everything above it is an addition that can be
removed, and removing it leaves nothing broken behind.

Level 3 is an add-on and stays outside the build. The core does not know it
exists: it hooks in, and if it dies the core is still whole at 0 or 1.

## The kill switch / El interruptor

One value, `nivel_soberania`, governs all of the above. It lives with the
machine's state, not with the person's memory — it describes an installation,
not a human being.

🇬🇧 If the signature is withdrawn, or the connection is lost, the system **falls
to 0 at once**. It does not step down one level at a time: it collapses.
🇪🇸 Si se retira la firma, o se pierde la conexión, el sistema **cae al 0 de
golpe**. No baja de nivel en nivel: colapsa.

### Four rules the switch does not negotiate

1. **0 is the floor and the default.** No file, an unreadable file, a corrupt
   file, a level out of range, a level that is not a number — every one of them
   resolves to 0. There is no path on which a doubt resolves upward.
2. **The collapse fails closed and quietly.** No visible network error, no data
   left half-written, no function left spinning. What depended on a higher
   level declares its absence with `NO_DATA` and a cause; the rest keeps
   working.
3. **Nothing raises itself.** Code can lower the level. Only a person raises
   it. A module that could grant itself a permission is not a permission.
4. **Two ways to force sanctuary, and neither needs the interface.** An empty
   sentinel file named `MODO_SANTUARIO` next to the state, or the `--santuario`
   flag on the command line. Either one wins over whatever the state declares,
   and the declaration is left untouched underneath — the switch cuts the
   current, it does not rewrite the wiring.

This is the same honest-sensor rule that already governs this tree: with no
data you say *there is no data*, never a decorative zero and never a frozen
screen.


## License

CC BY-SA 4.0 — [LICENSE-PROSE](LICENSE-PROSE).

Se elige CC BY-SA 4.0 y no la licencia del codigo por coherencia, no por
gusto: el README ya licencia **todos** los `.md` bajo LICENSE-PROSE. Poner
aqui la del codigo crearia una tercera version del mismo dato, que es como
empezo este problema.

CICATRIZ, 2026-08-23. Esta nota decia, escrita el 22: «en este arbol no
existe ninguna licencia Apache: LICENSE es MIT». Era falso cuando se
escribio. `LICENSE` es el Apache-2.0 completo desde el commit 11acf6e del
2026-08-19, y aquel commit toco `LICENSE` y nada mas -- ningun documento se
entero. La correccion del 22 no se hizo mirando el fichero: se hizo de
memoria, que es exactamente el fallo que este documento existe para impedir.
El dato manda sobre el recuerdo, incluido el recuerdo de quien corrige.
