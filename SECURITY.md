# Security Policy

> Español más abajo · [Ir a la versión en español](#politica-de-seguridad)

Aurelius keeps your memory in a file on your own machine. If something in this
project can leak that file, corrupt it, or run code you did not ask for, we want
to know before anyone else does.

## Reporting a vulnerability

**Email: davidpecero@gmail.com** — subject line starting with `SECURITY:`.

Please do **not** open a public issue for a security problem. Write to the
address above first.

Helpful, in whatever detail you have:

- What the problem is, in one or two sentences.
- Steps to reproduce it, or a proof of concept.
- Version or commit (`git rev-parse HEAD`), OS, and Python version.
- What an attacker gets out of it.

If you want an encrypted channel and none is published here, say so in a first
plain email and we will arrange one.

## What to expect

This is a small project with a single maintainer. These are honest targets, not
a corporate SLA:

| Stage | Target |
|---|---|
| Acknowledgement that your email arrived | **within 7 days** |
| First assessment — confirmed, not reproducible, or out of scope | **within 14 days** |
| Fix or documented mitigation for a confirmed issue | **within 90 days** |
| Progress update while a report is open | **every 30 days** |

The process:

1. You report privately.
2. We confirm receipt and try to reproduce it.
3. We tell you what we found: confirmed, not reproducible, or out of scope — and
   why.
4. If confirmed, we fix it and publish the fix.
5. We credit you in the release notes and the commit, by whatever name you
   choose. Say so if you would rather stay anonymous.

**Coordinated disclosure.** Please give us **90 days** from the acknowledgement
before publishing. If we go silent or miss the targets above without saying
anything, publish — an unmaintained promise is not a reason to sit on a real
bug. If a vulnerability is already being exploited in the open, tell us and
publish whenever you judge is right; we will not ask you to wait.

There is no bug bounty. There is no money in this project. What we can offer is
a real answer, a fix, and credit.

## Supported versions

Only the current `main` branch is supported. There are no long-lived release
branches; fixes land on `main` and that is the version to run.

## Scope

In scope:

- Anything that reads or exfiltrates `~/.aurelius/memory.db` (or the path given
  to `--db`) beyond the machine it lives on.
- Failures of **redaction at the border**: data that should have been redacted
  on `--export` and was not.
- Code execution from data — a crafted memory entry, corpus file, or imported
  form (`cara.py --aplicar`) that ends up executing.
- The first-run download of the model and voice: unverified integrity, a
  tampered artifact accepted, downgrade or path traversal on unpacking.
- Generated HTML (`cara.html`) that executes injected content from your own
  stored memories.
- Path traversal, symlink attacks, or unsafe permissions on files Aurelius
  writes.

Out of scope:

- Aurelius does **not** encrypt your database at rest, and does not claim to.
  Anyone with read access to your user account can read your memories. That is a
  design decision, not a bug — report the threat model, not the fact.
- Vulnerabilities in Python itself, your OS, or the upstream model weights, other
  than how Aurelius fetches and verifies them.
- Anything requiring physical access to an unlocked machine, or root on it.
- Missing hardening headers or similar on `cara.html`, which is a local file and
  not a served site.
- Reports produced only by a scanner, with no reasoning about impact.

## A note on what this project is

Aurelius is a learning project about technical sovereignty. A clear, reproducible
security report is worth more to it than a patch — it teaches. If you took the
time to find something here, thank you.

---

<a id="politica-de-seguridad"></a>

# Política de seguridad

Aurelius guarda tu memoria en un fichero de tu propia máquina. Si algo de este
proyecto puede filtrar ese fichero, corromperlo o ejecutar código que no pediste,
queremos saberlo antes que nadie.

## Cómo reportar una vulnerabilidad

**Correo: davidpecero@gmail.com** — con el asunto empezando por `SECURITY:`.

Por favor, **no** abras un issue público para un problema de seguridad. Escribe
primero a esa dirección.

Ayuda, con el detalle que tengas:

- Cuál es el problema, en una o dos frases.
- Cómo reproducirlo, o una prueba de concepto.
- Versión o commit (`git rev-parse HEAD`), sistema operativo y versión de Python.
- Qué gana un atacante con ello.

Si quieres un canal cifrado y aquí no hay ninguno publicado, dilo en un primer
correo en claro y lo acordamos.

## Qué esperar

Esto es un proyecto pequeño con un solo mantenedor. Son objetivos honestos, no un
SLA corporativo:

| Etapa | Objetivo |
|---|---|
| Confirmación de que tu correo llegó | **7 días** |
| Primera valoración — confirmado, no reproducible o fuera de alcance | **14 días** |
| Arreglo o mitigación documentada de un problema confirmado | **90 días** |
| Actualización mientras el reporte siga abierto | **cada 30 días** |

El proceso:

1. Reportas en privado.
2. Confirmamos recepción e intentamos reproducirlo.
3. Te decimos qué encontramos: confirmado, no reproducible o fuera de alcance — y
   por qué.
4. Si se confirma, lo arreglamos y publicamos el arreglo.
5. Te acreditamos en las notas de la versión y en el commit, con el nombre que
   elijas. Dilo si prefieres permanecer anónimo.

**Divulgación coordinada.** Danos **90 días** desde la confirmación antes de
publicar. Si nos quedamos en silencio o incumplimos los plazos de arriba sin
decir nada, publica: una promesa sin mantener no es razón para sentarse sobre un
fallo real. Si una vulnerabilidad ya se está explotando en abierto, avísanos y
publica cuando lo veas oportuno; no te pediremos que esperes.

No hay recompensa económica. En este proyecto no hay dinero. Lo que sí podemos
ofrecer es una respuesta de verdad, un arreglo y el crédito.

## Versiones soportadas

Solo se soporta la rama `main` actual. No hay ramas de versión de larga vida: los
arreglos aterrizan en `main` y esa es la versión que hay que ejecutar.

## Alcance

Dentro de alcance:

- Cualquier cosa que lea o exfiltre `~/.aurelius/memory.db` (o la ruta dada con
  `--db`) fuera de la máquina donde vive.
- Fallos de la **censura en la frontera**: datos que debieron redactarse en
  `--export` y no se redactaron.
- Ejecución de código desde datos — una entrada de memoria, un fichero de corpus o
  un formulario importado (`cara.py --aplicar`) que acabe ejecutándose.
- La descarga del modelo y la voz en el primer arranque: integridad sin verificar,
  un artefacto manipulado aceptado, degradación de versión o path traversal al
  desempaquetar.
- HTML generado (`cara.html`) que ejecute contenido inyectado desde tus propias
  memorias guardadas.
- Path traversal, ataques por symlink o permisos inseguros en los ficheros que
  Aurelius escribe.

Fuera de alcance:

- Aurelius **no** cifra tu base de datos en reposo, y no dice lo contrario.
  Cualquiera con acceso de lectura a tu cuenta de usuario puede leer tus
  memorias. Es una decisión de diseño, no un fallo — reporta el modelo de
  amenaza, no el hecho.
- Vulnerabilidades de Python, de tu sistema operativo o de los pesos del modelo
  original, más allá de cómo Aurelius los descarga y verifica.
- Cualquier cosa que requiera acceso físico a una máquina desbloqueada, o root en
  ella.
- Cabeceras de endurecimiento o similares en `cara.html`, que es un fichero local
  y no un sitio servido.
- Reportes producidos solo por un escáner, sin razonamiento sobre el impacto.

## Una nota sobre qué es este proyecto

Aurelius es un proyecto de aprendizaje sobre soberanía técnica. Un reporte de
seguridad claro y reproducible vale aquí más que un parche: enseña. Si dedicaste
tiempo a encontrar algo aquí, gracias.
