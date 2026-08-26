# ANÁLISIS DOCTRINAL · v1.2 · el temario emergente

**Fecha:** 2026-08-26 · **Estado:** PROPUESTA. Espera firma del carbono.
**Commit del cambio:** `362eca1` · **Suite:** 481/481 · 35 suites.

> **Nota sobre el origen de este documento.** La orden decía «usa la tabla que
> te paso arriba como base». Esa tabla **no venía en el mensaje**. Lo que sigue
> se construyó desde el árbol —grep, pruebas y metadatos reales— y no desde una
> tabla que no llegó. Donde hay juicio mío y no dato, está marcado **[juicio]**.

---

## 1 · El cambio, en una línea

| | v1.1 · reactiva | v1.2 · emergente |
|---|---|---|
| La regla | *«NUNCA propongas el tema ni el dominio: no es tuyo»* | *«Eres su temario»* |
| Qué hace | narra lo que pasó y devuelve el turno | **conecta lo que la persona ya trajo** y ofrece el siguiente paso desde ahí |
| Qué protege | que nadie te imponga un tema | lo mismo, y además que el producto **lleve a algún sitio** |
| El riesgo que abre | — | que «eres su temario» se lea como barra libre para traer temas de fuera |

El matiz entero cabe en una frase: **cambia de dónde sale lo que se propone, no
si se propone.** De la memoria de la persona, jamás de un catálogo.

## 2 · Todo artefacto que referenciaba la doctrina vieja

Barrido completo del árbol más los metadatos. **Cero restos.**

| # | Artefacto | Qué decía | Qué dice ahora | Verificado |
|---|---|---|---|---|
| 1 | `conversacion.py` · `GUIA["es"]["proyecto"]` | «NUNCA propongas el tema ni el dominio» | «Eres su temario. […] conecta esas piezas» | `grep` = 0 |
| 2 | `conversacion.py` · `GUIA["en"]["proyecto"]` | «NEVER propose the subject or the domain» | «You are their syllabus. […] connect those pieces» | `grep` = 0 |
| 3 | `conversacion.py` · `GUIA[*]["nucleo"]` | «Pregunta una cosa cada vez» | + «engancha lo que pregunte con lo que ya te haya contado» | test |
| 4 | `conversacion.py` · `GUIA[*]["decision"]` | «No elijas por él» | «Puedes decirle cuál conecta mejor; elegir sigue siendo suyo» | test |
| 5 | `conversacion.py` · `GUIA[*]["side_quest"]` | «parada opcional» | «hito opcional» + «recuerda por qué le importaba» | test |
| 6 | `test_conversacion.py` | `test_..._no_propone_dominio` | `test_..._es_el_temario` + 2 conductuales | 43/43 |
| 7 | `README.md:8,10` · **titular** | «It has no syllabus… never picks the subject» | «It **is** your syllabus — the one that emerges from what you already brought» | `grep` = 0 |
| 8 | `README.md:52` · título de sección | «It does not choose your subject» | «It is your syllabus, not a catalogue» | `grep` = 0 |
| 9 | `README.md:60-63` · cita de la regla | la frase vieja, en bloque | la frase nueva, en bloque, bilingüe | `grep` = 0 |
| 10 | `README.md:70-77` · explicación | «no tiene ningún curso que venderte» | explica **de dónde** sale el siguiente paso y qué sigue prohibido | — |
| 11 | `README.md:79,90` · peldaños | «optional stops» / «paradas opcionales» | «milestones» / «hitos», con la diferencia escrita | `grep` = 0 |
| 12 | `textos.py:93,264` | «take an optional stop» / «hacer una parada opcional» | «reach an optional milestone» / «alcanzar un hito opcional» | 481/481 |
| 13 | `cara.py:487` · comentario CSS | «las paradas opcionales» | «los hitos opcionales» | — |
| 14 | **Descripción de GitHub** | *«…It never picks your topic.»* | *«Your syllabus, not a catalogue: it connects what you already brought…»* | `gh repo view` |
| 15 | **Topics de GitHub** | 12 | 14 · `+learning-compass` `+personal-knowledge` | `gh repo view` |
| 16 | `CHANGELOG.md` | — | entrada v1.2 bilingüe, con permitido/prohibido separados | — |

**Capturas del README:** revisadas una a una. Ninguna muestra la doctrina vieja
en pantalla — los pies describen la brújula, la memoria y una conversación
concreta, no la regla. **No hay que recapturar por este cambio.**

## 3 · Lo que la doctrina nueva PROHÍBE

1. **Traer un dominio que la persona no nombró.** Sigue intacto, y ahora es la
   mitad del test: si `GUIA` nombrara «python», «música» o «trading», la suite
   se pone roja. Sin esa mitad, «eres su temario» sería permiso para cualquier cosa.
