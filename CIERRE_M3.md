# CIERRE DE M3 · HEGEMONIKON

Acta de cierre de la tercera misión: **La Fuga del Museo**. Qué se construyó,
qué se verifica, qué no se verifica, y qué queda debiendo M4.

Estado: **FIRMADA** · Pisky · Soberano · 2026-08-16. **M3 está cerrado.**
Árbol al firmar: `0c7e230` · 224/224. Estado hoy: 225/225 en `bin/pruebas`,
salida 0, en cinco intérpretes (3.10.12 · 3.11.16 · 3.12.13 · 3.13.15 · 3.14.4).

Este documento no sustituye a [LIMITES_DEL_CRITERIO.md](LIMITES_DEL_CRITERIO.md):
allí está el detalle de qué demuestra cada criterio y el acta del rojo del
2026-08-16. Aquí está el cierre.

---

## 1 · LO CONSTRUIDO

### Las seis salas

M3 es un recorrido de seis salas. Cada una hace una pregunta real, escribe lo
contestado en el perfil de la persona y cierra con un concepto nombrado.

| # | Sala | Concepto que cierra |
|---|---|---|
| 1 | `prohairesis` | identidad digital |
| 2 | `safehouse` | frontera física |
| 3 | `horme` | superficie de ataque |
| 4 | `prosoche` | política de frontera |
| 5 | `katalepsis` | fuente verificable |
| 6 | `hupexairesis` | lo que no depende de ti |

El orden de cierre de una sala no es casual: **primero se escribe lo
contestado, después se marca completada**. Marcar completada una sala cuyas
respuestas no llegaron al disco sería firmar un recorrido que no existe.

### Reanudación

El recorrido sobrevive a cerrar el programa. `_detectar_reanudacion()` devuelve
la sala por la que se vuelve a entrar, y volver **no pisa lo que ya estaba
cerrado**: las salas completadas conservan su concepto, su hora de salida y sus
minutos.

Eso obligó a una regla que hoy es doctrina del árbol: la entrada en una sala se
escribe con `ON CONFLICT(sala) DO UPDATE` y **nunca** con `INSERT OR REPLACE`,
porque lo segundo borra la fila entera y se lleva por delante lo que la sala ya
sabía. El mismo razonamiento se aplicó después al perfil (D80).

Parar es un estado, no un abandono: `_marcar_sala_pausada` deja la siguiente
pausada y se reanuda por ella.

### El permiso del gerente

El perfil de M3 es memoria de la persona, y sale por **una sola puerta**:
`perfil_para_gerente(db)`. Tres reglas, las tres verificadas:

- **Fila ausente vale `no`.** Una base recién creada, una fila que nunca se
  escribió y una sesión cortada antes de la pregunta dan todas la misma
  respuesta, y es la que no entrega nada. Solo un `si` explícito abre.
- **La comprobación vive dentro del camino de lectura**, no en quien llama. Esa
  es la diferencia entre un permiso y una costumbre: en el llamante, bastaría
  un llamante nuevo que no la conociera — y siempre hay un llamante nuevo.
- **Sin permiso levanta `SinPermiso`**, no devuelve un diccionario vacío. Vacío
  se confunde con «no contestó nada», y son cosas distintas: una es no tener
  datos y la otra es tenerlos y que no sean tuyos.

### El tiempo, medido y no estimado

Los minutos de cada sala salen de `julianday('now') - julianday(entrado_en)`
**en la propia base**: es el reloj que ya escribió la entrada, así que no hay
dos relojes que puedan discrepar. Si `entrado_en` no se puede leer, la fila
queda en `-1` — no medido — y **no cuenta para la estimación**.

Hacen falta **dos** salas medidas para hablar de tiempo (`MINIMO_PARA_ESTIMAR`).
Con una sola, la «media» es esa sala: no es una media, es una anécdota con
decimales. Desde la tercera, el tiempo que se anuncia sale de las salas de esa
persona y no de un número escrito por nadie. La sala 3 se avisa aparte por ser
la larga.

### Lo que M3 no necesita

Sin Piper, sin micrófono y sin altavoz, M3 se completa **escribiendo**. La voz
y el oído son adornos del relato, no requisitos — y el apagado es del producto,
no de cada suite: `AURELIUS_SIN_HARDWARE=1` cierra las tres puertas y cruza a
los procesos hijo.

---

## 2 · ESTADO DE LOS 10 CRITERIOS

**10 de 10 pasan.** Verificados uno a uno, no solo dentro de la tanda:

```
Criterio 1: se reanuda en la sala 3 sin repetir la 1 ni la 2.          ... ok
Criterio 2: una sala abandonada no deja media persona en profile.      ... ok
Criterio 3: un nombre ya sabido no se vuelve a pedir.                  ... ok
Criterio 4: se sale de la sala 5 sin fuente, y queda 'sin_declarar'.   ... ok
Criterio 5: lo no contestado se ve NO_DATA literal, nunca vacio.       ... ok
Criterio 6: cero DELETE en fuga.py. Estados por columna.               ... ok
Criterio 7: el manifiesto lleva la huella de su propio cuerpo.         ... ok
Criterio 8: sin voz ni oido, la sala se completa escribiendo.          ... ok
Criterio 9: entrar en una sala pide su leitmotiv.                      ... ok
Criterio 10: M3 se completa con un solo dato real y el resto NO_DATA.  ... ok

Ran 10 tests · OK
```

### Trampa de lectura · detectada y cerrada (M-D80e)

**Estuvo así y se arregla; queda escrito porque la cicatriz vale más que la
superficie lisa.** Los nombres de los tests y los números de criterio **no
coincidían en cuatro casos**:

| Criterio | Cubierto por (antes) | Ahora |
|---|---|---|
| 7 · manifiesto | `test_08_manifiesto_se_comporta` | `test_07_manifiesto_se_comporta` |
| 8 · sin voz ni oído | `test_07_sin_oidos_sin_voz_funciona` | `test_08_sin_oidos_sin_voz_funciona` |
| 9 · leitmotiv | `test_10_toda_confirmacion_tiene_sonido` | `test_09_toda_confirmacion_tiene_sonido` |
| 10 · misión completa | `test_09_mision_completa_con_un_dato` | `test_10_mision_completa_con_un_dato` |

**Nada fallaba por eso, y por eso duró.** Los diez pasaban. Solo se ve
auditando, y quien auditase por el número del método concluiría que faltan
criterios que están.

Renombrar no basta: volvería a torcerse. `test_00_el_numero_del_test_es_el_del_criterio`
lo comprueba **por introspección** —lee el número del método y el que declara
su docstring, y exige que sean el mismo— y además exige que estén los diez, para
que una renumeración que borrase uno no deje la comprobación en verde con nueve.
No se usa una lista escrita a mano: una lista es otra cosa más que se puede
desincronizar del árbol, y sería el mismo fallo con un fichero más.

Verificado en los dos sentidos: la guarda pasa sobre el árbol arreglado y
**falla** sobre una copia donde se deshace el arreglo.

### Ninguno falla · tres cambiaron de sostén

Ningún criterio se ha caído ni se ha reescrito. Tres se sostienen hoy sobre
piezas que en el cierre anterior no existían, y eso los hace **más fuertes, no
distintos**:

- **Criterio 2** (nada a medias) se apoyaba en que `_volcar_pendiente`
  confirmara el lote entero. Desde D80 el SQL vive en `memory.guardar_perfil`
  con `commit=True` al final del lote: la promesa «el perfil de una sala se
  vuelca entero o no se vuelca» sigue intacta. Un escritor por clave la habría
  roto, y por eso `guardar_perfil` acepta `commit=False`.
- **Criterio 6** (cero `DELETE`) sigue comprobándose sobre `fuga.py`, y el SQL
  del perfil ya no vive ahí. La cobertura no se pierde porque `memory.py` tiene
  su propia comprobación de cero `DELETE` (caso 14 de `test_memory.py`). **Son
  dos comprobaciones sobre dos ficheros, y hacen falta las dos:** si mañana un
  tercer módulo escribe `profile`, ninguna de las dos lo vería.
- **Criterio 9** (leitmotiv) se apoya desde D78 en un generador **determinista**.
  Antes, `hash(str(i))` estaba aleatorizado por proceso: dos clones sonaban
  distinto. Ahora la misma sala suena igual en todas partes, y el sha256 de los
  seis se reprodujo en otra máquina, carácter a carácter.

### Lo que da valor al 10/10

**Los sabotajes: 6/6 detectadas.** `test_fuga.py --sabotaje` rompe `fuga.py` de
seis maneras concretas en una copia del árbol y exige que la suite se ponga
roja. Sin eso, «10/10 verde» solo diría que el código pasa la suite — una
afirmación sobre la suite, no sobre el código.

### Cobertura alrededor de los 10

`test_fuga.py` tiene **36 casos**, no 10. Los otros 26 son las condiciones que
hicieron falta para que los 10 significaran algo: que las tablas de M3 las cree
M3 y no el `setUp` de la suite, que una sala cerrada sí escriba, que el permiso
no quede suelto al abandonar la sala 3, la gramática de las preguntas numeradas
por los dos canales, los minutos medidos, y el recorrido entero de punta a
punta.

Esa es la cicatriz más cara de M3: **la suite fabricaba en su `setUp` las tablas
que iba a comprobar**, así que `fuga.py` no las creaba en ninguna parte y la
suite estaba verde. En una máquina limpia M3 reventaba con `no such table:
fuga_sala`. Un test que fabrica el dato que va a comprobar prueba SQLite, que ya
funcionaba.

---

## 3 · LÍMITES CONOCIDOS

### El límite que importa

**Ninguno de los 10 criterios comprueba que la persona salga de M3 sabiendo
algo que no sabía al entrar.**

Esa era la razón de construir M3.

Los 10 miden el continente: que el estado persiste, que la ausencia se declara,
que nada se borra, que la sala se completa sin hardware, que el permiso no se
salta. Todos son verificables por máquina, y por eso están. Que las seis salas
**enseñen** algo, y que lo enseñado quede, no está medido en ninguna parte de
este árbol. No hay un caso que lo intente y falle: **no hay caso**.

Un 10/10 verde es compatible con una persona que recorre las seis salas, deja
su perfil escrito, firma su manifiesto y sale igual que entró. No es una
hipótesis pesimista: es lo que los criterios permiten, porque ninguno lo
excluye.

### Los otros límites, en orden de cuánto pesan

- **El rojo del 2026-08-16 sigue abierto.** Correlación exacta con un fichero
  de 18.000 bytes; disco descartado; **presión de memoria sobre `tmpfs` NO
  descartada**. Mecanismo: `NO_DATA`. Desde D80c `bin/pruebas` fija
  `TMPDIR=/var/tmp`, así que si vuelve, vuelve en un sitio conocido — eso cierra
  una indeterminación, no el incidente. Detalle en `LIMITES_DEL_CRITERIO.md` §c.
- **`aurelius.py` no lo importa ninguna suite.** Es el punto de entrada del
  producto y el sitio desde el que se ofrece M3. `test_interprete.py` es lo
  primero que lo arranca, y solo como subproceso y solo para `--view`.
- **La prueba de recuperación no está hecha.** Borrar el clon, restaurarlo desde
  el remoto, cronometrar y exigir verde. Es el único test que mediría lo único
  que el producto promete —que te lo llevas y vuelve— y solo se ha hecho por
  accidente, nunca a propósito.
- ~~**El rango de intérpretes tiene dos puntos, no un intervalo.**~~
  **CERRADO (M-D80e).** Los cinco puntos están corridos: 3.10.12, 3.11.16,
  3.12.13, 3.13.15 y 3.14.4, todos 225/225 con `uv run --python X.Y
  ./bin/pruebas`. Lo que sigue sin cubrir es la **distribución**: las cuatro
  medidas con `uv` fijan el intérprete y corrieron en una sola máquina.
