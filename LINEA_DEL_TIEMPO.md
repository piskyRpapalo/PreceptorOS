# LÍNEA DEL TIEMPO · PreceptorOS

> Registro cronológico del ecosistema. Espejo idéntico en todos los repositorios excepto CineK (decreto del Soberano, 2026-10-28): lo que el silicio descubre en un repo se puede leer desde cualquiera.
> Ley del registro: append-only — la historia no se reescribe, se añaden días. Cada entrada cita PR, commit o fichero; lo no medido dice NO_DATA con su causa.
> Curada por la Mesa (orquestador): preceptor-orquestador-github.

## 2026-10-28 · la gran jornada

**Web — las dos muertes de la puerta vieja (autor: claude)**
- web#390 → main 10506b5: 301 /play/ → /openworld/ conservando query. La puerta del mapa viejo muere en la web pública.
- web#391 → main 2270db3 (cabeza 0b1bbac): purga del service worker. VERSION abkh; precache sin la pila del juego viejo — los clientes instalados dejan de verlo. CI verde completo (gates n=2).
- Corte D (borrado físico de la pila theGame, 6 commits, cabeza local cb2cbaa): PENDIENTE DE PUSH (manos del Soberano). Dentro vive el decreto INTRO: solo OpenWorld + Tools. En vivo: NO_DATA hasta fusión.
- bb-lote1 (cabeza local 210e6f0): TABLA_SEMANTICA ampliada aditivamente (campos nuevos por estado sin romper los 7) + escenario F2.1 con referencias BigInt independientes. Detrás de D: rebase + re-sello.

**App — la colonia caminante y el manifiesto (autor: codex)**
- Lotes h→q (FIRMOs por pieza del Soberano): app#121 rutas sembradas de habitantes · #122 autoría de nodos · #123 servicios de edificio · #124 pin del gemelo isométrico · #125 contrato colony-projection/1 (x=48q+24r, y=12r, ambas superficies) · #126 liveness por poll · #127 contrato de terminales (the Risen y Atlantis preservados) · #128 frames de caminantes · #129 admisión de nodos bajo firma del Soberano (instalar sin firma: MEDIDO exit 0; sin firma: NO_DATA sin nivel 3).
- Pila caminante (FIRMO «firmo todo»): #130 fixture caminante → a8a25c4 · #131 nota del bus de estado → 23aaea9 · #132 densidad 9 habitantes → 8ed5d4f · #133 capas de suelo → 16f6eb3. Suelo de 3 capas (parche de patrón repetible + campo de densidad + dispersión por hash de celdas con RANGO ACOTADO declarado; claro con banda de borde; y-ordering; previews pintados por el renderizador real) — técnica medida de Starnet, identidad nunca.
- #134 manifiesto MVP de interfaz → main d5bf02d (FIRMO ·6480161599): 41 ítems — LEY 12 / FALTA 12 / ADAPTAR 11 / PUERTA 6. Hallazgos medidos: 404 vivos en las dos rutas apex de Tools; lexicón base de 182 entradas; /play/ 301. Puertas nombradas sin construir: red de labs por nodo, estado del lab en el mapa, E-STOP/correa por nodo, aprobaciones remotas por nodo.
- Decreto pantalla de inicio (encargo servido en #134 ·6480119172): «tutorial» desaparece de la superficie de inicio — el tutorial es el path determinista DENTRO de OpenWorld (llave → faro → primera pelea); el bocadillo de Tools abre una PESTAÑA APARTE con las tools hoy escritas abajo, paridad de contenido probada; nada de controles muertos.
- Ley de la Mesa asentada: jamás transcribir shas a mano — se leen del PR por API y pasan directas al merge; la guarda expectedHeadSha es la última muralla (dos 409 bajo firma errónea, cero fusiones).

**Decretos del corpus (dictados por el Soberano, asentados por la Mesa)**
- Presupuesto D2: 25 MiB por bloque SUSTITUYE TODO; el tope de 16 KiB queda revocado entero; 1.024 B siguen para frames, paquetes y llms.txt.
- Vocabulario vetado en TODO (código, interfaz, CI, docs): siete términos retirados por decreto; la figura renombrada se llama HEXELION — el orquestador de IA local del rack; «nodo hexelion» = el nodo del rack pintado en el mapa. Silicio propone, carbono firma.
- Canon de cosecha: fórmula de cosecha y constantes de hash = canon firmado con procedencia (cosechado y verificado 32/32 del tesoro medido, 2026-10-26). Regla ODD: ideas, ejemplos y joyas cuentan como firmados; se registran en el repo con cita y la gacha honesta construye sobre el registro.
- Radio del Estado en dos fases: fase 1 por frame (la melodía es el estado; 8 notas pentatónicas por cifra; el pulso sale de la MISMA f(t) que el audio); fase 2 por estado del juego.
- APP = BUILDER DE NODO (norte): los usuarios componen su nodo desde la app y despliegan su lab; estructura verificable primero, construir encima después.
- Referencias de técnica: Bot Crossing (primera) y Starnet (segunda). MIT cubre solo código; nombre, logo, sprites y arte OFF LIMITS: técnica sí, identidad nunca.

## 2026-10-27 · canon cosechado
- Canon matemático del juego cosechado y verificado (32/32 joyas con cita fichero:línea, TABLA_JOYAS + joyas.jsonl). Detalle: canon-matematicas (registro interno de la Mesa) y el libro de firmas.
- Pre-firmas y papeles antiguos asentados: firmas/PRE_FIRMAS_Y_JOYAS_PAPELES_ANTIGUOS_20261026.md. NO_DATA: eventos del 27 con cita puntual — registro en el libro de firmas.

## 2026-10-20 → 26 · rescate y plan unificado
- Plan de preceptores unificado (p0x PLAN_PRECEPTORES_UNIFICADO_20261021.md); mapa del ecosistema unido en 15 partes (p0x planes/MAPA_ECOSISTEMA_UNIDO_20261021*.md); comisión M0–M10 a codex; fusiones de la noche del 26-10 (firmas RECIBOS_FUSIONES_NOCHE_20261026.md).
- Misión F0→F3 con codex en curso (tarjetas E1–E8); faro 244/244 sin drift.

## 2026-08 · el producto
- v1.0 (2026-08-22): primera memoria local-first — SQLite en un fichero, rito de primera ejecución, borde de redacción, fusible. v1.1 (08-25): rutas de datos selladas. v1.2 (08-26): el temario emergente. v1.3 (08-26): capas de soberanía y kill switch — el producto arranca en nivel 0 y no se sube solo. Cita completa: CHANGELOG.md del repo de la app.

## Raíces y gobierno
- Norte: mapa vivo (the rift), post-MVP, el lab controla la web 24/7 en tres fases (L1 observar → L2 alarma → L3 palancas por git+API, jamás sirviendo).
- Censo canónico de repos: study/11-repos.md — el drift contra él es ROJO.
- Censos vivos de estado: lab/STATE.md (snapshot con fecha; re-medir antes de fiarse), app/CHANGELOG.md, docs del repo web.
- Protocolo de la Mesa: el carbono firma por pieza sobre cabeza exacta (FIRMO); recibos en el canal del buzón y el libro de firmas; SCRUB en todo lo público.

## Ley de este espejo
- Este fichero es idéntico en todos los repositorios del ecosistema excepto CineK.
- Cada actualización AÑADE; lo ya escrito no se toca (append-only).
- Lo no medido dice NO_DATA con su causa, jamás cero, jamás inventado.

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA