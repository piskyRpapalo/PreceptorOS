# Joyas ronda 3 · solo lo no escrito (7-nov-2026)

> Tercera pasada de la lapidaria, cortada con deduplicacion real: cada joya de aqui NO estaba en ningun paquete previo (plano F0, doc joyas ronda 1, insumo de 7 puertas, addendums, joyas ronda 2). Minas: hoja-de-ruta-pestana-por-pestana, plan-accesibilidad, tronco-y-blindaje, lab-v2-fabrica-de-tests (docs de este PR #195). Leyes intactas: crear lo que falte, no inventar lo no medido; FIRMO del Soberano por cabeza exacta; SCRUB.

## Las 7 joyas

1. **LAB V2, contrato completo** · Casa: odd/tasks/lab-v2-fabrica-de-tests-20261107.md. El plano F0 cubre las rebanadas i-iv (lab_avisos, prueba_edificio, lora_dataset), no el contrato: experimentos = titulos del Soberano; telemetria de agentes SOLO de senales medidas (sin senal = NO_DATA con causa, edad del dato visible); reporte de estado <=100 caracteres en ventana cerrable, solo hechos medidos, jamas inferido; enlaces Lab-Hablar/Modelos/Web/Cuaderno; registro fabrica/1 {id, titulo, estado, novedades, agentes[], edad}. Puerta: LAB-1 censo -> LAB-2 cara -> LAB-3 enlace vivo harness-app -> LAB-4 ciclo cerrado (F2 redacta sus reportes).

2. **CUADERNO T9: mini-terminal** · Casa: hoja-de-ruta-pestana-por-pestana-20261107.md. Un mini-terminal para pegar textos grandes. Puerta: el Cuaderno y la Frontera dejan de pelearse con el insertor de 1 KB.

3. **HARNESS: ciclos declarados** · Casa: hoja-de-ruta-pestana-por-pestana-20261107.md. Cada bucle declara su periodo junto a la edad del dato en la cara; sin declaracion = NO_DATA con causa. (La edad del dato ya esta servida en addendum; el ciclo declarado, no.)

4. **Lock de la cuenta efimera** · Casa: hoja-de-ruta-pestana-por-pestana-20261107.md (norte). A voluntad del usuario: partida persistente hasta liberarla. Puerta: la cuenta cangrejo gana sesion sin dejar de ser efimera por diseno.

5. **Blindaje zero-trust del conjunto** · Casa: tronco-y-blindaje-20261107.md. Tras la piel: nada suena, ni cuenta, ni mide, ni sale sin decreto. Despues: benchmarks LIVE de dispositivos con sello de procedencia nativo (fuente+sha, firma de la casa, NO_DATA visible). Luego: traduccion a destinos (Android, Ubuntu, Windows, iOS), jamas copias paralelas: un tronco, muchos destinos.

6. **Accesibilidad: lo que falta medir** · Casa: plan-accesibilidad-20261107.md. NO_DATA a medir: cobertura ARIA de los 9 paneles, orden de foco al cambiar de pestana, contraste medido de app.css, prueba real con lector de pantalla; heredar la doctrina web a la app. Ya medido (no rehacer): role="status" en app.html, 44px tactiles, reduced-motion nativo, 8 lenguas, color nunca solo.

7. **interactive-widget=resizes-content** · Casa: ventana de referencia (~420x680), 1 atributo del meta viewport. Puerta: el teclado movil no devora la ventana y el insertor anclado abajo sigue visible al escribir. Cura de una tension medida, no un adorno.

## Nota de deduplicacion

La ronda 2 (joyas-ronda2-puertas-20261107.md) re-sirve unas 16 puertas ya escritas en paquetes previos; 2 de sus joyas estan desfasadas: el indice de memoria ya fue abierto (preview con base propia, citas medidas, calentamiento 7,9 s) y la IX ya vive como app#205 (draft HITL). El litigio #189/#190/#191 esta cerrado (superseded por #194).

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA