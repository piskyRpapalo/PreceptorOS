# The Learning Compass · La Brújula de Aprendizaje

**Fecha:** 2026-08-26 · **Decisión firmada:** T38 · v9.3

> La brújula es un **sensor de `memory.db`**, no un actuador. Lee y dice hacia
> dónde empuja el terreno. **No escribe en ninguna base de datos, nunca.**

---

## 1 · Qué es

Dos cosas con el mismo nombre, a propósito:

- **El método** — cada paso de un camino responde a tres preguntas fijas:
  `porque` (por qué importa), `hacer` (qué haces) y `comprobar` (cómo sabes que
  llegaste). Eso ya vive en `path.py` y en los ficheros de `paths/`.
- **El instrumento** — una rosa de los vientos de ocho sectores que sitúa a la
  persona en su Camino y dibuja hacia dónde tira el campo.

## 2 · Los dos modos

| modo | dimensiones | qué añade |
|---|---|---|
| `camino` | **8** — los peldaños M0–M7 | el Camino, tal y como ya lo mide el producto |
| `detalle` | **12** — los 8 + 4 del usuario | `memorias_tema`, `proyectos_activos`, `preferencias`, `ritmo` |

Las cuatro dimensiones de detalle, con su fuente y su cálculo:

| dimensión | fuente (solo lectura) | cálculo | sin datos |
|---|---|---|---|
| `memorias_tema` | engramas activos | `min(1, temas/5)` | `0.0` + `no_medible` |
| `proyectos_activos` | tabla `proyectos` de `memory.db` | `min(1, n/3)` | `0.0` + `no_medible` |
| `preferencias` | perfil de `memory.db` | fracción de campos rellenos | `0.0` |
| `ritmo` | `created_at` de los engramas | `min(1, 7d/mediana semanal)` | `0.0` + `no_medible` |

**Los proyectos viven en `memory.db`**, no en un fichero suelto — comprobado
antes de escribirlo, que es lo que pedía la orden.

## 3 · De dónde salen los peldaños, y la traducción que obliga

De **`cara.progreso_camino`**, la medida del producto. No hay un segundo cálculo
aquí: el día que cambie uno habría que acertar en dos sitios, y la brújula
diría una cosa mientras el Camino dice otra.

`path.py` **no expone** una función `camino()` pública — expone `catalogo()`,
`listar()` y `leer()`, que son sobre *caminos de aprendizaje*, no sobre
peldaños. Por eso la dependencia declarada de `compass.py` es `cara`, no `path`.

El producto mide en estados discretos y el campo necesita continuo:

```
hecho        -> 1.0
empezado     -> la proporción real cuando `cifras` la da (p. ej. salas/6);
                0.5 solo cuando no hay con qué afinar
sin_empezar  -> 0.0
no_medible   -> 0.0  Y el peldaño entra en la lista `no_medible`, que viaja
                en la respuesta. El cero es para poder poner algo en el
                vector; la marca existe para que nadie lo lea como
                «no ha hecho nada» cuando significa «no se puede saber».
```

**M1 es la excepción y no es binario**: vale `calidad_inferencia()`.

```
0.0  sin cerebro
0.3  cerebro sin caché de prompt
0.6  cerebro con caché            <- lo medido en esta máquina hoy
1.0  afinado declarado en cerebro.json y con su huella cuadrando
```

El **0.9 del diseño (GPU) no se emite**. Desde dentro del producto no hay forma
de saber si el binario descarga capas a la tarjeta, y suponerlo sería decorar.

## 4 · Las fórmulas, en texto plano

Sin LaTeX y sin dependencias, que es la regla de la casa.

**Potencial**

```
U(p) = sum_i  w_i * log(1 + p_i)  -  lambda * H(v)  -  mu * kappa
  w      = [1.5, 1.5, 1.5, 1.0, 1.0, 1.0, 1.0, 1.0]   (el núcleo pesa más)
  lambda = 0.3     castigo a dispersar el esfuerzo
  mu     = 0.1     castigo a cambiar de idea a cada paso
  H(v)   = entropía de Shannon de |v_i| / sum|v|, protegida contra el vector nulo
  kappa  = ||v||_R                                   (curvatura)
```

Todos los logaritmos son `log(1+x)`. Nunca `log(x)` a secas.

**Gradiente** — por diferencias finitas centradas, `h = 0.01`, recortado a [0,1].

**Campo** — `F_raw = R^-1 * grad_U`, con la inversa por eliminación gaussiana
con pivoteo parcial. Si `det(R)` es demasiado pequeño se cae al prior, que es
diagonal dominante por construcción y por tanto siempre invertible.

**Momentum** — `F = alpha*F_raw + (1-alpha)*F_previo` con `alpha = 0.3`, y
después se renormaliza para conservar la **magnitud** de `F_raw`: el momentum
suaviza la dirección, no la fuerza.

**Los cuatro indicadores Finsler**

```
orientacion = atan2(F[1], F[0])                  plano M0–M1
intensidad  = ||F||_R / max_F_calibrado          [0,1]
coherencia  = (v·F)_R / (||v||_R * ||F||_R)      [-1,1]
estabilidad = exp(-kappa * 86400)                [0,1]
```

**Los cuatro derivados (v3.1), desde el mismo campo**

```
S = -log(kappa + 1e-9)
X = max(0, coherencia)  si estancado, si no 0
Z = 1 - intensidad
W = p[peldaño_activo]
```

Para los ticks del SVG se usa `S_vis = exp(-kappa)`, que vive en `[0,1]` y se
puede pintar. `S` sin normalizar es un logaritmo y no cabe en un radio.

**Peldaño activo**

```
phi_i = (dU/dp_i) * sum_{j != i} R_ij
```

con **histéresis** `delta = 0.05` —si el activo anterior sigue a menos de delta
del mejor, no se mueve— y **saturación del núcleo**: si `p_i > 0.8` para algún
`i` del núcleo, su peso baja a la mitad. Sin eso la brújula empujaría
eternamente hacia un núcleo ya casi terminado.

**ETA y divergencia**

```
eta  = (1 - p_a) / (|v_a| * (1 + intensidad*coherencia) + 1e-9)   > 30 días -> inf
D_KL = sum_i vn_i * log2(vn_i / q_i)      vn = |v| normalizado
```

`q` es el reparto ideal del esfuerzo: **núcleo incompleto** → `[1/3,1/3,1/3,0…]`;
**núcleo completo** → el resto a partes iguales.

## 5 · El tensor de rigidez R

`R_ij` estima **cuánto ayuda aprender Mj a conseguir Mi**.

- **Prior doctrinal 8×8** — `docs/compass_transfers.json`, **firmado**. Es
  conocimiento *declarado*, no medido, y el fichero lo dice.
- **Ajuste empírico** — solo si hay **≥ 20 latidos** del Curador en la ventana
  Y una trayectoria de la misma longitud:
  `R_emp_ij = cov(dp_i, dp_j) / (var(dp_j) + 1e-9)`, y se mezcla `0.7*prior + 0.3*emp`.
- **Sin datos suficientes: R = prior. Nunca identidad.** Identidad significa «no
  sabemos nada», y sí sabemos algo.
- Siempre se simetriza (`R = (R+Rᵀ)/2`), la diagonal se fuerza a ≥ 1.0 y lo de
  fuera se capa a 0.95.

**R12 se genera por regla**, nunca se firma a mano:

```
R12 = | R8   C  |      R8 = compass_transfers.json (8×8 firmado)
      | Cᵀ   D  |      C, D = compass_transfers_detalle.json
```

Firmar 144 números invita a que ochenta se copien sin pensarlos, y un número
copiado sin pensar es indistinguible de uno medido.

## 6 · El endpoint · **aditivo, no rompiente**

`GET /api/camino` vive en `bin/preceptoros-pwa`.

