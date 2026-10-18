# Contratos de decisión: forma sin autoridad

Base de integración: `4f384c36d0beef48e920b633ac4246afbc9c4350`, medida el
2026-10-18. Implementación en borrador; no instalada en procesos vivos.

Fuentes de dirección:
[decisión del canal](https://github.com/piskyRpapalo/PreceptorOS/issues/40#issuecomment-6244301336)
y [tier 2](https://github.com/piskyRpapalo/PreceptorOS/issues/42#issuecomment-6244301373).
Son las dirimencias vigentes frente a las propuestas locales anteriores.

## Recuperación y aristas

| Pieza | Función, frontera y vara | Consumidor |
|---|---|---|
| `decision_evento.py` | Valida decisiones sin autoridad; rechazo por campo y bytes | Adaptador local del registro, optativo y aún sin desplegar |
| `eleccion_tier2.py` | Valida elecciones sin inferencia; sabotajes tipados | Productor local de etiquetas, optativo y aún sin desplegar |
| `test_contratos_decision.py` | Prueba ambos contratos con datos sintéticos, sin modelo ni BD viva | unittest y `bin/pruebas` |
| `canales.py` | Conserva la vista del canal existente | Sin cambios en esta pieza |
| `decisor.py` | Conserva tier 1 y su contrato | Sin cambios en esta pieza |

Se recuperan los validadores de los adaptadores locales; no se publica el
registro privado, su BD ni el productor de entrenamiento. Los adaptadores del
worktree privado importan esta fuente mediante `PRECEPTOROS_CONTRATOS` (directorio
explícito de la app). Ninguna instalación ni servicio vivo se modifica. No se
crea otro registro ni se transporta contenido del rack al repositorio público.
El código anterior no tuvo API pública: su orden HLC se retira del trabajo
local, sin alias que vuelva a habilitarlo. No se reescribe el historial.

## Canal L4a

Objeto cerrado: `v=1,rol,alternativas,eleccion,encargo_ref,firmo_ref,sello,ancla,utc`.
`rol` es categoría, nunca identidad privada. Se conserva el vocabulario de roles
y sellos del canal. `alternativas`: 1–20 textos distintos, hasta 64 B UTF-8 cada
uno; `eleccion` pertenece al conjunto. `encargo_ref` usa issue o SHA-256;
`firmo_ref` usa comentario o SHA-256. Una referencia no verifica una firma.
`firmo_ref=null` requiere causa tipada externa; no concede permiso.
`ancla` es fichero relativo:línea o issue:comentario, sin ascensos de directorio.
`utc` es una hora declarada ISO UTC, sin autoridad temporal. El cuerpo canónico
UTF-8 mide menos de 1.024 B; se rechaza entero si no cabe, nunca se trunca.

El orden causal local es `n`, asignado al insertar. No se ordena por UTC, no
se usa HLC ni se introduce política de ganadores. HLC/multi-escritor/A2A:
`NO_DATA`, fuera de esta fase, requiere otra firma. El adaptador conserva el
canal append-only y no abre la BD de autoridad ni siquiera al crear un canal
temporal vacío. Ninguna fila de un canal vivo se escribe para estas pruebas.

Dos recibos espejo llevan solo estado, código, recuento y SHA-256 del payload.
El cotejo recalcula el hash del cuerpo validado; dos huellas falsas iguales no
bastan. Siempre `SIMULATED`, origen `NO_DATA-práctica`. No abre A2A, no publica
ni concede unicidad global. Mapping a registro/supervisión humana sujeto a
revisión; jamás claim de cumplimiento legal.

## Tier 2

Se conserva `hexelion.eleccion.tier2/1`, los campos superiores existentes y
`probs[].opcion/p_bp`. Este validador es exclusivo del tier 2; no cambia ni
reclasifica la salida de tier 1. Campos extra o faltantes producen causas.

- `choice`: una opción cerrada o `NO_DATA`; `noul` es booleano coherente.
  Abstención exige `choice=NO_DATA`, `score=null` y causa. Fuera de 1–20 opciones
  solo cabe abstención con probabilidades vacías; jamás se llama al modelo.
- `score`: número finito o null, sin rango ni umbral semántico. Booleanos,
  NaN e infinitos se rechazan. La confianza nunca prueba acierto. No se impone
  que choice sea el máximo ni que score equivalga a una probabilidad.
- `probs`: cubre las opciones exactamente una vez si hay medida. Valores
  finitos no negativos. La unidad heredada es p_bp; probabilidad = p_bp/10000.
  **EPSILON propuesto/declarado: 0**, suma racional exacta de las representaciones
  decimales. No se usa tolerancia implícita ni suma flotante redondeada. La medida
  sintética acompaña este PR; no es un umbral de adopción del modelo. Cambiarlo
  requiere revisión explícita. Sin declaración exacta, rechazo.
- `judge`: `veredicto` cerrado (acuerdo/desacuerdo/NO_DATA), `contra`, `regla`
  y `calibracion` obligatoria. Esta última contiene estado, SHA-256 de evidencia,
  muestras, aciertos y causa. MEDIDO/SIMULATED requieren hash y conteos válidos;
  NO_DATA requiere hash/aciertos null, muestras 0, causa y veredicto NO_DATA.
  La forma del hash no acredita calibración: su procedencia se revisa por separado.
- `arnes`: tier=2, donde, modelo, modo, hash, build y configuracion obligatorios.
  Digest SHA-256 identifica el artefacto declarado; no se inventa desde su tag.
  Configuración es JSON no vacío y finito. El productor sin rastro rechaza antes
  de inferir; no rellena metadatos reales con fixtures.
- `content_v`, `plan_hash` y `no_data` conservan el rastro. El módulo es puro:
  no abre archivos, sockets, procesos, ledger ni interruptores. Los metadatos
  estructurados completos son carga; el recibo mínimo para el mini permanece
  separado. No se reduce ni fragmenta una cédula para cumplir el techo del recibo.

Los umbrales históricos de un productor local no se convierten en política de
este contrato. Calibración real y umbrales semánticos siguen pendientes, con
causa; solo se prueban artefactos sintéticos en este lote.

## Vara y límites

Rojos antes del verde: HLC, versión extra, elección ajena, UTC inválida,
longitudes 1.023/1.024/1.025, espejo discrepante; score no finito, probabilidades
repetidas/incompletas, desviación de suma, abstención discordante, juez sin
rastro, arnés sin digest/tier incorrecto y campos con efectos laterales.
También una desviación de 1e-300 debe detectarse con EPSILON=0.

Gates separados, dos tandas: runner del adaptador local; contrato puro;
unittest de la app y `bin/pruebas` completo. Sus cifras no se suman. Pruebas
con bases temporales o funciones puras; sin inferencia nueva. El guardián
privado usa su variable de entorno, jamás incorpora los valores al árbol.

B2, sonda real y optimización de hoja de contacto: `NO_DATA`, falta corpus
canónico recibido. Fear-free y scene-legibility permanecen en su worktree
local sin cambios en este lote. No hay UI, transporte nuevo ni cambios en
rutas de cédulas. El silicio no firma: firma el carbono.

## Medición del lote · 2026-10-18

Fuente: `docs/contratos-decision-medida.json`, estado SIMULATED. Corpus fijo:
20 repartos sintéticos, semilla 42, de 1 a 20 opciones, todos suman 10.000
puntos base; error normalizado máximo exacto 0. Dos salidas antiguas inválidas
(sin rastro y abstención con score) pasaban y ahora se rechazan. La desviación
1e-300 se probó roja antes del cálculo racional. Tres mutaciones deliberadas
del validador fueron detectadas. El fixture de productor sin digest pasó de
2 llamadas a 0 (antes aceptaba, después rechaza antes de inferir). Beneficio
real: NO_DATA por corpus canónico ausente; no hay medida de velocidad de modelo.

Las pruebas sintéticas publicadas permiten repetir los límites; el baseline
anterior y el adaptador de productor permanecen locales por privacidad, con
sus hashes en el recibo. La medida no afirma rendimiento de una instalación.
