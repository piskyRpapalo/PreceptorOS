# PORTADA↔HEXELION (W2 link)

## Comisión

Una pieza = un PR. Conectar el chat de `interface/hexelion.html` con Hexelion por
el servidor existente (`bin/preceptoros-pwa`), como proxy local. El navegador
solo conoce el endpoint propio de la app. La estación/modelo `hexelion:latest`
se configura en el servidor por variable de entorno; falta de configuración es
`NO_DATA` con causa. Todas las salidas de red del proxy quedan limitadas a
loopback. Solicitud a la estación fija `think: false`.

## Plan para aprobación

1. Medir el contrato actual de `/api/lab`, el append-only del hilo y la W1 UI;
   revisar modelos/harness y cliente HTTP ya disponibles en el repo. Mantener
   fallback honesto y no tocar registros históricos.
2. Rutas medidas (bin/preceptoros-pwa): `/api/orquestador` es un router de
   verbos tipados para edificio/RAG, no un generador de chat libre;
   `/api/hexelion/search` solo busca memoria; `/api/hexelion/decision` devuelve
   NO_DATA porque no tiene adaptador; `/api/harness` solo lee el sensor loopback.
   `/api/lab` sí genera, pero en la tubería mini y atribuye respuestas a
   `orquestador`, por lo que no representa la estación. Estos contratos no bastan
   para hablar con Hexelion sin confundir voz/modelo. Añadir `/api/hexelion/chat`
   en `bin/preceptoros-pwa`, proxy del servidor al endpoint local configurado.
   Reutiliza el hilo `orquesta` append-only y las voces ya existentes
   `soberano` y `hexelion`. Validar origen loopback literal, modelo fijo
   `hexelion:latest`, límites y timeouts. El navegador nunca recibe URL de estación.
3. Antes de generar, sondear `/api/tags` con timeout estricto de 3 s; exigir
   `hexelion:latest`. Después enviar a `/api/generate` con `think: false` y
   `stream: false`, sin redirects ni retries; la generación lleva timeout acotado.
   Errores de conexión, rechazo, timeout, JSON/modelo ausente son `NO_DATA` con
   causa segura, sin exponer dirección/credencial.
4. Mantener hilo atribuido append-only. Registrar persona y respuesta solo por
   las rutas de canal ya existentes, preservando voces reales. Stop en el cliente
   cancela solo la espera; dejar claro que el servidor pudo completar/asentar.
5. Cada respuesta muestra recibo compacto `<1.024 B`: modelo, duración total
   de generación devuelta por la estación (`total_duration`) y reloj total del
   navegador medido aparte como en W1; causa. Si falta la medición, `NO_DATA` con
   causa, nunca cero inventado. No añadir campos
   al frame canónico del hilo.
6. Añadir pruebas para config ausente, solo loopback, `think:false`, proxy sin
   filtrar dirección al cliente, respuesta medida/error honesto, Stop y append-only.
   Mocks de transporte aislados; no son prueba de estación viva.
7. Correr `python3 -m unittest test_pwa`, `./bin/pruebas`, `node --check` y
   `git diff --check`; SCRUB estricto del diff. Estación viva queda `NO_DATA`
   hasta un sondeo corto autorizado al endpoint configurado con `curl -s -m 3`,
   sin imprimir URL privada, respuesta sensible ni secreto. No activar servicios.

## Riesgos/decisiones registradas

- Estación, host y puerto exactos: NO_DATA en el repo público; se acepta solo
  configuración local por entorno, sin valor por defecto ni valor en commit.
- Máquina/harness que lo ejecute y timeout de servidor: medir durante explore;
  respetar el límite de sondeo de 3 s y no permitir espera ilimitada.
- Disponibilidad real de `hexelion:latest`: NO_DATA hasta sondeo seguro con
  resultado reducido a status, duración y causa; sin almacenar contenido.
- Cualquier host no-loopback, credencial, /home path, tailnet address o registro
  nuevo de voz está fuera de la pieza.

## Gates

- `python3 -m unittest test_pwa`
- `./bin/pruebas`
- tests nuevos según los contratos de arriba
- SCRUB: loopback solamente; ningún secreto ni dirección privada en diff/log/PR
- Draft PR HITL a `main`; parar después de abrirlo. Nunca merge, firmar ni push
  a `main`.

## Log

- 2026-11-06: tarjeta y plan redactados antes de implementar.
- 2026-11-06: medición de rutas: se justifica `/api/hexelion/chat`; los endpoints
  existentes tienen contratos incompatibles o son lectura/estado. Rama basada en
  `origin/main` ea551cf. Aprobación recibida para cocinar.
