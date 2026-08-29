---
id: mision-escaparate
clase: producto
version: 1.0.0
fecha: 2026-08-29
metrica: personas que terminan M1 con tok/s y TTFT medidos en SU maquina (objetivo → 1 por instalacion); cifras de rendimiento mostradas sin medir (objetivo → 0)
umbral: no se re-edita sin diez Cahiers reales que hayan pasado El Olvido
presupuesto_kb: 12
n_medicion: 10
enlaces: [espec-cahier, mision-tenedor, handoff-v83]
---

# MISIÓN · EL ESCAPARATE
### La primera vez que alguien mide su propia máquina en vez de creerse una cifra.
*Autor: el Preceptor · Canoniza: el Soberano · Ejecuta: CC*

---

## MOTIVO

Quien llega, llega por curiosidad. No sabe qué es un token, no sabe cuánta memoria
tiene su GPU, y la industria entera lleva años diciéndole cifras que no puede
comprobar. El Escaparate no le enseña esas cifras: le enseña **a medirlas**.

La primera misión no produce un producto. Produce **un Cahier con dos números
dentro que la persona sacó de su propio aparato**: tokens por segundo y TTFT. A
partir de ahí ya no depende de que nadie le diga si su máquina sirve.

**Principio:** una cifra medida por ti vale más que una recomendación. Y una cifra
que no puedes medir se declara `NO_DATA`, no se rellena.

---

## LO QUE EL ESCAPARATE **NO** ES (leer antes de diseñar)

- **No es un tutorial.** No hay lecciones antes de la práctica. La persona escribe
  una pregunta, el modelo contesta, y la medición ocurre encima de esa conversación
  real. Si hace falta leer tres pantallas antes de tocar nada, se diseñó mal.
- **No es un benchmark.** No compara la máquina de nadie con la de nadie. Mide
  ESTA máquina, la escribe en ESTE Cahier, y ahí se queda. La comparación pública
  es el Libro de Pruebas, y es voluntaria y posterior.
- **No promete que el modelo sea bueno.** El Escaparate enseña el borde, no el
  brillo. Termina con el modelo fallando a propósito.
- **No pide una cuenta, ni un correo, ni un identificador.** El Cahier nace en el
  aparato. Si la misión necesitara un servidor para completarse, se diseñó mal.
- **No toca valor.** IronClaw íntegro.

---

## EL CONTRATO

### Los dos peldaños

| Peldaño | Qué hace la persona | Qué queda escrito en el Cahier |
|---|---|---|
| **M0 · El primer turno** | Escribe su primera pregunta y recibe respuesta del modelo local | El Cahier existe: fichero creado, `agente.json` inicial, primer engrama de conversación |
| **M1 · La medida** | Repite un turno con el cronómetro puesto | `tok_s` y `ttft_ms` medidos, con el modelo y el motor con que se midieron |

### Las dos cifras, y cómo se declaran

- **`ttft_ms`** — milisegundos hasta el primer token. Es la que la persona *siente*.
- **`tok_s`** — tokens por segundo en generación. Es la que decide si un bucle es
  viable esta noche.

Las dos se guardan **con su contexto o no se guardan**: modelo, cuantización,
motor (WebLLM / LanguageModel / local), y fecha. Una cifra sin el modelo al lado
no se puede reproducir, y una cifra que no se puede reproducir no es una medida:
es una anécdota.

**Honest sensors, sin excepción:** si el navegador no expone lo necesario para
cronometrar, se escribe `NO_DATA` con su causa —`sin WebGPU`, `motor no
declara tiempos`— y la misión **continúa**. Un Escaparate que exige una medida
imposible convierte a la mitad de la gente en fracasada por tener otro portátil.

### El Cold Start: cinco engramas antes del primer turno

El modelo local no sabe qué es un token. Eso **no es una avería**: el
conocimiento del vocabulario vive en el Cahier, no en los pesos. Por eso el
Cahier nace con cinco engramas ya dentro:

`token` · `ttft` · `no_data` · `cuantizacion` · `contexto`

