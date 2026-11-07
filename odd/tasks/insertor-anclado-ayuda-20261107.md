# Insertor anclado y ayuda efímera · 2026-11-07

Estado: proposal, funcionalidad medida por pruebas locales. Base: `e747df6ee64c34a8fa65d1080042e06c1eaffc1f` (`main`, tras #196). Alcance: esqueleto funcional; no introduce piel Acho.

## Contrato

- El `h1` aparece una vez dentro del chrome nativo de la app. La barra existente de nueve pestañas queda en ese chrome, antes del carril. El nombre de documento/browser tab no se cambia.
- Los nueve controles de panel mantienen sus ids, roles y tamaño táctil mínimo de 44 px. El cambio de panel conserva `transicion.js`, `sting.js` y `prefers-reduced-motion` existentes.
- Un solo compositor vive después del carril, siempre visible aunque cambie el panel. Su texto no pertenece a ningún panel y no desaparece al navegar.
- Gramática de comando: `@<id-de-zona> [pregunta]`, donde la etiqueta pertenece al conjunto congelado en `zonas.js`; `@ayuda [nota]` es el único carril local efímero. No hay interpretación libre de tags.
- Una etiqueta de zona navega a ese panel. Con pregunta, el navegador envía la pregunta y solo el id enumerado del panel al mismo origen. El servidor mantiene el texto original en el canal y la búsqueda de memoria; añade una descripción fija del panel al prompt como contexto de interfaz, nunca como evidencia ni autoridad.
- Sin pregunta, `@<zona>` enseña los títulos h2/h3 de ese panel en el carril de ayuda. `@ayuda` enseña esa base del panel activo y puede mantener una nota local. La nota se renderiza como texto, no se envía al chat, no se escribe en memoria y se borra al cerrar o con Escape.
- Tag mal formado o fuera del catálogo falla cerrado antes de cualquier POST. La base local lee solo títulos h2/h3, hasta ocho; nunca valores de campos ni el hilo.

## Mapa funcional

- `interface/app.html`: header, nav `.pestanas`, paneles, `#ayuda-efimera` y `#form-chat` global.
- `interface/insertor.js`: parser cerrado y extractor acotado de títulos.
- `interface/app.js`: cambio de panel, carril de ayuda y chat global; mantiene la transición y el sting existentes.
- `hexelion_book.py`: allowlist de contexto fijo por id de panel.
- `bin/preceptoros-pwa`: `POST /api/hexelion/chat` acepta texto y, opcionalmente, id de panel; el id desconocido se rechaza.

## Medidas y pruebas

- Inspección de `interface/app.css`: botones de `.pestanas` ya medían 44×44 px; no se cambian sus medidas. `mostrar()` ya invoca sting tras anunciar la zona y `transicion.js` ya omite animación con movimiento reducido. Se conserva ese comportamiento.
- `./bin/pruebas` y CI deben medir el gate completo sobre la cabeza final antes de abrir el PR.
- Sabotajes: tag desconocido/mal formado sin POST; tag válido cambia el destino; `@ayuda` no usa canal ni memoria; nota efímera se escapa como texto y se elimina al cerrar; panel de petición no declarado se rechaza; el contexto fijo no se acepta como fuente.

## Log

- 2026-11-07: pieza propuesta desde main `e747df6`; base de navegación y sting leída antes de editar. El camino real a Hexelion permanece mismo origen y solo recibe los campos del contrato.
