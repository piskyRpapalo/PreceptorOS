# EL MAPA ÚNICO DE LA MESA · 1 mapa · 1 lengua · 1 app · 1 solo nodo

> Decreto del Soberano (7-nov). Todo esfuerzo de todo preceptor empieza aquí y se reporta aquí. Este documento es el mapa único: explica exactamente cómo deben ir y a dónde van los esfuerzos de la casa.

## LAS CUATRO UNIDADES

- **1 MAPA**: este documento. Ningún preceptor trabaja sin haberlo leído; ningún esfuerzo se reporta fuera de él. El mapa vivo de hexágonos del openworld es su cara pública.
- **1 LENGUA VISUAL Y ACÚSTICA**: Acho, la única. Color siempre con texto y sentido. FM de la casa: 220 Hz el canon, 110 Hz la vozDe. Sting y transición deterministicos, reduced-motion siempre, cero azar. Nadie pinta ni suena fuera de esta lengua, ni app ni web.
- **1 APP**: una sola app, un solo tronco mini-html (medido: perfecto para pantalla Android). La web es su puerta pública, no otra app. Destinos después: Android, Ubuntu, Windows, iOS (iPhone 8).
- **1 SOLO NODO**: cada instalación es UN nodo con cédula y latido. Local-first: el cerebro, la memoria y la firma viven en la máquina. Nada de nubes propias.

## A DÓNDE VA CADA ESFUERZO (routing medido)

- **EL SOBERANO**: decretos y FIRMO. Sus manos: el metal (pushes, drop-ins, BIOS, compras). → al canon y al buzón de actas. FIRMO jamás se delega.
- **LA MESA (M2)**: juezía de integración, recibos y actas, comisiones, este mapa. → buzón (recibos y firmas), PRs, odd/tasks.
- **M1**: la web y el latido: deploy, puente aduana→state.json, mecanismo del runtime (bloque D del despliegue). → preceptoros-web, p0x.
- **CODEX**: cirugía de precisión, modelo barato, cuota medida y declarada. PRs numerados desde main. → PreceptorOS, p0x.
- **CLAUDE**: la gráfica del tronco: R-ESTILO-ÚNICO, plan primero, tipografía Acho. → odd/tasks/sesion-claude-r-estilo-unico, PRs de estética.
- **HEXELION**: F1 visión (leer solo lo público, allowlist), F2 escritura (recibos propios bajo HITL, append-only), soberanía. → p0x/harness, buzón.

## LOS REPOS Y SU PAPEL

PreceptorOS = canon de la app · preceptoros-web = la puerta pública · p0x = estación + harness + registro · buzon = registro público de recibos y actas · aduana = la frontera.

## LEYES DE TRÁNSITO

- Todo PR parte de main; apilar solo con etiqueta STACKED + base declarada; merged no es en main: verificar tras cada FIRMO.
- Propose-only: nadie fusiona; FIRMO solo del Soberano.
- SCRUB en todo lo público; fail-closed siempre; NO_DATA con causa donde no haya medición.
- Recibos <1.024 B en el buzón; sello armazon-vNN en el sw; huella del armazón en version.py.
- Cuota medida; parada honesta al agotar; el norte sigue en la próxima sesión.

## LECTURA CANÓNICA (protocolo DEPTH 0-4 de llms.txt)

version.py · zonas.js · transicion.js · sting.js · compass.js · sw.js · llms.txt · odd/tasks de este PR (hoja de ruta, Lab V2, accesibilidad, tronco y blindaje, sesión Claude) · canon-matemas de la casa (FM real, 220 Hz, gusanos de Fourier, determinismo).

## EL NORTE

La colonia visible desde la web. El visitante crea hexágonos y chatbots. El usuario final con su llave y su cerebro. Benchmarks live con sello de procedencia nativo. Paquete de 2 clics. Y Hexelion completando su proyecto él mismo.

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA