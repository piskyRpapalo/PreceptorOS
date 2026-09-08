# Matriz de cumplimiento · qué hace cada pieza, en idioma de auditor

**Para quién es esto.** Para alguien que tiene que dictaminar si este sistema
puede desplegarse en una empresa, y que no debería tener que leer 40 ficheros
de Python para averiguar qué controles existen. Cada fila nombra **la función
real** que implementa el control, en la forma `<fichero>.py::<funcion>`, para que se pueda ir a mirar.

**Qué NO es.** No es un certificado, ni una declaración de conformidad, ni una
promesa de que este sistema cumple el AI Act. Es un mapa: dice dónde está
implementado cada control y dónde **no** lo está. Los huecos van dentro, en su
propia sección, y con la misma letra que lo demás — un mapa de cumplimiento que
solo enseña lo que cumple es material de venta disfrazado de auditoría.

**Cómo se mantiene honesto.** `test_compliance.py` lee este fichero, extrae
cada referencia con la forma `<fichero>.py::<funcion>` y comprueba que existe en el árbol. El
día que alguien renombre una función, este documento se pone rojo en el gate en
vez de envejecer en silencio. Un documento de cumplimiento que se desincroniza
del código no es documentación desactualizada: es una afirmación falsa sobre un
sistema, que es exactamente lo que un auditor viene a buscar.

---

## 1 · Supervisión humana · AI Act art. 14

La ley exige que una persona pueda entender, vigilar e **interrumpir** el
sistema. Aquí eso no es una capa encima: es la ley más profunda de la casa,
`IronClaw` — *el silicio propone, el carbono firma*.

| Control | Dónde vive | Qué hace exactamente |
|---|---|---|
| Interrupción de emergencia | `soberania.py::modo_santuario`, `soberania.py::salir_de_santuario` | Entra y sale del estado en que el sistema deja de proponer. Entrar y salir son **dos gestos distintos**: salir nunca es un efecto secundario de otra cosa |
| Estado de la supervisión | `soberania.py::santuario_activo`, `soberania.py::obtener_nivel` | Se consulta, no se recuerda. Un permiso que se guarda en una variable es un permiso que sobrevive al gesto que lo dio |
| Permiso por nivel | `soberania.py::verificar_permiso`, `soberania.py::exigido`, `soberania.py::exige` | Cada operación declara qué nivel de soberanía exige. La comprobación es explícita y su negativa lleva causa (`soberania.py::causa`) |

**Lo que un auditor debe saber:** el nivel de soberanía es del operador
humano, no del proceso. Ningún bucle automático lo sube.

---

## 2 · Confidencialidad y perímetro · ISO 27001 A.8.10 · AI Act art. 10

| Control | Dónde vive | Qué hace exactamente |
|---|---|---|
| Sanitización de salida | `guardrails.py::redactar_salida` | Redacta lo que no debe cruzar. Lo que viaja al registro es **clase y cantidad, jamás el fragmento** — el registro de una fuga no puede contener la fuga |
| Puerta única de salida | `memory.py::cruzar_frontera` | Una sola puerta. Antes eran dos llamadas y la segunda hasheaba el texto **ya redactado**, con lo que el registro no podía probar qué salió |
| Registro de lo que cruzó | `memory.py::registrar_salida`, `memory.py::resumen_salidas` | Deja fila con canal, estado y motivo. Se puede enseñar a un tercero **porque no contiene lo que salió** |
| Preparación del envío | `guardrails.py::preparar_envio` | El paso que decide qué sale, separado del que lo manda |
| Políticas efectivas | `guardrails.py::ruta_politicas`, `guardrails.py::_politicas_efectivas` | Las políticas se leen de fichero, no se compilan dentro. Un auditor puede leer las que están vigentes |
| Aislamiento de ejecución | `frontera.py` (celda Wasmtime) | Memoria acotada, CPU acotada por combustible determinista, **sin sistema de ficheros y sin red**. Un módulo que importe algo del anfitrión no llega ni a instanciarse |

**Lo que un auditor debe saber:** el sandbox está instanciado y listo, y **no
ejecuta nada por sí mismo**. Solo corre código cuando una misión con mandato
llama a proponer.

---

## 3 · Trazabilidad y registro · AI Act art. 12 · ISO 42001 §8.3

