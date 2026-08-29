---
id: espec-cahier
clase: especificacion
version: 1.0.0
fecha: 2026-08-29
metrica: Cahiers que se abren con sqlite3 a mano sin la aplicación (objetivo → 1); datos de soberanía que viven solo en localStorage (objetivo → 0)
umbral: no se re-edita sin diez Cahiers reales exportados y reimportados
presupuesto_kb: 14
n_medicion: 10
enlaces: [mision-escaparate, mision-tenedor, handoff-v83]
---

# ESPECIFICACIÓN · EL CAHIER
### La memoria es un fichero de la persona. Todo lo demás son detalles de implementación.
*Autor: el Preceptor · Canoniza: el Soberano · Ejecuta: CC*

---

## MOTIVO

El Cahier es lo único del producto que no se puede rehacer. El modelo se
redescarga, la interfaz se reescribe, el andamio se archiva; lo que la persona
escribió, no. Esta especificación existe para que esa asimetría se note en cada
decisión técnica.

**Frase-llave:** *el Cahier recuerda; el Libro de Cabecera enseña; el Libro de
Pruebas atestigua.* Las tres cosas son distintas y no se mezclan nunca.

---

## LO QUE EL CAHIER **NO** ES (leer antes de tocar código)

- **No es un nombre de código.** «Cahier» es el nombre **público**: el que ve la
  persona en la interfaz y el que se usa en la documentación. En el código y en el
  esquema se sigue llamando `memory` / `memoria`, y **las tablas no se renombran**.
  Renombrar un esquema vivo por coherencia de marca es cambiar datos de sitio para
  que un documento quede bonito.
- **No es una cuenta.** No hay registro, no hay identificador de servidor, no hay
  correo. Si una función del Cahier necesitara un servidor para completarse, esa
  función está mal diseñada.
- **No vive en localStorage.** localStorage es **buffer de reconciliación** y nada
  más: lo que hay ahí puede perderse sin que se pierda nada. Si un dato de
  soberanía solo existe en localStorage, es un fallo, no un atajo.
- **No es el Libro de Pruebas.** Lo que se publica es una línea firmada que la
  persona decide enviar. El Cahier entero no sale nunca solo.
- **No toca valor.** IronClaw íntegro.

---

## EL CONTRATO

### El esquema real, medido el 2026-08-29

Trece tablas en la rama `main`, doce reales y una virtual:

| Tabla | Qué guarda |
|---|---|
| `engrams` | Los recuerdos. El corazón del Cahier |
| `engrams_fts` | Índice **virtual FTS5** sobre `engrams` |
| `links` | Relaciones entre engramas |
| `profile` | Quién es la persona, según ella |
| `borradores` | Lo escrito y no confirmado. **No son engramas** |
| `hilos` · `hilos_eventos` | Los hilos, por event sourcing |
| `salidas` | Lo que el sistema decidió mostrar o sugerir |
| `turnos` | La captura de conversación |
| `proyectos` | En qué trabaja la persona |
| `fuga_sala` · `fuentes` | La Frontera: qué entra y de dónde |
| `latidos` | Señales de vida de los bucles |

**Corrección de cuenta sobre el Handoff v8.3:** allí se dicen «11 tablas». Son
trece, y las dos que faltaban en esa lista son `latidos` y `engrams_fts`. La
cifra sale de leer el árbol, no de recordarlo.

### Migración: solo aditiva

Se añaden tablas y columnas; no se renombran ni se borran. Un Cahier de hace tres
meses tiene que abrirse hoy. Esta es la regla que hace cierta la promesa del
formato que cuenta la Sala 2 del lore.

### FTS5 no se supone: se sonda

`memory.py` ya trae una sonda (`_hay_fts5`) que crea una tabla virtual temporal
para comprobar si el SQLite de este aparato trae FTS5. **Ese es el patrón, y se
mantiene:** si falta, se declara y se cae a una búsqueda más pobre pero real. Un
producto que asume FTS5 se rompe en silencio en el aparato de alguien.

WAL está activo (`pragma journal_mode=wal`), y en el navegador el fichero vive
sobre **OPFS**.

### Recuperación · v1 del lado de la aplicación

- **v1:** FTS5 más top-k inyectado en el prompt por la aplicación. Es lo que hay,
  y funciona hoy.
- **Embeddings:** coseno por fuerza bruta con MiniLM de `@huggingface/transformers`
  (~23 MB). Fuerza bruta es honesta a esta escala; fingir un índice no lo sería.
