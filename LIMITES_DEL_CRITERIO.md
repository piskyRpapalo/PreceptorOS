# LÍMITES DEL CRITERIO

Qué prueban los 10 criterios de M3, qué no prueban, y qué quedó en rojo sin
causa conocida.

Existe porque un número verde es un titular, y un titular no puede afirmar más
que la sección que lo sostiene. «10/10 criterios» sostiene exactamente lo que
hay en la primera sección de este fichero. Lo de la segunda no lo sostiene
nadie todavía, y lo de la tercera está abierto.

---

## a) Qué verifican los 10 criterios

Los 10 viven en `test_fuga.py` y se corren con `bin/pruebas`. Cada uno arranca
una sala de verdad, le habla por teclado con un guion y mira lo que la sala
dejó escrito — no inserta filas con SQL y luego comprueba que la fila está.

| # | Criterio | Lo que queda demostrado |
|---|---|---|
| 1 | Se reanuda en la sala 3 sin repetir la 1 ni la 2 | El recorrido sobrevive a cerrar el programa. Las dos primeras salas se recorren de verdad, en otra conexión, como volver al día siguiente. |
| 2 | Una sala abandonada no deja media persona en `profile` | Un abandono a la tercera pregunta no escribe un perfil a medias. El estado «a medias» es una columna (`fuga_sala.estado`), no una fila suelta. |
| 3 | Un nombre ya sabido no se vuelve a pedir | Lo que la persona ya contestó no se le pregunta otra vez. |
| 4 | Se sale de la sala 5 sin fuente, y queda `sin_declarar` | No hay callejón sin salida: la falta de fuente se declara y se sigue. |
| 5 | Lo no contestado se ve `NO_DATA` literal, nunca vacío | La ausencia es visible. Una celda en blanco no se distingue de un fallo de escritura. |
| 6 | Cero `DELETE` en `fuga.py` | Los estados son columnas. Nada de lo que la persona escribió se borra para representar un cambio. |
| 7 | El manifiesto lleva la huella de su propio cuerpo | Lo que M3 firma corresponde al texto que M3 emitió. |
| 8 | Sin voz ni oído, la sala se completa escribiendo | La voz es un adorno. Una máquina sin Piper ni micrófono hace M3 entero. |
| 9 | Entrar en una sala pide su leitmotiv | El canal sonoro se pide de verdad, y hay más de uno. |
| 10 | M3 se completa con un solo dato real y el resto `NO_DATA` | No se exige rellenarlo todo para haber terminado. |

Y una afirmación de segundo orden, que es la que da valor a las diez: los
sabotajes. `test_fuga.py --sabotaje` rompe `fuga.py` de seis maneras concretas
en una copia del árbol y **exige que la suite se ponga roja**: 6/6 detectadas.
Sin eso, «10/10 verde» solo diría que el código pasa la suite, que es una
afirmación sobre la suite y no sobre el código.

---

## b) Qué NO verifican

**Ninguno de los 10 comprueba que la persona salga de M3 sabiendo algo que no
sabía al entrar.**

Esa era la razón de construir M3.

Los 10 criterios miden el continente: que el estado persiste, que la ausencia
se declara, que nada se borra, que la sala se completa sin hardware. Todos son
verificables por máquina, y por eso están. Lo otro —que las seis salas enseñen
algo, y que lo enseñado quede— no está medido en ninguna parte de este árbol.
No hay un caso que lo intente y falle: no hay caso.

Un verde de 10/10 es compatible con una persona que recorre las seis salas,
deja su perfil escrito, firma su manifiesto y sale igual que entró. Eso no es
una hipótesis pesimista; es lo que los criterios permiten, porque ninguno lo
excluye.

Queda escrito aquí y no se compensa. No hay promesa de que el siguiente
criterio lo arregle, ni fecha, ni criterio 11 esbozado: eso sería sustituir una
medida que falta por una intención, que es la operación exacta que este fichero
existe para no hacer.

---

## c) El rojo del 2026-08-16

En una tanda de esa madrugada, **7 pruebas fallaron**. Correlación exacta: las
7 son exactamente las que tocan un fichero de 18.000 bytes. La aritmética es
correcta y el hallazgo es bueno.

**La hipótesis de falta de espacio está desmentida.** En esa MISMA tanda,
`test_leitmotivs` salió `ok` habiendo escrito 6 WAV de 110.294 B —**661.764
bytes**, 36 veces más datos— en un `tempfile.TemporaryDirectory`, el mismo
sitio, y habiendo calculado el sha256 de cada uno. Misma operación, mismo
destino, 36× el volumen, verde.

El orden lo empeora: descarga (1.ª, FALLO), estado (2.ª, ok), fuga (3.ª,
FALLO), guardrails (4.ª, ok), leitmotivs (5.ª, ok). El espacio habría tenido
que liberarse a mitad de tanda, y ahí nada libera nada.

Medición posterior (2026-08-16, tras reinicio), que corrobora sin ser la razón
principal: `/` con 541G libres y `/tmp` en tmpfs de 29G con 432K usados —
`TemporaryDirectory` ni siquiera toca el disco—; inodos al 2% y 1%; y el
journal de la ventana, 9.129 líneas reales, sin una sola coincidencia de
`no space` / `ENOSPC` / `I/O error`, ni de `oom-kill`, en toda la semana
disponible.

**Mecanismo: sin determinar.** `NO_DATA`.

El árbol da hoy VERDE 218/218, salida 0, en Python 3.14.4 y en 3.10.12. Eso no
cierra el rojo: dice que no se reproduce, que es una afirmación distinta y más
débil. Un rojo sin causa conocida se declara, no se cierra.

Lo que sigue abierto, en concreto:

- No se sabe qué hizo fallar a esas 7 y no a las otras.
- No se sabe si la correlación con los 18.000 bytes es la causa o un rasgo
  compartido de otra cosa.
- No hay constancia de la hora exacta de aquella tanda, así que la ventana del
  journal que se inspeccionó (01:00–02:31) puede no contenerla. El grep se
  amplió a todos los arranques registrados desde el 10 de agosto y tampoco hay
  nada; eso acota, no demuestra.
- Si vuelve, lo primero que hay que capturar es la tanda entera con su hora y
  el `errno` literal, no el resumen.