| Control | Dónde vive | Qué hace exactamente |
|---|---|---|
| Registro de interacciones | `captura.py::registrar` | Guarda el par entero. **Nunca levanta**: se llama con la respuesta ya entregada, y a esas alturas un fallo aquí no puede romper el turno. Devuelve `None`, que es decir «no se guardó» |
| Qué contexto viajó | `captura.py::asegurar` (columnas `ctx_ids`, `ctx_tokens`, `ctx_fuera`, `ctx_completo`) | Sin esto, dos averías que piden arreglos **opuestos** son indistinguibles: alucinar con el dato delante, o no tenerlo delante |
| Veredicto **con juez nombrado** | `captura.py::juzgar` | Un veredicto sin juez es una opinión con cara de medida. Se distingue quién juzga: el carbono, otro modelo, o un comprobador determinista |
| Tasa de acierto | `captura.py::rendimiento` | Calculada solo sobre lo **juzgado**. Un turno sin juzgar no es un turno fallado |
| Procedencia de lo importado | `importar.py::importar` | Origen, firma y autor de cada corrección que entra desde fuera, con `firma_ok` explícito |
| **El producto DEJA línea** | `captura.py::consentir`, `captura.py::corregir`, `captura.py::juzgar`, `importar.py::importar` | Los cuatro actos que el art. 12 quiere ver registrados escriben su evento **dentro de la misma transacción** que el cambio: o entran los dos, o no entra ninguno. Nunca hay un cambio sin su registro |
| Clase de evidencia del juez | `captura.py::_actor_de` | La columna guarda el juez tal cual —el tag completo del modelo—; la línea guarda su **clase**. Un acierto firmado por un comprobador determinista no vale lo que uno firmado por un modelo que opina |
| **Registro encadenado append-only** | `linea.py::anotar`, `linea.py::verificar` | Cada evento lleva dentro la huella del anterior. Cambiar uno viejo obliga a recalcular todos los siguientes, y `verificar` lo ve y **dice en cuál**. No se pisa nada: una rectificación escribe un evento nuevo que apunta al viejo |
| El estado como pliegue | `linea.py::pliegue` | El estado actual se **calcula** recorriendo lo que pasó, con la procedencia de cada valor. Por eso «qué sabía el sistema el martes» tiene respuesta |
| El tramo auditable | `linea.py::tramo` | Recorta la línea por fecha y por sujeto. Es lo que dibuja la barra de tiempo y lo que consulta un auditor a mano |
| Sello de integridad | `huella.py::leer`, `memory.py::_recuento_verificable` | Demuestra que la memoria no cambió, sin decir lo que dice |
| Copia y restauración | `memory.py::respaldar`, `memory.py::restaurar` | Contingencia y rollback |

**El detalle que más vale ante un auditor:** el vocabulario de veredictos
distingue **callarse bien** de **fallar**. `no_data` (dijo «no lo sé» y de
verdad no lo sabía) y `traspaso` (dijo «esto le toca a otro» y le tocaba)
cuentan como **aciertos**. Un banco de pruebas que los puntúe como error
entrena al modelo a inventar antes que a callarse.

---

## 4 · Transparencia y no engaño · AI Act art. 50

> **Nota de numeración, y conviene leerla.** El acta de diseño citaba «art.
> 52», que es la numeración del **borrador de 2021**. En el texto publicado
> —Reglamento (UE) 2024/1689— las obligaciones de transparencia son el
> **art. 50**; el 52 pasó a ser la clasificación de modelos de propósito
> general con riesgo sistémico, que es otra cosa. Lo cazó `test_compliance` al
> cruzar este documento contra `normas.py`, que es exactamente el fallo para el
> que se escribió ese cruce.
>
> **Esto lo debe confirmar un jurista antes de que salga a un cliente.** Aquí
> se corrige lo que se puede comprobar por coherencia interna; la validez de
> una cita legal no la dictamina un test.

| Control | Dónde vive | Qué hace exactamente |
|---|---|---|
| La ausencia se declara | `NO_DATA` en todo el árbol; p. ej. `medidas.py::desde_paquete` | Un campo sin dato sale `null` **y con su causa**. Nunca una estimación «para que la tabla quede bonita» |
| Cifras sin respaldo | `cifras.py::sin_respaldo`, `cifras.py::aviso` | Marca las cantidades que no salen de la pregunta ni de lo que el sistema sabe de la máquina. **Marca, no censura**, y el aviso dice «nadie las ha comprobado», no «son falsas» |
| Formas peligrosas en la salida | `output_guard.py::inspeccionar`, `output_guard.py::preparar_respuesta` | Bloquea comandos destructivos por forma. **Declara lo que no frena**: variables, codificaciones e indirecciones |
| Trazas de razonamiento | `traza.py::generar` | Lo que el sistema dice que hizo, junto a lo que hizo |

**Lo que un auditor debe saber, y que casi ningún sistema declara:**
`output_guard.py` documenta en su propia cabecera lo que **no** puede frenar,
porque «un output-guard que se presenta como filtro completo invita a confiar
en él para lo que no puede hacer, y eso es peor que no tenerlo».

---

## 5 · Autonomía del operador · riesgo de cadena de suministro

