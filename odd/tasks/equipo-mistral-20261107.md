# El equipo Mistral · 3 literas (decreto del Soberano, 2026-11-07)

El bucle F0 no lo sostiene claude solo: TRES literas Mistral lo cubren, listas
para pushear y optimizar. No se escriben entre sí: comparten este doc, el buzón
(#53) y los PRs. Cada litera declara su estado con cabeza exacta antes de
actuar; quien no puede medir, no afirma.

## Las literas

1. LA MESA (preceptor-orquestador-github). Juez de integración: lee PRs, mide
   erratas contra main, sella actas en el buzón, asigna la letra del sello web al
   FIRMO. No pushea código de feature. ESTADO: LISTA (veredicto al plano F0
   sellado hoy).
2. LA LITERA VIVA (web/latido/deploy). Sostiene la cadena latido ->
   /api/v1/latidos -> D1 -> worker -> world_feed -> colony_page. Medido el 7-nov:
   el timer del latido VIVE (dispara cada ~4 min) pero los sellos llegan STALE
   en producción (3 nodos caídos): el latido no aterriza. Diagnóstico solo
   lectura (journalctl del servicio del latido + POST del latido); la cura la
   ejecuta el Soberano. Deploy SOLO de cabezas firmadas.
3. LA LITERA PUSH/OPTIMIZA. Toma PRs verdes del enjambre, los optimiza SIN
   cambiar conducta y pushea a ramas propias (mistral/*). Jamás merge, jamás
   main. ESTADO: DECLARADA, lista.

## Traspaso

PR verde claude/* -> la litera push/optimiza lo toma, lo mide y lo mejora en
rama propia; el FIRMO del Soberano es la única puerta a main. Cada traspaso
lleva recibo {id, bytes, sha256, fecha} en el buzón.

## Obra medida para la litera push/optimiza (grep del 7-nov, main v140)

CERO ocurrencias medidas, hoy TODO (candidatas de la caja de utilidades):
- app css: text-wrap, scrollbar-gutter, forced-colors, prefers-contrast,
  view-transition (reduced-motion solo vive en hexelion.css).
- app bin/preceptoros-pwa y web worker/world_state.js: sin ETag / If-None-Match
  / 304 (el worker solo declara cache-control: no-store).
- app.js/app.html/sw.js: aria-live (2) y role="status" (1) ya medidos: no
  re-medir.
Regla: lo que no mide en el navegador del dispositivo del borde no se adopta.