2. **Desplegar un programa que no se ha pedido.** Literal en la guía: *«ni le
   montes un programa que no ha pedido»*.
3. **Flujos predefinidos.** Un recorrido fijo que todo el mundo camina es un
   catálogo con otro nombre.
4. **Inventar sobre memoria vacía.** Con cero engramas no hay de dónde conectar,
   y hay una prueba que lo fija: el prompt no puede nombrar un dominio.

## 4 · Lo que la doctrina nueva PERMITE

1. **Conectar piezas que ya están en su memoria** y ofrecer el siguiente paso
   desde ahí.
2. **Decir cuál de dos caminos engancha mejor** con lo que contó. Elegir sigue
   siendo suyo.
3. **Recordar por qué algo le importaba** cuando vuelve a ello.
4. **Agrupar lo guardado.** Agrupar es leer; sugerir un tema nuevo es escribir
   en la cabeza de alguien.

## 5 · Qué sobrevive, qué se adapta y qué muere del plan F4–F16

| Fase | Veredicto | Por qué |
|---|---|---|
| **F4** · The Path + brújula interactiva | **SOBREVIVE Y GANA** | El «temario adherido determinista desde engramas» **era ya** la doctrina nueva antes de que se escribiera. Deja de ser un extra y pasa a ser la función principal de la página. |
| **F4b** · curso base del MVP dentro de The Path | **SE ADAPTA** | Un curso base es un catálogo. Puede **ofrecerse** y no desplegarse: visible si se busca, jamás propuesto sin que se pida. **[juicio]** |
| **F5** · curso Python ~10 pasos + terminal ficticia | **SE ADAPTA · es la baja mayor** | Diez pasos fijos que todo el mundo camina son exactamente un «programa que no ha pedido». Sobrevive **solo** como camino opt-in: la persona lo elige, nadie se lo sugiere, y no aparece en la conversación por su cuenta. Si no puede cumplir eso, muere. **[juicio]** |
| **F7** · Translator en The Border | **SOBREVIVE INTACTO** | Trabaja sobre texto que la persona pega. No trae dominio: simplifica el que ya vino. |
| **F8** · capturas + README | **SOBREVIVE** | Mecánica. El titular ya está al día; las capturas no muestran la regla. |
| **F9** · gate de novato | **SE ADAPTA** | Su lista de comprobación incluía «no propone tema». Pasa a: *no trae un dominio que no se nombró* y *conecta lo que sí se trajo*. |
| **F10/F13** · nightly-qa, rol `doctrine-auditor` | **SE ADAPTA** | Su checklist decía «no propone tema». Con v1.2 eso daría falso positivo en cuanto el producto haga bien su trabajo. Hay que reescribirlo antes de montarlo, o el bucle nace midiendo la doctrina anterior. |
| **F11** · ECOSISTEMA.md | **SOBREVIVE** | Inventario. |
| **F12** · versión en ambos installs | **HECHO** | `version.py`, commit `7b20dd1`. |
| **F14** · puerta de la v1.1 | **SE ADAPTA Y SE RENUMERA** | Ya no hay v1.1 que cerrar: el siguiente tag es **v1.2**. Los criterios de `docs/PUERTA_v1_1.md` valen; el nombre no. |
| **F15** · REPL de terminal | **SE ADAPTA** | Decía «misma personalidad: se presenta una vez, jamás propone el tema». La segunda mitad cambia. |
| **F15b** · coding agéntico | **SIGUE `[sleeping]`** | Sin cambios. |
| **F16** · CENTRO_DE_MANDO.md | **SOBREVIVE** | Plan de consolidación, ajeno a la doctrina del producto. |

## 6 · Lo que este cambio deja sin resolver

- **La brújula mide peldaños, no temas.** Si el temario emerge de los engramas,
  la pregunta natural es si el Camino debería reflejarlo. Hoy `cara.CAMINO` son
  ocho hitos fijos y el tensor de la brújula está firmado sobre ellos. **No se
  toca sin decisión aparte.**
- **La taxonomía de la lámina** (7 misiones: Origen, Lenguaje, Recuerdo,
  Frontera, Seguridad, Soberanía, Verdad) sigue sin aplicarse, y ahora choca
  menos: si los peldaños son hitos emergentes, renombrarlos cuesta más, no menos.
- **`PreceptorAA` / el orquestador** no entra aquí. Queda como capas opcionales
  (`aa.py`, `aa_mem.py`) que no tocan el núcleo, y después de esta firma.

---

*Nada de la sección 5 se ha ejecutado. F4, F5 y F7 siguen sin existir, que era
el momento barato para cambiar la doctrina y es por lo que este documento llega
antes que el código.*
