# Mini-HTML · inventario de paneles de la app única (2026-11-07)

> Decreto del Soberano (transcrito en buzon#30 ·6705344338): una sola app, una sola estética; la única verdad es el mini HTML hecho por codex hoy. Este inventario nombra la app pieza por pieza, para cambios rápidos y cambios profundos. Formato: lista simple hoy; forma mañana.

Medido sobre: interface/{app.html, app.js, zonas.js, compass.js, transicion.js, sting.js, install.js, manifest.json} · base main 8f2bc83 · anatomía del PR #186 cabeza c30d04f. Recibos: buzon#19 ·6705310589 · buzon#30 ·6705344338.

## Cabecero (siempre visible)
- h1 PreceptorOS + p#estado (aria-live): hoy dice "comprobando…" / "no alcanzo al servidor" / "sin cerebro: puedo preguntar y recordar, no conversar".
- button#ir-inicio > span.rostro-preceptor: la esfera con la cara, arriba derecha; en la anatomía del #186 pliega/restaura el carril. La instalación real de la PWA es manifest.json + install.js; la esfera nunca fue ese camino (el pixel art ascii además no fue el recurso usado).
- TAREA 2: p#estado pasa a ser la voz de la app: texto variable que dice en qué panel está quien mira + la telemetría que la app ve del sistema, enfocada a modelos hablando. Multi-idioma como el resto (8 lenguas medidas en app.js).
- TAREA 3: el icono con la cara se ELIMINA; el cabecero queda solo texto e iconos de la app.

## Barra de pestañas · 9 zonas (zonas.js, congeladas)
Orden medido: Mando · Hablar · Frontera · Cuaderno · Lab · Harness · Puerta pública · Modelos · Ajustes.
- TAREA 1 (primera): hoy todo solo cuadra con zoom al 90%; la barra debe caber a zoom 100% sin recorte.
- Efecto al cambiar: transicion.js (gusano armónico determinista, 420 ms, 7 segmentos, canvas, respeta prefers-reduced-motion) + sting.js (candidato al audio del cambio: NO_DATA hasta leerlo).

## Panel 1 · Mando (panel-mando) — la brújula
"la brujula · sensor de tu memoria, nunca actuador" (comentario medido). compass.js pide /api/camino?modo=camino|detalle cada 30 s; cachea en localStorage con la edad del dato dicha en la cara; peldaños M0-M7; rango 0-4 por media (>=0,85->4 · >=0,6->3 · >=0,35->2 · >0,08->1); estados no_medible/completado; botones The Path / Detail. Backend: compass.py + test_compass.py: LA JOYA. NO_DATA: qué mide cada peldaño, hasta leer compass.py.
- TAREA 5 (profunda): estética nueva enfocada a los hexágonos del WorldMap + sistema completo de desarrollo enfocado a las funciones de la memoria de la app, el Lab y los textos locales.
- Funciones objetivo (NO_DATA hoy, lista simple):
  - Vista hexagonal del WorldMap viva en el Mando.
  - El camino de la memoria dibujado sobre el mapa (M0-M7 con sentido).
  - Enlace medido con el Lab y los textos locales.
  - Telemetría de modelos hablando (la misma que el cabecero).

## Panel 2 · Hablar (panel-conversacion)
hilo + textarea#dicho ("Escribe tu respuesta…") + botón "Dilo" + pie "Cada turno tarda minutos en un teléfono. No es que se haya colgado." Hoy habla con el orquestador local; el PR #190 lo conecta al chat local de Hexelion con citas verificadas.
- Funciones objetivo (NO_DATA): conversar con Hexelion verificado · memoria citada en cada respuesta · voz (ACHO FM, canon de la casa) · latencia y modelo declarados en la cara.

## Panel 3 · Frontera (panel-gobierno) — el filtro
Switch "Redacción activa" + insignia "sin medir" + texto a comprobar + "Pasar por el filtro" + hallazgos (clase y cantidad, nada más) + anidar-caja: lo que entraría en tu memoria (texto tachado del servidor, ¿por qué te importa?, anidar) + payload tal cual llegó. Ley del fichero: la interfaz nunca cuenta; fail-closed.
- Funciones objetivo (NO_DATA): filtro siempre presente antes de escribir memoria · causa de cada hallazgo · recibo del anidado en el Cuaderno.

## Panel 4 · Cuaderno (panel-cuaderno)
Recuento (turnos · consentidos · corregidos) + lista de turnos con Consentir/Retirar. Ley: "Un turno capturado no es un turno consentido."
- Funciones objetivo (NO_DATA): consentimiento turno a turno, retirada siempre posible · recibo de cada cambio.

## Panel 5 · Lab (panel-lab)
Canales recientes + Modelos locales (consulta el Lab local).
- Funciones objetivo (NO_DATA): el Lab del rack a la vista · qué cerebro responde en cada canal · estado del modelo activo.

## Panel 6 · Harness (panel-harness)
Frescura + bucles de ciclos locales.
- Funciones objetivo (NO_DATA): ciclos del harness interino declarados · edad del dato en la cara.

## Panel 7 · Puerta pública (panel-puerta)
Llave de entrada (copiar) + Documento que lee la IA (copiar texto fuente exacto). "La vista traduce las marcas de ausencia."
- Funciones objetivo (NO_DATA): la puerta pública de la web lee esto · verificación de la llave desde la web.

## Panel 8 · Modelos (panel-modelos)
Lista de modelos locales del dispositivo.
- Funciones objetivo (NO_DATA): catálogo medido de cerebros del nodo · disponibilidad y sello.

## Panel 9 · Ajustes (panel-ajustes)
Tarjetas medidas: Creation voice · Identidad del nodo (cédula firmada hacia la aduana; esta app no firma) · Create a node (proposal; firma:null; el teléfono jamás firma) · Identidad local y edificio del nodo · Publicar una creación firmada · Bandeja (/api/bandeja).
- Funciones objetivo (NO_DATA): la estación de ajustes del nodo único · sin firmas en el navegador, jamás.

## Orden de tareas (decreto)
1. T1: la barra inferior cabe a zoom 100%.
2. T3: eliminar la esfera-cara (rostro-preceptor).
3. T2: p#estado = la voz de la app (panel activo + telemetría de modelos).
4. T5: Mando con hexágonos del WorldMap + sistema memoria/Lab/textos (profunda).
5. Cada panel lleva arriba su lista NO_DATA de funciones objetivo; mañana le damos forma.
Una sola estética: la anatomía de hoy es el canon; nada paralelo.

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA
