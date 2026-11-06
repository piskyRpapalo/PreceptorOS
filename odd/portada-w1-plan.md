# THE ONE APP INTERFACE · portada (W1)

## Comisión

Una pieza, un PR. `interface/hexelion.html` es la `start_url` instalada y pasa a
ser la portada de la app única: chat atribuido, fila superior de zonas reales,
hexágono A2, composer A4 y recibo honesto. Anatomía inspirada por gentle-dot
(Alan Buscaglia, MIT; medida según `odd/tasks/portada-interfaz-unica.md`); no se
importan sus colores, marcas ni stack.

## Plan para aprobación

1. Conservar el órgano existente: conversación local por `/api/lab`, mente y
   harness H3; no inventar rutas, identidad ni resultados de modelo. Inspeccionar
   `interface/hexelion.html`, su JS/CSS, static route, PWA shell, SW y versionado.
2. Reorganizar la portada como chat primero, botones compactos arriba para mapa/
   face, lab, modelos y ajustes. Cada botón abre una ruta existente verificada;
   si no está cableada, mostrar `NO_DATA` con causa.
3. Presidir con el hexágono A2 y enlazar solo estados derivados de eventos
   observables. Cada estado tendrá texto; paleta por bandas Acho nombradas,
   nunca valores de color propios. Sin animaciones de entrada; controles de
   44px, foco visible 3px, regiones `aria-live`, reduced-motion y composer A4.
4. Llenar `docs/style-contract.md` Stage 2 solo tras fijar por FIRMA el SHA web
   exacto. Candidato indicado: `683d875274dc7cf9e75580569d2c0b135ac43187`.
   Medir cada slot desde ese árbol y citar ruta; slots no definidos quedan vacíos
   con `NO_DATA` y causa. Mantener mapping compatible del grupo adoptante.
5. Añadir pruebas para slots citados o NO_DATA, uso de bandas nombradas y a11y;
   verificar composer/recibo bajo 1.024 B. Alinear PWA route, SW y versionado
   según corresponda, sin build.
6. Correr `python3 -m unittest test_pwa` y `./bin/pruebas`; SCRUB del diff.
   La demo visual instalada y en dispositivo queda `NO_DATA` hasta los ojos del
   Soberano.

## Puertas y preguntas registradas

- **NO_DATA: pin firmado de Stage 2.** `683d8752…` se cita como candidato y
  GitHub muestra el commit landing de web#679/#680, pero el libro local no
  contiene una transcripción FIRMA de ese SHA exacto. No se escribirán valores
  en el contrato hasta que la FIRMA de esta pieza pinne esa cabeza exacta.
- **Rutas por zona:** confirmar mediante el inventario fuente qué rutas vivas
  corresponden a map/face, lab, models y settings; cualquier hueco visible dirá
  `NO_DATA` y causa.
- **Evidencia visual:** rendering instalado y dispositivo físico permanecen
  `NO_DATA` hasta la demostración del Soberano.

## Gates

- `./bin/pruebas`
- `python3 -m unittest test_pwa`
- tests nuevos: citas/NO_DATA de slots, color solo por banda Acho, mínimos de
  44px, foco visible de 3px, `aria-live`, reduced-motion y límite de recibo.
- SCRUB: loopback únicamente; sin credenciales, IPs no-loopback ni rutas privadas.

## Log

- 2026-11-06: plan presentado antes de cocinar; aprobación pendiente.