- **Verificación independiente: solo hasta `5a86cc6`.** El Preceptor reprodujo
  224/224 en otra máquina sobre ese árbol. `fd518b6` está verificado únicamente
  en el Soberano, en dos intérpretes.

---

## 4 · DEUDA PARA M4 · LA FORJA

**Esto no diseña M4.** El diseño de la mecánica pedagógica no sale de aquí. Lo
que sale de aquí es la **deuda**: lo que M3 dejó sin medir y que M4 hereda,
escrito para que no se pierda entre misiones.

### La deuda principal

M3 mide **estado**. La Forja tiene que medir **aprendizaje**, y esa es una clase
de afirmación distinta: el estado se lee en una tabla, y lo aprendido no.

De los límites de arriba sale una condición que M4 no puede saltarse sin repetir
el error de M3: **si el aprendizaje no deja artefacto, no se puede medir, y lo
que no se puede medir se declara `NO_DATA` en vez de darse por hecho.** Una
barra de progreso que muestra lo que no puede medir es una barra falsa, y en
cuanto la persona lo descubre deja de creerse el resto de la pantalla (D76).

### Lo que M3 entrega a M4, ya funcionando

- Un perfil con un escritor único y `ON CONFLICT` (D80).
- Recorrido reanudable con estados por columna y cero `DELETE`.
- Tiempo medido por sala, con `-1` para lo no medido y mínimo de dos medidas
  para hablar de media.
- Una puerta de permiso que falla cerrada.
- Un generador determinista, que es lo que hace reproducible una huella.
- Un modo sabotaje que exige que las pruebas se pongan rojas.

### Lo que M4 no debe heredar

- **Suites que fabrican lo que van a comprobar.** Es el defecto que ocultó
  cuatro bugs en M3 y sigue sin auditarse en el resto de las suites.
- **Criterios que se numeran distinto que sus tests.** Barato de evitar al
  escribirlos, caro de descubrir auditando.
- **Cifras sin su máquina.** Desde D79c la cabecera declara intérprete y
  temporal; lo que se mida en M4 se reporta con las dos cosas o no se reporta.

### La condición de entrada

**Este acta está firmada** (Soberano, 2026-08-16), así que esa condición está
cumplida. Quedan las otras dos que el Soberano puso al firmar: `p0x` en jetson,
y la deuda técnica de arriba cerrada. Abrir un frente nuevo con el
anterior sin acta es lo que este proyecto lleva un mes evitando: código sin
acta, y después nadie sabe qué se decidió ni por qué.

---

## 5 · ESTADO MEDIDO AL CIERRE

```
── AURELIUS · TODAS LAS PRUEBAS ────────────────────────────────
  Python 3.14.4 · /usr/bin/python3
  [...]
  225 pruebas · 13 suites · 6 corredores

── SABOTAJES · se exige rojo ───────────────────────────────────
  ok    test_idioma.py --sabotaje       4/4 detectadas
  ok    test_fuga.py --sabotaje         6/6 detectadas

VERDE · 225/225          salida=0
```

| Verificación | Dónde | Árbol |
|---|---|---|
| 225/225, salida 0 | Soberano · Python 3.14.4 (sistema) | actual |
| 225/225, salida 0 | Soberano · Python 3.10.12 (`uv`) | actual |
| 225/225, salida 0 | Soberano · Python 3.11.16 (`uv`) | actual |
| 225/225, salida 0 | Soberano · Python 3.12.13 (`uv`) | actual |
| 225/225, salida 0 | Soberano · Python 3.13.15 (`uv`) | actual |
| 224/224, salida 0 | **máquina independiente** · Python 3.10.12 | `5a86cc6` |

---

**FIRMADA · Pisky · Soberano · 2026-08-16.**