Cuando la persona pregunta «¿qué es un token?», el modelo declara `NO_DATA` y la
recuperación del Cahier pone la definición delante. **Esa es la lección de M0, y
es la lección más importante de todo el producto:** el modelo no sabe; la memoria
sí; y la persona puede leer y cambiar esa memoria.

### El evento · **El Olvido**

Al final de M1, la conversación se lleva **a propósito** más allá del borde de
contexto, y el modelo olvida algo que se dijo al principio. No se simula: se
empuja de verdad y se enseña el número.

Lo que la persona aprende en ese momento no es que el modelo sea malo. Es que **el
contexto es finito y medible, y el Cahier es lo que no se olvida**. El Olvido es
el argumento entero del producto, contado por la máquina en vez de por un texto.

### La lámina-seed

Al cerrar la misión, el Cahier fija una semilla determinista derivada de las dos
medidas y de la fecha. Con ella se dibuja la lámina de la persona. Misma semilla,
misma lámina, siempre: es un recibo de que las cifras son suyas, no un adorno
aleatorio.

---

## FASES

### F0 · El censo de motores (primero, y puede cambiar el diseño)
Inventariar qué motores existen de verdad en los navegadores reales y cuáles
declaran tiempos aprovechables para cronometrar. Sin este censo, `ttft_ms` es una
promesa. Si ningún motor da tiempos fiables, F2 cambia de forma.

### F1 · El Cahier nace
Crear el esquema, escribir los cinco engramas del Cold Start, y demostrar que la
recuperación los encuentra. Gate: preguntar «qué es un token» devuelve la
definición del Cahier con su origen declarado.

### F2 · La medida
Cronometrar TTFT y tok/s sobre un turno real y escribirlos con su contexto. Gate:
dos ejecuciones seguidas producen dos filas distintas y ninguna se inventa.

### F3 · El Olvido
Empujar el contexto hasta el borde de forma reproducible y registrar el número
real. Gate: el borde medido coincide con el declarado por el motor, o se declara
la discrepancia.

### F4 · La lámina-seed
Derivar la semilla, dibujar, y comprobar el determinismo: misma entrada, misma
lámina, en dos navegadores distintos.

### F5 · Verificación
Recorrer la misión entera desde una instalación limpia, sin red después de la
descarga del modelo, y comprobar que el Cahier resultante se abre con `sqlite3`
a mano.

---

## INVARIANTES

- **Cero cifras sin medir.** Ningún número de rendimiento aparece en pantalla si
  no salió del aparato de quien mira. `NO_DATA` con causa es una respuesta válida;
  un valor por defecto no lo es.
- **La misión se completa sin red** una vez el modelo está en el dispositivo.
- **El Cahier es un fichero SQLite** que la persona puede abrir con otra
  herramienta. Si hiciera falta la aplicación para leerlo, se diseñó mal.
- **localStorage no persiste nada.** Solo buffer de reconciliación.
- **10 KB por fichero** de interfaz. Sin excepción y sin negociación.
- **El Olvido se mide, no se narra.**
- PARA y reporta al final de **cada fase**. No se encadenan.

---

## PROMPT PARA CC (una fase por sesión)

```
MISIÓN · EL ESCAPARATE, fase F<n>.
Lee mente/misiones/MISION_ESCAPARATE.md entero antes de tocar nada,
incluida la sección "LO QUE EL ESCAPARATE NO ES".

Ejecuta SOLO la fase F<n>. Respeta las INVARIANTES.
Si una cifra te hace falta y no puedes medirla en esta máquina, escribe
NO_DATA con su causa y sigue: inventarla es exactamente lo que esta misión
existe para eliminar.

Reporta en formato de 12 líneas. Cierra con 3-6 SUGERENCIAS (S/M/L) anexadas a
mente/feedback/PENDIENTES.md. PARA. No encadenes fases.
```

---

## CHANGELOG

**v1.0.0 (2026-08-29)** · Creación. Destilado del Handoff v8.3 (Misión 1, peldaños
M0-M1, evento *El Olvido*, Cold Start de cinco engramas, lámina-seed). Se añade el
censo de motores como F0 porque `ttft_ms` depende de que el motor declare tiempos,
y eso no estaba comprobado en ningún sitio.
