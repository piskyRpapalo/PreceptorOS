# Sovereignty / Soberanía

🇬🇧 What this installation is allowed to do, who decides it, and how to cut it.
🇪🇸 Qué puede hacer esta instalación, quién lo decide y cómo cortarlo.

> This is doctrine. The mechanism lives in `soberania.py` and `estado.py`, and
> `test_soberania.py` is what proves the two agree with this page.
>
> Esto es doctrina. El mecanismo vive en `soberania.py` y `estado.py`, y
> `test_soberania.py` es lo que demuestra que ambos coinciden con esta página.

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

## Licence / Licencia

CC BY-SA 4.0 — [LICENSE-PROSE](../LICENSE-PROSE), como el resto de la prosa
de este árbol.