| Control | Dónde vive | Qué hace exactamente |
|---|---|---|
| Cero dependencias externas | `test_superficie.py` | Recorre el grafo de importaciones desde las tres puertas del producto y exige que el camino por defecto sea **biblioteca estándar pura**. La lista de excepciones está **vacía** |
| Identidad del aparato | `soberano.py::codigo_de`, `soberano.py::declarar`, `soberano.py::quien` | Quién manda en este aparato, derivado sin sal para que coincida con el navegador |
| Medida de la máquina real | `medidas.py::desde_paquete`, `medidas.py::backend` | Lo que este hardware da de sí. El backend se **pregunta** a quien lo sabe, no se supone |

**El argumento de venta, dicho sin adorno:** el camino por defecto no alcanza
ninguna dependencia externa, y eso lo comprueba una prueba en cada gate — no
una afirmación en un README.

---

## 6 · Los huecos · lo que hoy NO se cumple

Esta sección tiene el mismo peso que las cinco anteriores. Un mapa que solo
enseña lo verde no es un mapa.

| Hueco | Qué falta exactamente | Consecuencia para una auditoría |
|---|---|---|
| **Firma criptográfica** | La biblioteca estándar de Python no trae Ed25519. `importar.py` guarda las firmas que recibe con `firma_ok = NO_DATA`: ni comprobadas ni rechazadas | **No hay no repudio.** Los registros son íntegros (se detecta si cambian) pero no están firmados: no se puede demostrar ante un tercero quién los produjo |
| **Sellado de tiempo** | Las marcas de tiempo las pone la misma máquina que emite el registro | Una fecha que depende del firmante no fecha nada ante un tercero |
| **Append-only en las tablas viejas** | `linea.py` ya es append-only y encadenado, pero `engrams`, `profile` y `turnos` siguen admitiendo `update` — diez, contados | Los eventos nuevos están protegidos; **el histórico anterior a la línea, no**. La migración de esas tablas es la pieza que queda |
| **Anclaje externo de la cadena** | La cadena detecta manipulación **parcial**. Quien pueda escribir el fichero puede rehacerla entera y volver a encadenarla | Sin publicar la última huella donde no se pueda retocar, o sin firma, la evidencia protege del retoque puntual y no del reescrito completo. **Está probado como tal**, no supuesto |
| **Evaluación de sesgos del adaptador** | Entrenar un LoRA modifica el perfil de riesgo del modelo base (AI Act art. 10) y hoy no se documenta sistemáticamente | Un adaptador desplegado sin su documentación de propósito y sesgos es un cambio de perfil de riesgo sin declarar |
| **Verificación de retención de PII** | La Frontera redacta, pero no hay un banco de pruebas ciego que lo demuestre con un conjunto de datos conocido | «Redacta» es hoy una afirmación de diseño, no una medida |

---

## 7 · Las anclas legislativas · `normas.py`

Cada concepto de la casa lleva declarado **qué artículo lo juzga**, en una sola
tabla y no repetido por el árbol: `normas.citas("linea")` devuelve
`AI Act art. 12`, `art. 19`, `ISO 27001 A.5.33`, `A.8.15`, `ISO 42001 8.3`.

**No es un renombrado, y esa decisión está firmada.** El acta de la Notaría
pide que *«el alma de la casa se mantenga, pero se traduzca al idioma de los
auditores»*. Renombrar `frontera` a `perimetro_de_sanitizacion` costaría las
dos cosas a la vez: el vocabulario que la gente ya usa, y la trazabilidad de
todo lo escrito hasta hoy, que quedaría hablando de una pieza con otro nombre.

**Y anclar no es cumplir.** El ancla señala al juez, no al veredicto:
`sello_soberano` está anclado *y* declarado como hueco en la sección 6, a la
vez. Si anclar significara cumplir, esta tabla sería una declaración de
conformidad escrita por el propio interesado.

Cada fuente lleva su **edición** (`normas.FUENTES`), y hay prueba que lo exige:
los artículos del AI Act cambiaron de número entre borradores y las ISO se
revisan. Una cita legal sin edición es una cita que nadie puede comprobar.

La consulta que hace un auditor —llega con «art. 12» en la mano— es
`normas.anclados_por("ai_act", "art. 12")`.

---

## 8 · Cómo verificar todo esto sin fiarse de este documento

1. `python3 -m pytest -q` · la suite entera.
2. `bin/pruebas` · el corredor, que además ejecuta **sabotajes**: rompe el
   código a propósito y exige que las pruebas se pongan rojas. Una suite verde
   sobre código roto no prueba nada, y eso también se comprueba.
3. `python3 test_superficie.py` · el candado de las dependencias.
4. `python3 test_compliance.py` · que cada función citada aquí exista.
5. `python3 test_normas.py` · que ninguna cita apunte a una fuente
   fantasma y que cada fuente diga de qué edición habla.

