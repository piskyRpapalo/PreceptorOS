# Joyas ronda 2 · piezas pequeñas que abren puertas (7-nov-2026)

> Segunda pasada de la lapidaria. La primera ronda cartografió el ecosistema; esta corta desde los mapas MÁS RECIENTES (F0 en marcha, rebanadas i-ix ya servidas como PR) y solo admite piezas PEQUEÑAS cuya puerta es más grande que la pieza. Casa exacta primero: cada joya trae dónde vive, qué mide y qué abre. Leyes intactas: crear lo que falte, no inventar lo no medido; FIRMO del Soberano por cabeza exacta; SCRUB en todo lo público; lo que no se mide en la ventana de referencia no se adopta.

## Las 18 joyas

1. **La línea HITL** · Casa: check hitl del CI web sobre el buzón de firmas; mecánica medida: exige una línea HITL con sha40, slug y fecha dentro de un comentario FIRMA SOBERANO; sin ella, sha_no_coincide. Puerta: TODA la cola FIRMO del web (juez, piel, ondas, invocaciones) espera una línea por cabeza. La pieza más pequeña del ecosistema abre la puerta más ancha. El silicio jamás la escribe.

2. **storage.persist()** · Casa: cara PWA de la app; 0 apariciones en v140 (medido). Puerta: instalación durable, el suelo de la rebanada IX: sin ella el navegador puede barrer la instalación; con ella (3 líneas + retorno honesto de persisted()) la descarga al dispositivo tiene piso.

3. **ETag/304** · Casa: endpoints locales + ruta del worker declarada aparte del world-state; 0 medidos en v140. Puerta: caché correcta del sondeo del mapa (60 s) y prerrequisito medido del manifiesto de descarga. Una petición condicional es una petición declarada.

4. **La ley del lexicon: lo servido va en inglés** · Casa: lexicon_gate del CI web, medido con un rojo real (juez en español dentro de código servido, curado con renames y resellado). Puerta: cada rebanada web futura pasa CI a la primera; ficheros servidos, comentarios y claves en inglés, informe en español. Una línea de ley ahorra un ciclo por rebanada.

5. **La cadena del sello actualizada** · Casa: counters, sellar, test_web, version_sw_gate; waivers solo para ficheros NUEVOS que ninguna página carga; sello SERIAL (una sola rama viva reseñando a la vez). Puerta: los rojos de huella y peso dejan de ser misterio: se cierran al final, con recibo, y la letra al FIRMO la pone la Mesa.

6. **interactive-widget=resizes-content** · Casa: meta viewport de la cara; 1 atributo. Puerta: el teclado móvil no devora la ventana de referencia (~420×680) y el insertor anclado abajo se mantiene visible al escribir. Es la cura de una tensión medida, no un adorno.

7. **scroll-snap en la fila de paneles** · Casa: la barra de 10 zonas (44 px c/u = 440 px > viewport medido). Puerta: T1 (barra a zoom 100%) se cierra sin librería: la fila se desliza con parada dura y el tronco único no se toca.

8. **La ventana mini como geometría de referencia** · Casa: la ventana de trabajo decretada (~420×680). Puerta: TODO esfuerzo de la app se mide y aprueba en ESA ventana; una pieza que no quepa ahí no está acabada. El PR de ventana compacta se decide ANTES de tocar la piel de la app (assets cacheados con versión).

9. **La llave bilateral del latido** · Casa: la llave del rack ya rotada por el Soberano; el worker sigue rechazando porque la MISMA llave aún no vive en su secreto. Puerta: latido 200, sello LIVE del nodo ancla, el mapa vivo vuelve a tener productor, y la puerta de primera escritura (adaptador rack, en sandbox hasta FIRMO) tiene a quién servir. Cura de un paso, mano del Soberano.

