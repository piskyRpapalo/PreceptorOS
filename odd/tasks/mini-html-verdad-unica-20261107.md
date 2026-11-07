# Mini HTML · verdad medida de la app (2026-11-07)

Esta nota corrige el inventario publicado en `mesa/mini-html-inventario-20261107`:
esa rama lee `main` antes de la anatomía y no describe la vista que se abrió en
la prueba local. No reemplaza cambios de Mistral ni afirma que propuestas abiertas
estén fusionadas.

## Procedencia comprobada hoy

- `main`: `8f2bc8371b359f6e2e4398bd6a443a97cd459358`.
- #186: draft abierto, `c30d04fb67e1a574d1a936dbc7c185cf79cae1bd`; añade chat primero,
  nueve botones de zona y la esfera pixel como control de plegado.
- #188: draft abierto, `2436f5b6c51f8ef1112322c371ee461a36b73d6d`, hijo de #186;
  alinea el inventario de nombres públicos.
- #189, #190 y #191 siguen drafts abiertos, respectivamente:
  `cc88db0baeb3cf8da41a9bf621ee79fb6b8847a6`,
  `fe3f843df44b29bd09dc4709e501246cc1054bd8`,
  `3253cf1c37e85e662cb409df1b2f1aa0d6277da4`.
- La vista local combinada de la prueba fue una composición aislada de #186–#191
  con ajustes locales de cache y anchura; no es `main` ni la rama del inventario.

Esta propuesta retira la esfera introducida por #186 y conserva el plegado con un
botón textual accesible. Su base es el head exacto de #188, no `main`; por eso
depende de que la cadena de anatomía y cura de nombres siga abierta.

## Carcasa observada en la propuesta

El mini HTML es `interface/app.html`; comportamiento y traducciones viven en
`interface/app.js`, estilos en `interface/app.css`, catálogo de zonas en
`interface/zonas.js`, transición de cambio en `interface/transicion.js` y audio
de cambio en `interface/sting.js`. La PWA declara recursos en
`bin/preceptoros-pwa`, cachea el armazón en `interface/sw.js` y calcula la huella
servida desde `version.py`.

Hay nueve paneles, en este orden: `panel-mando`, `panel-conversacion`,
`panel-gobierno`, `panel-cuaderno`, `panel-lab`, `panel-harness`, `panel-puerta`,
`panel-modelos`, `panel-ajustes`. Los botones llevan `data-panel` en `app.html` y
la lista congelada está en `zonas.js`.

La propuesta #186 inicia en Hablar y usa el chat local de Hexelion en #190. En
la prueba anterior el panel abrió y conservó su compositor; la consulta produjo
`NO_DATA: station_unavailable` porque el destino del túnel rechazó conexión.
Modelo de respuesta y cita de asistente: NO_DATA, no hubo respuesta del modelo.
Una búsqueda diagnóstica encontró un recuerdo local, pero no produjo cita en
respuesta.

## Cambio T3 en esta propuesta

Se quitan `span.rostro-preceptor`, su fondo pixel art y `#toggle-panel` del
cabecero. El botón de panel solo plegaba la navegación y el carril; no instala
ni cierra la app, así que también se retiran su comportamiento y estilo.
`transicion.js` sigue enlazado y su llamada desde `mostrar()` no se modifica.

Seguimiento de la petición del 2026-11-07: se elimina del panel Hablar el texto
de espera sobre teléfonos y el estado prematuro «Local orchestrator ready».
Tras una respuesta, el cabecero muestra el modelo que el servidor incluyó en
`respuesta.maquina.modelo`; si falta o falla la respuesta, muestra el estado
de ausencia allí. El modelo solo se anuncia a partir de ese campo medido.

El botón de instalar/añadir la PWA es otra función: la controlan el manifiesto y
`install.js`; esta cura no altera esa ruta. Tampoco hace que la cabeza pixel
permanezca visible fuera de la ventana.

## Medición de esta edición

Chromium local, ventana de app, cliente medido de 420 × 640: Hablar y el
compositor están visibles, sin esfera ni botón de plegado; `PreceptorTransicion`
está cargado. Hay nueve pestañas y la barra tiene desplazamiento horizontal:
ocho iconos aparecen en el primer marco; el noveno requiere desplazar la barra.
Captura local:
`/tmp/preceptoros-remove-face-20261107.png`.

La prueba de conexión hecha en la sesión anterior devolvió
`NO_DATA: station_unavailable`; el túnel informó rechazo de conexión en su
destino. Modelo y cita de respuesta: NO_DATA. Esta edición no repitió una
solicitud de chat, así que conexión y fuentes en este head siguen sin medir.
Despliegue: NO_DATA, no se ha desplegado.

Agent: Codex