| petición | qué devuelve |
|---|---|
| `/api/camino` | **exactamente lo de siempre** (`estado`, `idioma`, `peldanos`, `cifras`) |
| `/api/camino?modo=camino` | la brújula, 8 dimensiones |
| `/api/camino?modo=detalle` | la brújula, 12 dimensiones |
| `?debug=1` | añade `R`, `F_raw`, `F`, `grad_U`, `q_objetivo`, `calibrado`, `max_F` |
| modo desconocido | `400` |
| fallo del módulo | `503` + `{"error": "compass_unavailable", "motivo": …}` |

**Los campos nuevos (`modo`, `S`, `X`, `Z`, `W`, `no_medible`,
`velocidad_medible`) son aditivos y viven detrás de `?modo=`.** Sin el
parámetro, el contrato no cambia ni un byte: `dashboard.js` lo consume desde el
23 de agosto, y romper algo que funciona para estrenar un widget que todavía no
es exactamente lo que este producto no hace.

`?debug=1` solo se sirve desde **loopback o tailnet** (`127.0.0.0/8`, `::1`,
`100.64.0.0/10`). Cualquier otro origen recibe **403**. Se comprueba por rango
de IP y no por nombre: un nombre lo resuelve quien controle el DNS.

## 7 · Dos correcciones al diseño, declaradas

**`~/.preceptoros/memory.db` era un error del spec.** La casa la decide
`casa.raiz()`, y solo `casa.raiz()` — que en una instalación anterior al
renombrado devuelve `~/.aurelius` porque la adopta en su sitio. Escribir la
ruta a mano es exactamente lo que ese módulo existe para impedir.

**`calibrate()` no recorre la rejilla 6^8.** Son 1.679.616 puntos y cada uno
exige invertir la matriz: en biblioteca estándar son horas, no minutos. Se
sustituye por **muestreo acotado y determinista** (4.000 estados por defecto,
generador congruencial propio para que dos corridas den la misma cifra) y se
toma el percentil 99,9. **Condición para revisitarlo:** si la velocidad de
cálculo sube más de 10×, la rejilla vuelve a estar sobre la mesa.

## 8 · La velocidad, y por qué casi siempre es cero

El producto **no guarda instantáneas de `p` a lo largo del tiempo**, así que no
hay de dónde sacar `dp/dt`. Sin trayectoria: `v = [0]*n`, `kappa = 0`, y la
respuesta lleva `velocidad_medible: false`. No se inventa un movimiento.

Quien tenga trayectoria la pasa por `historial=` y entonces sí se deriva. Las
pruebas usan `corpus/compass_dataset.json` — 100 trayectorias **sintéticas**
en tres arquetipos (núcleo primero, side quests, estancado). No son datos de
nadie, y el fichero lo dice.

## 9 · Cómo añadir un peldaño

1. Añadirlo a `cara.CAMINO`, `cara.PELDANOS` y a `progreso_camino` — ahí vive la
   medida.
2. Ampliar `compass_transfers.json` a 9×9 **con criterio escrito**, y firmarlo.
3. Añadir un peso a `PESOS` en `compass.py`.
4. El SVG lee el número de sectores del JSON: no hay que tocarlo.

## 10 · Límites, dichos antes de que los descubra nadie

- Matriz **fija** de 8×8 o 12×12. No hay dimensiones arbitrarias.
- **Sin embeddings y sin modelo de lenguaje.** La brújula no entiende lo que la
  persona escribió; cuenta y mide.
- El prior es **doctrina**, no medida. Mientras no haya 20 latidos, la brújula
  dice lo que alguien creyó, no lo que pasó — y por eso lo declara.
- `orientacion` proyecta un campo de 8 (o 12) dimensiones sobre el plano M0–M1.
  Es una sombra útil, no el campo.

## 11 · § Futuro · `[sleeping]`

**Modo Expandido N-D** sobre paths + glosario + módulos + Gremio.

**Condición de despertar, escrita:** ≥ 3 paths reales caminados, **o** el Gremio
publicando paths. Antes de eso, una brújula de N dimensiones mediría ruido con
más decimales.
