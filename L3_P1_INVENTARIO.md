# L3 · P1 · Inventario medido del puente

Inventario de solo lectura medido el 2026-10-16 desde loopback. No cambia la interfaz ni activa escrituras en las superficies fuente.

| Zona / superficie | Fuente medida | Estado y límite | Destino del puente |
|---|---|---|---|
| Mando / carga del nodo | Ojo `GET /api/arranque` en `127.0.0.1:8790` | HTTP 200; incluye `cargar_partida` y `rack_ahora`. El glosario se entrega por separado; respetar el orden de carga y la frescura del Ojo. | Fuente viva para presentar la carga del nodo si se integra en esta zona. |
| Harness / bucles | Nexo `GET /api/timers` en `127.0.0.1:8765` | La ruta existe y el sensor lee timers de usuario con `systemctl --user show`; cada fila declara última y próxima ejecución, estado y causa. Medición local: siete timers del encargo activos. | Fuente para la zona Harness; `/api/salud` solo enumera diez sensores y no trae las filas de timers. |
| Rack | `~/.preceptoros/laboratorio/rack.json` | Existe; esquema `hexelion.rack-instantanea/1`; `generado` medido y contrato con caducidad de 15 minutos. No contiene `timers`; contiene nodos, Ollama, nivel, registro y causas. | Foto local offline-first. No usarla como fuente de última/próxima pasada de los siete bucles. |
| Modelos | PreceptorOS `GET /api/lab` en `127.0.0.1:8740` | HTTP 200; entrega `modelos.mini`, `grande` y `eleccion`, con tags, disponibilidad/estado y causas. La UI debe mostrar lo declarado por el payload, sin calcular recuentos. | Fuente de la zona Modelos y de los datos de modelos que ya muestra Lab. |
| Hablar / canal del rack | PreceptorOS `POST /api/lab` | Ruta existente del servidor; la conversación del Lab responde por tubería local. El POST modifica el canal y queda fuera de esta pieza de inventario. | Fuente ya conectada para Hablar; no sustituir por Sala. |
| Puerta | PreceptorOS `GET /api/empieza-aqui?idioma=es` | HTTP 200; entrega bienvenida, límites, verbos, llave y bloque pegable derivados de `empieza_aqui.documento`. | Fuente de la zona Puerta; presentar el documento que ya sirve el endpoint. |
| Frontera | PreceptorOS `POST /api/frontera` | Ruta existente; la app presenta hallazgos del servidor y no decide ni cuenta. | Fuente ya conectada a la zona Frontera. |
| Cuaderno | PreceptorOS `GET /api/captura` y gestos consentir/retirar | La lectura lista turnos con recuento del servidor; cambios individuales tienen recibo. | Fuente ya conectada a la zona Cuaderno. |
| Nexo / salud | `GET /api/salud` en `127.0.0.1:8765` | HTTP 200; enumera diez sensores. No es el payload de lecturas del sensor timers; para ese dato usar `/api/timers`. | Fuente de salud del Nexo, no fuente directa para pintar los siete ciclos. |
| Sala | `GET /`, `/api/mensajes`, `/api/voces` en `127.0.0.1:8831` | Código local confirma chat grupal y rutas de lectura. No se consultó el hilo porque ninguna zona de L3 lo consume; no se hizo POST. | Sin zona asignada en L3; no importar mensajes a la app. |
| Ollama-puente | `deploy/soberano/ollama-puente.py`; proxy con lista blanca hacia `127.0.0.1:11434` | Código medido; solo permite las rutas declaradas, entre ellas `GET /api/tags` y `POST /api/chat`/`generate`. El inventario de modelos que consume la app ya viene de `/api/lab`; la UI no consulta ni enumera Ollama. | Dependencia interna del motor del Lab, no fuente directa de la zona Modelos. |

## Límites del inventario

- Las lecturas HTTP de Ojo, Nexo y PreceptorOS fueron GET a loopback; no se escribió en esas superficies.
- La instantánea del rack sirve a la cara offline-first, pero su esquema no incluye ejecuciones de timers. Harness debe leer el sensor existente del Nexo por un endpoint del servidor local, no abrir un socket desde el navegador.
- Sala no tiene una zona asignada en las cuatro piezas de L3. No se mezcla con el canal orquesta del Lab.
- El endpoint de modelos de PreceptorOS ya entrega las tres fichas con sus causas. La presentación debe reflejar esos campos; los nombres/tags no se duplican como inventario manual.

## Procedencia de código

- Ojo: `~/p0x/Alejandria/ojo/ojo.py:1279-1284` (`/api/arranque` y `rack_ahora`); `:979-1044` (carga y glosario).
- Nexo: `~/p0x/hexelion-nexo/servidor.py:69-76` (`/api/salud` y `/api/timers`); `~/p0x/hexelion-nexo/sensores/timers.py:57-96` (filas y causas).
- Rack: `~/p0x/hexelion/laboratorio/rack_instantanea.py:11-12,48-51,202-212,296-318` (archivo, caducidad, campos y validación).
- Puente Ollama: `~/p0x/deploy/soberano/ollama-puente.py:31-34` (lista blanca y destino loopback).
- App: `bin/preceptoros-pwa:264-291,439-462,621` (endpoints de puerta y Lab); `:976` (frontera); `:1108-1133` (captura); `lab.py:24-37` (contrato del Lab y tubería); `empieza_aqui.py:213` (documento de entrada).
- Sala: `~/p0x/hexelion/laboratorio/sala/sala.py:1-19,49` (alcance y dependencia loopback).