- **`sqlite-vec` queda diferido** mientras no haya un build WASM público. Se
  declara como diferido, no como planeado.
- **Tool calling nativo es extensión, no v1.** En el rack la *emisión* de la
  llamada está demostrada, pero el cierre del ciclo devuelve `content: null`: hay
  un fallo de formato sin depurar. Mientras eso no se cierre, no sostiene la
  recuperación de nadie.

### Cold Start · cinco engramas antes del primer turno

`token` · `ttft` · `no_data` · `cuantizacion` · `contexto`

El modelo **debe** declarar `NO_DATA` sobre estos términos y dejar que el Cahier
los responda. No es un fallo del modelo: es el reparto. Los pesos no saben; la
memoria sí. Firmado por el Soberano el 2026-08-29 tras medirlo en las dos líneas
del LoRA v7.

### El Libro de Cabecera se instala DENTRO del Cahier

El temario —misiones, bases de lenguaje, catálogo de habilidades— se descarga de
la web **en la instalación** y se escribe dentro del Cahier como engramas de
origen declarado. A partir de ahí es memoria de la persona: puede leerla,
corregirla y anotarla como cualquier otro recuerdo.

Todo engrama que venga del Libro de Cabecera lleva su origen y su versión. Sin
eso, dentro de un año nadie sabrá qué escribió la persona y qué vino de fábrica,
y esa distinción es justo la que el producto vende.

### El espejo · local ↔ Perfil IKEA

El Cahier vive en el aparato. El espejo del Perfil IKEA es **una copia firmada y
parcial**, no la fuente. Reglas:

- La fuente de verdad es siempre la local. El espejo se reconstruye desde ella,
  nunca al revés.
- Se sube lo que la persona marque, con firma ed25519. Nada por defecto.
- Un conflicto **no se resuelve solo**: se muestran las dos versiones y decide la
  persona. Un merge automático sobre la memoria de alguien es una pérdida de datos
  con buenos modales.

### Éxodo (v1.1) · llevárselo entero

Exportación e importación del Cahier cifrado con AES-256-GCM y firmado con
ed25519, en un fichero portable.

> **MARCADO, NO APLICADO.** El Handoff v8.3 fija la extensión de ese fichero como
> `.aurelius`. Ese nombre se retiró del ecosistema el 2026-08-29. Una extensión
> es un identificador de formato y no se cambia por gusto: cambiarla rompe a quien
> ya tenga ficheros exportados. La decisión —conservarla como fósil declarado o
> fijar otra antes de que exista el primer fichero— es del Soberano. Hoy no hay
> ninguno exportado, así que es el momento más barato para decidirlo.

---

## INVARIANTES

- **El Cahier se abre con `sqlite3` a mano**, sin la aplicación. Es la prueba de
  que la persona lo posee.
- **Migración aditiva.** Nada se renombra, nada se borra.
- **FTS5 se sonda, no se supone.**
- **localStorage no persiste soberanía.** Solo buffer.
- **Los `borradores` no son engramas** y no se recuperan como tales.
- **Todo engrama declara su origen.** Lo de fábrica y lo escrito por la persona
  no se confunden nunca.
- **El espejo nunca sobrescribe lo local.**
- **Nada sale del aparato sin acto explícito** de la persona.

---

## PROMPT PARA CC (una pieza por sesión)

```
ESPECIFICACIÓN · EL CAHIER, pieza <nombre>.
Lee mente/misiones/ESPEC_CAHIER.md entero antes de tocar nada,
incluida la sección "LO QUE EL CAHIER NO ES".

No renombres tablas ni columnas. Migración aditiva o nada.
Si una capacidad exige red para completarse, PARA y repórtalo: es señal
de que la pieza está mal planteada, no de que falte una llamada.

Reporta en formato de 12 líneas. Cierra con 3-6 SUGERENCIAS (S/M/L) anexadas a
mente/feedback/PENDIENTES.md. PARA.
```

---

## CHANGELOG

**v1.0.0 (2026-08-29)** · Creación. Destilado del Handoff v8.3 y del árbol vivo.
Tres cosas salen de medir y no del documento de partida: el esquema real son
**trece** tablas y no once (faltaban `latidos` y `engrams_fts`); la sonda de FTS5
ya existe en `memory.py` y se eleva a regla en vez de inventar otra; y la
extensión `.aurelius` del Éxodo queda **marcada para firma**, porque nombra un
formato con una palabra que el ecosistema retiró.
