# ASSETS · las hojas de la cara

Documento interno del equipo (por eso va en español, como los comentarios del
código, y no en el inglés de industria de `README.md`). Describe qué son los
dos PNG de `assets/`, de dónde salieron, bajo qué licencia viajan, y el
contrato de animación que la cara está obligada a respetar.

## Procedencia y licencia

Los dos sprites fueron **generados por el Soberano** en su propio nodo. No
provienen de un banco de imágenes, no llevan marca de agua ajena y no arrastran
condiciones de terceros. Viajan bajo **CC BY-SA 4.0**, la misma licencia que la prosa y el lore, y
**no la del código**: `memory.py` es Apache-2.0 y estos PNG no. Son arte, y se licencian
como el resto del arte de esta casa — se remezclan citando la fuente y
compartiendo igual.

Firmado el 2026-08-22. Antes esta línea decía «la licencia del repo:
Apache-2.0», que no existe en ningún fichero de este árbol, y despues «la misma
que el código», que tampoco: el código es Apache-2.0.

Se guardan en el árbol, no se descargan. Una cara que necesita ir a buscarse a
sí misma a algún sitio no es una cara: es una dependencia con dibujos.

## Las dos hojas

Las dos son PNG de **1024 × 341**, RGBA, con **4 fotogramas en horizontal** de
**256 × 341** cada uno. No hay filas: una sola tira. En CSS eso es
`background-size: 400% 100%` y `background-position-x` en `0%`, `33.333%`,
`66.667%` y `100%` para los fotogramas 1 a 4.

> **Desde el 2026-09-02 son tres hojas, no dos.** `aurelius-up.png` sigue en el
> árbol y sigue siendo la hoja de `cara.py`, pero el **tablero PWA** ya no la
> usa: pasó a `preceptor-up-v2.webp`, de ocho fotogramas. Ver la sección al
> final. Las dos implementaciones tienen distinto número de fotogramas **a
> propósito y de momento** — la razón está escrita ahí abajo, y es geométrica.

### `aurelius-talks.png` · la boca

| # | Qué es |
|---|---|
| 1 | boca abierta poca |
| 2 | boca abierta más |
| 3 | boca en "o" |
| 4 | sonrisa de reposo |

### `aurelius-up.png` · el despertar

| # | Qué es |
|---|---|
| 1 | mármol sin romper (espera) |
| 2 | apertura progresiva |
| 3 | apertura progresiva, más |
| 4 | forma final con trozos volando |

## Contrato de animación

Esto no es una sugerencia estética: es el contrato que `test_cara.py` comprueba
y que la cara implementa como una máquina de cuatro estados.

| Momento | Qué se ve | Estado |
|---|---|---|
| Antes de la primera frase del día | `up[1]` fijo | `dormido` |
| La primera frase | `up[1→2→3→4]`, **una sola vez** | `despertar` |
| Tras despertar, en silencio | `talks[4]` | `reposo` |
| Mientras escribe o habla | `talks[1→2→3]` en bucle | `hablando` |
| Al terminar de hablar | `talks[4]` | `reposo` |

Tres condiciones que hacen falta para que el contrato signifique algo:

- **El despertar ocurre una vez.** Hay una bandera que se apaga al terminar la
  secuencia. Un despertar que se repite en cada frase deja de ser un despertar
  y se convierte en un tic.
- **La animación es estado LOCAL de la UI.** No depende de la red, ni de un
  servidor, ni de que nadie le diga en qué fotograma va. La cara se abre con
  doble clic desde el disco y se anima igual con el cable desenchufado.
- **Se respeta `prefers-reduced-motion`.** Quien pidió a su sistema que no le
  muevan cosas por delante recibe los fotogramas finales sin la secuencia. El
  contenido es el mismo; lo que cambia es cuánto se mueve.

## Por qué dos hojas y no un vídeo

Un sprite se incrusta en el HTML como `data:` y viaja dentro del fichero. Un
vídeo obliga a un segundo fichero al lado, y un fichero al lado se pierde en
cuanto alguien mueve la cara de sitio. La cara tiene que seguir siendo **un
solo fichero que se puede enviar por correo**.


---

## `preceptor-up-v2.webp` · la tira de ocho (tablero PWA)

Firmada por el Soberano el **2026-09-02**. La generó
`herramientas/unir_bustos.py` a partir de los ocho `busto-*.webp` de
`assets/`, y ese script es la única fuente de verdad del orden.

**2048 × 256**, RGBA, WebP **sin pérdida** (VP8L), 8 fotogramas cuadrados de
256 × 256. En CSS: `background-size: 800% auto` y `background-position-x` en
séptimos.

| # | Fotograma | `background-position-x` | Píxeles ámbar |
|---|---|---|---|
| 0 | `dormido` | `0%` | 18 |
| 1 | `grieta` | `14.2857%` | 0 |
| 2 | `rompe` | `28.5714%` | 413 |
| 3 | `ojo` | `42.8571%` | 506 |
| 4 | `halo` | `57.1429%` | 395 |
| 5 | **`despierto`** | **`71.4286%`** | **684** ← reposo del busto |
| 6 | `corazon` | `85.7143%` | 634 |
| 7 | `oscuro` | `100%` | 669 |

Los ocho **no son fotogramas de una secuencia dibujada**: son ocho estados con
nombre propio. El orden se eligió midiendo el ámbar de cada uno —de apagado a
encendido— porque una decisión narrativa sin una métrica detrás se vuelve a
discutir cada seis meses.

### Los tres sitios que dan por sabida esta geometría

Cambiar el orden o el número de fotogramas obliga a tocar los tres:

| Dónde | Qué da por sabido |
|---|---|
| `dashboard.css` · `.busto` | `800% auto`, reposo en `71.4286%`, `steps(6, jump-none)` |
| `dashboard.css` · `.telon-busto` | `800% auto`, `steps(8, jump-none)`, recorrido `0%`→`100%` |
| `herramientas/unir_bustos.py` | `ORDEN` y `REPOSO` |

El busto del tablero recorre **0..5 y se para**: son SEIS valores, o sea
`steps(6, jump-none)`, no siete. Los fotogramas 6 y 7 sólo se ven en el telón,
que sí llega hasta el final.

### Por qué el tamaño es 2048 × 256 y no 4096 × 512

Los originales miden 256 px. Un `×2` con NEAREST no añade un solo píxel de
detalle y cuesta 82 KB. Medido, no supuesto.

### Por qué WebP y no PNG

Misma imagen, sin pérdida: **464 046 b** en WebP contra **841 754 b** en PNG
optimizado. Un 45 % menos por cero pérdida — comprobado píxel a píxel: de los
524 288 píxeles de la tira, **ninguno visible difiere** de su original. Los
únicos bytes que cambian son los RGB que viven debajo de `alpha = 0`, que
ningún ojo ve y que el codificador normaliza. Si una sesión futura compara los
ficheros a lo bruto verá deltas de 255 y creerá que hay pérdida: no la hay, y
por eso queda escrito aquí.

### Por qué `cara.py` NO la usa (todavía)

No es un olvido. `cara.py` genera un HTML de un solo fichero donde **las dos
hojas comparten** un `background-size: 400% 100%` y un `.marco` con
`aspect-ratio: 3/4`, y `pintar()` divide entre `(100/3)` fijo. Los fotogramas
nuevos son **cuadrados**; los de `talks` siguen siendo 3:4. Meter la tira de
ocho ahí dentro estiraría los bustos un 33 % en vertical, o dejaría bandas
oscuras, o cambiaría la forma del marco a mitad de la animación.

La salida limpia es una hoja `talks` cuadrada que haga juego — y **entre los
ocho bustos nuevos no hay ninguna posición de boca**, así que ese material aún
no existe. Hasta que exista, `cara.py` se queda con la tira de cuatro. Lo que
sí se arregló es `dato_uri()`, que declaraba `image/png` para cualquier
extensión y habría servido un WebP mintiendo sobre su tipo.