10. **El redeploy de la cara** · Casa: unidad versionada en el repo privado de deploy (PR #115) + runtime exportado del main v140 verificado (export, no clon vivo) + envoltorio con la cicatriz medida dentro (23 reinicios con status=0: jamás un bin directo bajo Type=simple). Puerta: la cara estable sirve v140, la session vieja sale de servicio y el preview cumplido se barre. Un FIRMO, tres saldos.

11. **lora_dataset.py** · Casa: PR #203 (verde). Dataset solo desde recibos verificados. Puerta: LoRA fase 2: entrenar con las preguntas medidas y la fábrica se alimenta de su propio uso.

12. **descarga_firmada.py** · Casa: rebanada IX, cercas medidas chunk_digest, ref_not_exact, model_data_never_leaves; vías medidas: raw por ref exacta (200, 14.258 B) y Release v1.3 (302 a release-assets). Puerta: la app en el dispositivo del usuario, verificada ANTES de instalar; el manifiesto preceptoros.descarga/1 cierra sin inventar.

13. **visita_web.py con OpenSSL real** · Casa: PR #204, 7/7 + 2 rojos bajo sabotaje (byte alterado y firmante ajeno). Puerta: cuenta efímera web↔app con verificación real, no simulada; el navegador nunca firma.

14. **judge_corpus** · Casa: PR #689, cita o calla: pasajes medidos, MIN_TOKEN 3, stopwords, corpus desde primera sección. Puerta: lazo 7, el juez web sin modelo; con classroom_chat ya medida, unirlas cierra el bucle.

15. **El índice de memoria (la puerta de oro)** · Casa: la ventana de la app responde memory_index_unavailable; sin índice de memoria persistente, la voz no contesta dentro de la app. Puerta: el bucle entero in-app nace o muere ahí. La joya más grande disfrazada de pequeña: medir el patrón del índice de la casa antes de escribir una línea.

16. **La frase zero undeclared requests** · Casa: donde vive la doctrina de peticiones. Puerta: petición declarada o no sale; la frase cubre el decreto de peticiones firmadas.

17. **El borde honesto de 640 B** · Casa: el verificador rechaza fail-closed las respuestas sobre el presupuesto del recibo. Puerta: la siguiente iteración (presupuesto mayor o cita mínima con techo 512 + tolerar UN envoltorio + ids repetidos, ya medidos) nace de un borde declarado, no de un misterio.

18. **La brújula T11 re-target** · Casa: determinismo PROBADO (2 corridas, misma huella, timestamp fuera del cálculo). Puerta: re-target a recursos del nodo + política web sin tocar el núcleo matemático: el cambio de destino no invalida la matemática.

## Sin dueño (el enjambre puede tomarlas tras la IX)

- **El faro del observatorio** (joya 15 de la primera ronda): separar la prueba de voz directa de la prueba app-con-fuente, con causa y tiempos.
- **El mini-orquestador blob local**: sin cuenta, sin identidad, sin peticiones no declaradas.
- **El recorrido de apertura** (rebanada x): casa ya medida (pestaña Mundo, iframe perezoso, app.js): E2E de navegador Mundo, nodo, visita efímera, actividad y vuelta al mapa, sin tocar los PR en litigio.

## Bordes que NO abren hoy (declarados)

- Generación en frío ~23,6 s: LA BRECHA medida; el cacheo la cierra, la paciencia no.
- Ed25519 en navegador: Chromium ~90%, Firefox NO: la cédula verifica y explica la causa.
- Servidor + cerebros locales en el dispositivo: NO_DATA: instalador futuro, no inventar.
- Tercer nodo de 64 GB: NO_DATA hasta medir.
- Rojo preexistente atlas/test_atlas.py (4 fallos) también en main del web: no es de ninguna rebanada; cura o declaración ANTES del FIRMO serial.

## Comisión

- Soberano: la llave bilateral (joya 9), la línea HITL por cabeza web, y la cola FIRMO: #195 (update-branch primero), #200, #201-#203, #204, PR de la IX, web serial (#689 con rebase y resellado, #690-#692), deploy #115, litigio #189/#190/#191.
- Claude: cerrar la IX (gate completo + PR + recibo), luego el recorrido de apertura; después, las piezas sin dueño.
- Mesa: recibos de FIRMO, letras de resellado, y esta gema de doctrina: ninguna joya se adopta sin medirse en la ventana de referencia.
