# Poda de referencias · ps del GitHub publico (7-nov, PR #195)

MANDATO DEL SOBERANO: unir ideas-nov con el ground truth de HOY y proponer la eliminacion de referencias antiguas que ya no describen la app, la web y el lab de hoy. Propose-only: el silicio propone el texto, el carbono firma. El perfil y los llms.txt son manos del Soberano (regla del AGENTS del perfil); aqui solo se propone.

## La frase nueva (decreto)
«0 peticiones externas» muere; vive «0 peticiones no declaradas»: toda peticion esta DECLARADA o no existe. Forma publica en ingles: zero undeclared requests.

## Medido: donde vive la frase vieja (lectura directa de main hoy)
- preceptoros-web/README.md, contrato de uso: «zero external requests on load».
- preceptoros-web/README.md, promesas: «a page load asks only for preceptoros.org» (la parte del api bajo paquete firmado ya esta bien dicha; solo cambia el NOMBRE del principio).
- preceptoros-web/llms.txt: «The WEB makes no external request on load».
- Perfil README: fila WEB «zero third-party requests on load»; tabla de estandares «Nothing leaves the node; zero external requests on load»; «what we ask» «zero external requests on load, no telemetry».
- App (PreceptorOS) README y llms.txt: la frase NO vive (0 hits, medido; el APP dice «never leaves the machine»).
- lab README: la frase NO vive (medido).

## Propuestas de poda (texto propuesto, FIRMO del Soberano)
1. WEB README contrato de uso: «zero external requests on load» -> «zero undeclared requests (every request is declared here or absent)».
2. WEB README promesas: mismo parrafo medido, el principio renombrado a «0 undeclared requests»; el api firmado sigue siendo el unico host declarado.
3. WEB llms.txt: -> «The WEB makes zero undeclared requests; the one declared host is the signed-packet API.»
4. Perfil fila WEB: -> «zero undeclared requests» + CURA del texto duplicado medido: «A guide that installs local AI step by step; the guide installs local AI step by step» (clausula pegada dos veces).
5. Perfil tabla de estandares: -> «Nothing leaves the node undeclared; zero undeclared requests».
6. Perfil «what we ask»: -> «zero undeclared requests, no telemetry».
7. WEB README «Install it» + «works with no network» (dos lugares): decreto del 7-nov, la PWA se retira como DESCARGA y se conserva la arquitectura nativa: -> «the site works offline (service worker); installing it as a download is retired by decree 2026-11-07».
8. Perfil fila APP: «The doctrine and the laboratory» es HOY falso (la doctrina vive en STUDY): -> «the application: the measured meter with its mini-html face (panels, Mundo, the game fullscreen on Android) and the local database».
9. Comentario de profundidad «the 3 principles and the 4 repos» en app, web y lab READMEs: -> «the 4 core repos and the 2 doors» (el perfil ya lo dice, medido; los tres quedaron atras).
10. APP README: AÑADIR la mini-html como la cara del medidor (hoy el README no la menciona; es lo primero que un modelo externo lee y por eso se quejan).

## Medido: ya curado (citar, no tocar)
- theGame como home: retirado; las menciones actuales son notas del retiro (corte D).
- «four-part ecosystem»: 0 hits; el perfil ya dice 4 core + 2 doors.
- 16 KiB como ley: solo vive como nota historica del fork compactado.
- «27 benchmark sessions» del perfil: ANCLADO (lab README declara 27 sesiones, 2026-07-18 a 2026-10-28, medido).

## NO_DATA con causa (abiertos, no bloquean la poda)
- «measured live on 2026-11-01» (perfil, OpenWorld): sin recibo del faro de esa fecha.
- Sello de sw.js tras el FIRMO de #196: la lectura API no devolvio el contenido; vara: grep armazon sw.js en el clon.

## Reglas
- Una pieza por PR; cada rebanada con recibo; el FIRMO cubre cabezas exactas.
- SCRUB intacto: nada de IPs, puertos ni rutas privadas en lo publico.
