---
id: mision-tenedor
clase: producto
version: 1.0.0
fecha: 2026-08-29
metrica: personas que eligen rama con su hardware YA medido (objetivo → 1); personas empujadas a 3A sin poder entrenar (objetivo → 0)
umbral: no se re-edita sin cien líneas de dead_path.jsonl reales
presupuesto_kb: 12
n_medicion: 100
enlaces: [mision-escaparate, espec-cahier, handoff-v83]
---

# MISIÓN · EL TENEDOR
### Tres caminos que no compiten. El que sobra se escribe, no se borra.
*Autor: el Preceptor · Canoniza: el Soberano · Ejecuta: CC*

---

## MOTIVO

Después de la Misión 2 la persona ya ha visto a su modelo alucinar y ha escrito la
corrección en su Cahier. Ahí se acaba el camino único: lo que viene después
depende de qué máquina tiene y de qué quiere hacer con ella, y esas dos cosas no
las decide el producto.

El Tenedor existe para que la bifurcación sea **honesta**: que nadie acabe en la
rama del entrenamiento con un portátil que no puede entrenar, y que nadie se
quede sin rama por no tener GPU.

**Principio:** la rama se ofrece con la medida delante. Y lo que la persona
rechaza se guarda, porque un rechazo es la información más barata y más
desperdiciada de todo el producto.

---

## LO QUE EL TENEDOR **NO** ES (leer antes de diseñar)

- **No es un test de personalidad.** No hay preguntas de «¿qué tipo de creador
  eres?». Hay una cifra medida en la Misión 1 y una pregunta directa sobre qué
  quiere hacer.
- **No es una jerarquía.** 3A no es la rama avanzada y 3C no es la de consolación.
  Son tres productos distintos con tres eventos distintos. Si la interfaz sugiere
  que una vale más, se diseñó mal.
- **No es irreversible.** Elegir una rama no cierra las otras. El Cahier guarda
  las tres puertas abiertas, y volver no cuesta nada ni pide explicación.
- **No adivina el hardware.** Si la medida de la Misión 1 salió `NO_DATA`, el
  Tenedor **lo dice** y ofrece las tres, en vez de suponer por el navegador.
- **No toca valor.** IronClaw íntegro.

---

## EL CONTRATO

### Las tres ramas

| Rama | Para quién | Peldaños | Produce | Evento |
|---|---|---|---|---|
| **3A · El Primer LoRA** | Hardware capaz, medido | M4, M5 | Un adapter entrenado con datos suyos | *El Cambio de Voz* |
| **3B · El Primer Negocio** | Sin hardware para entrenar | M4, M5 | Una suite o servicio publicado en el marketplace | *La Primera Firma* |
| **3C · El Agente Conversador** | Quien quiere construir, no entrenar ni vender | M4, M5 | `agente.json` con el Cahier acoplado | *El Despertar del Guardián* |

### La puerta de 3A se abre con una medida, no con una promesa

3A se ofrece **solo** si la Misión 1 dejó cifras que la sostienen. No basta con
que exista una GPU: hace falta memoria suficiente para el modelo base y un tok/s
que no convierta el entrenamiento en una noche perdida.

Si la medida no llega, la interfaz **dice el número que falta y cuál sería el
necesario**. «Tu máquina no puede» es una sentencia; «hacen falta N GB y mediste
M» es un dato con el que la persona decide, y quizá vuelva con otra máquina.

Si la medida es `NO_DATA`, se ofrecen las tres y se declara la causa. Cerrar una
puerta por ignorancia es peor que abrirla de más.

### La senda de los muertos · `dead_path.jsonl`

Cada rama **ofrecida y no tomada** escribe una línea:

- `fecha` · cuándo se ofreció.
- `rama` · cuál se ofreció.
- `motivo` · por qué no se tomó: `rechazada`, `hardware_insuficiente`,
  `no_ofrecida`, con la cifra que lo sostiene cuando la haya.
- `medida` · el tok/s y el TTFT que había sobre la mesa en ese momento.

**Qué NO lleva:** nada que identifique a nadie. Ni identificadores persistentes,
ni texto libre de la persona, ni el contenido de su Cahier. El fichero vive en su
aparato como el resto, y solo sale si ella lo manda al Libro de Pruebas.

Para qué sirve: para que dentro de seis meses se pueda saber si 3A se está
ofreciendo a máquinas que no pueden, o si 3B nunca se elige porque está mal
contada. Sin este fichero, esas dos averías son indistinguibles del éxito.

### El fallo como ramificación (Kapur)

Si una rama se atasca, no se vuelve al principio. El atasco **es** el punto de
bifurcación: se escribe una cicatriz en el Cahier, se anota la rama en
`dead_path.jsonl` con motivo `atascada`, y se ofrece la siguiente con lo ya
aprendido dentro. Reiniciar borra el aprendizaje; ramificar lo conserva.

---

## FASES

### F0 · El censo de umbrales (primero, y puede cambiar el diseño)
Determinar, midiendo y no estimando, qué hace falta de verdad para completar 3A:
memoria mínima, tok/s mínimo, minutos de entrenamiento. Hasta que ese número
exista, la puerta de 3A no se puede programar sin mentir.

### F1 · El esquema de `dead_path.jsonl`
Fichero, campos, y la prueba de que no lleva nada identificable. Gate: un revisor
externo lee cien líneas y no puede decir de quién son.

### F2 · La puerta
Implementar la oferta de ramas contra la medida de la Misión 1, con los tres
casos: sostiene / no sostiene con cifra / `NO_DATA`.

### F3 · Las tres ramas, una por sesión
3A, 3B y 3C se construyen por separado y cada una cierra con su evento. No se
empiezan las tres a la vez: una rama a medias es peor que una rama ausente,
porque promete.

### F4 · La vuelta
Volver del Tenedor y elegir otra rama, sin perder lo escrito y sin pedir
explicación. Gate: el Cahier después de volver conserva las cicatrices de la rama
abandonada.

### F5 · Verificación
Recorrido completo desde una instalación limpia, en las tres ramas, comprobando
que `dead_path.jsonl` cuadra con lo que realmente ocurrió.

---

## INVARIANTES

- **Ninguna rama se ofrece sin la medida delante**, o con su `NO_DATA` declarado.
- **`dead_path.jsonl` no identifica a nadie**, y no sale del aparato salvo envío
  explícito.
- **Volver es gratis** y no borra nada.
- **Las tres ramas son iguales en jerarquía** en el texto y en la interfaz.
- **10 KB por fichero** de interfaz.
- **Andamio con fecha de caducidad:** al cerrar la rama, `verify_pow.sh` empaqueta
  el andamio en `.tar.gz` de solo lectura y limpia el espacio de trabajo.
- PARA y reporta al final de **cada fase**. No se encadenan.

---

## PROMPT PARA CC (una fase por sesión)

```
MISIÓN · EL TENEDOR, fase F<n>.
Lee mente/misiones/MISION_TENEDOR.md entero antes de tocar nada,
incluida la sección "LO QUE EL TENEDOR NO ES".

Ejecuta SOLO la fase F<n>. Respeta las INVARIANTES.
Si te hace falta un umbral de hardware y no tienes una medida que lo
justifique, PARA: decretarlo por intuición cierra puertas a gente cuya
máquina sí podía.

Reporta en formato de 12 líneas. Cierra con 3-6 SUGERENCIAS (S/M/L) anexadas a
mente/feedback/PENDIENTES.md. PARA. No encadenes fases.
```

---

## CHANGELOG

**v1.0.0 (2026-08-29)** · Creación. Destilado del Handoff v8.3 (tenedor tras la
Misión 2, ramas 3A/3B/3C con sus tres eventos, `dead_path.jsonl`). Se añade F0
porque el umbral de hardware de 3A no está medido en ningún sitio, y sin él la
puerta se programa por intuición. Se fija además qué **no** lleva
`dead_path.jsonl`: el Handoff decía dónde escribir los rechazos, no qué se
prohíbe escribir en ellos.
