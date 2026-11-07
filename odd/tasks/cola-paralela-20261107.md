# Cola funcional paralela · 2026-11-07

Estado: propuesta documental. Base medida: `e747df6ee64c34a8fa65d1080042e06c1eaffc1f` (`main`, tras el merge de #196). No modifica la ventana estable ni el servicio local. Reanudación ordenada: 2026-11-11.

## Decretos que rigen la cola

- El norte de Android fullscreen es el juego: la app abre Mundo/OpenWorld como ventana del juego.
- Se retira la PWA como descarga. Se conserva su arquitectura nativa: tronco mini-HTML y service worker.
- La doctrina es **«0 peticiones no declaradas»**: cada petición externa debe tener destino, iniciador, momento y propósito declarados. No equivale a prohibir peticiones externas.
- Función solamente. Chrome superior, composición visual Acho y sting pertenecen al carril Claude.
- Trabajo propuesto en piezas separadas, una por PR, desde `main` vigente. No alterar #196 ni heredar su rama.

## Cola y puertas de aceptación

### A · Doctrina de peticiones declaradas

Medición en esta base: `rg` no encontró `0 peticiones externas` ni `0 peticiones no declaradas` en README.md, llms.txt, docs/ u odd/. Declarar la frase nueva en los documentos que exponen la doctrina del proyecto (README.md, llms.txt y el documento normativo pertinente de docs/); explicar que las llamadas externas requieren declaración explícita. No añadir una promesa de cero tráfico. Revisar enlaces y búsquedas para evitar que la formulación vieja vuelva como doctrina activa. Sin cambios de interfaz; subir el sello del service worker solo si cambia un recurso que este precachea.

### B · Insertor anclado

Documento de contrato requerido: `odd/tasks/insertor-anclado-ayuda-20261107.md`. Implementar el insertor funcional anclado abajo, con:

- ruteo `@tag` medible y cerrado: tags reconocidos, destinos, fallo para tags desconocidos y regla de no envío;
- conjunto base de acciones/datos declarado por panel, sin inferir permisos;
- carril de sesión efímera en cliente, sin cuenta y sin persistir identidad; salida y limpieza verificables;
- NO_DATA con causa ante destinos o capacidades ausentes.

Criterio: pruebas demuestran ruteo correcto por panel/tag, rechazo de tag inválido, aislamiento entre paneles y borrado del carril efímero.

### C · Mini-orquestador local continuo

El blob del modelo debe vivir localmente en el aparato. Estado inicial honesto: `NO_DATA`, causa `su blob no está en este aparato`; no simular respuestas. Medir antes la ruta de carga y disponibilidad. Aplicar el patrón de chunks de la web y una decisión estilo Laya con contrato explícito; entregar información fresca a Hexelion mediante un agente continuo solo dentro de los límites locales declarados. No enviar prompts, memoria o estado a un destino no declarado.

Criterio: prueba con blob ausente devuelve NO_DATA con esa causa; blob presente permite una respuesta medida con origen, frescura, modelo y latencia; las pruebas adversariales bloquean carga remota no declarada, datos obsoletos presentados como frescos y salida simulada.

### D · Lab V2 funcional · LAB-1 a LAB-4

Tomar como contrato funcional la comisión Lab V2 (§62): señales medidas solamente, experimentos nombrados por el Soberano, telemetría de agentes con estado y edad visibles, reporte de novedades de hasta 100 caracteres derivado de recibos/commits/CI, y enlaces explícitos Lab↔Hablar↔Modelos↔Web↔Cuaderno. Datos ausentes o no verificables se muestran como NO_DATA con causa.

Criterio: sabotajes de fuente ausente/mentirosa, reporte mayor a 100 caracteres y ventana que no cierra son detectados; ninguna novedad se infiere de una señal sin fuente.

## Estado y orden

- #196: juzgado PASS por la Mesa en `fbaf1295b500310017438f01e8502e6d86370b4e`, CI 10/10 medido; luego fusionado en `main` como `e747df6ee64c34a8fa65d1080042e06c1eaffc1f`. Esta cola parte de ese main; el PR #196 no se modifica.
- Aún no implementado aquí: A, B, C y D. Esta pieza solo preserva los decretos, medidas y criterios para el relevo del 11-nov.
- Reanudar midiendo `origin/main` del día y el estado de los servicios antes de cada pieza. Publicar PR draft por pieza. No declarar gate verde hasta medirlo sobre el SHA final.

## Registro

- 2026-11-07: `origin/main` medido en `e747df6ee64c34a8fa65d1080042e06c1eaffc1f`; #196 ya estaba MERGED antes de crear esta rama. Inventario de frase ejecutado sobre README.md, llms.txt, docs/ y odd/.
