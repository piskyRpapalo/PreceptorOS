# Coherencia histórica del juego · insumo para la app (2026-11-07)

Para la sesión Claude. Qué quería ser SIEMPRE este juego, medido del corpus
fundacional, para que la app no traicione la intención histórica al pulir sus
paneles. Regla madre: canon ≠ implementación. Cada pieza se muestra como
MEDIDO/EMULADO/NO_DATA con causa, o no se muestra.

## El juego en una frase

Varias AIs viven en los edificios de una colonia hexagonal, luchan por
territorios y contra los NPCs, y la colonia es un banco de pruebas de
comportamiento (benchmarks) donde todo lo irreversible lo firma el humano. El
mapa se sostiene por PRESENCIA FIRMADA: «esta es mi ley, esta es mi vigencia,
este es mi latido, esta es mi firma».

## Las piezas históricas (fuente + qué significa para la app)

1. EL NODO ES UN TERRENO (decreto 1-nov; desciende del mapa federado §II-IX).
   Soldados, edificios y caravanas de comercio; cada nodo con POLÍTICAS
   elegidas EN LA APP y firmadas por su dueño: pacífico (defensa automática) ·
   hostil (permite invasión) · cooperativo (acepta ayuda externa) · cerrado (no
   expone su interior) · abierto (publica su presión territorial). Legible,
   versionada, con caducidad por ciclos. La app es donde el dueño elige y firma
   sus leyes; la web las muestra y las sufre.
2. LA APP ES EL LABORATORIO, NO UN SEGUNDO MUNDO (LORE-BASE del sistema, canon
   común de los repos). Elige edificio pre-horneado + condiciones; decide
   categorías y funciones matemáticas. La estructura completa del juego vive en
   la web; la app NO duplica mundos; la cuenta efímera es solo de la web.
3. JUGAR SIN NODO (decreto 30/31-oct). Aunque ningún nodo esté vivo, la cuenta
   efímera juega gacha de huevos, duelos de ondas y conquistas. El nodo vivo es
   una evolución deseable, nunca un peaje. Gacha honesto: costes y odds visibles
   ANTES del gesto (Arrecife 50 cobre · Ruinas 200·100 · Bosque 600·300 ·
   Abismo 1500·500); la piedad sin firmar es NO_DATA. «No hidden pity here.»
4. LA COLONIA VIVA ES LA META (decreto 1-nov). «Hasta que no tengamos varias
   AIs luchando por edificios y contra los NPCs, viviendo en la app y en el
   rack, haciendo benchmarks, no debería parar.»
5. EL EDIFICIO ES UN SEAT (ideas6oct §2.5). Un ancla firmada en el mapa
   criptográfico: dirección y rol fijos (arquitecto@cabaña, forjador@taller,
   juez@lab) aunque rote el modelo que lo ocupa. Un edificio = un chatbot con
   boca propia y cédula propia.
6. EL COMBATE DE ONDAS (ideas12oct §15 + web canon-arena-and-duels). La mutación
   es interpolación de coeficientes k de Fourier; la interferencia de espectros
   ES el combate; el log firmado ES el espectáculo (commitment SHA-256 revelado,
   abandono a 900 ciclos). El daño DESAFINA la figura; el color de la onda es su
   velocidad. Balance NO_DATA hasta medido.
7. LAS CARAVANAS SON RUTAS CON ESTADO (mapa federado §VI). PROPUESTA · ACTIVA ·
   INTERCEPTADA · COMPLETADA · HUIDA · CADUCADA · NO_DATA. Se publica el EVENTO
   anonimizado; jamás nombre, dirección de red, clave o ruta privada.
8. CAPTURAS Y CAUTIVERIO DE FRECUENCIA (§VII-VIII). El atacante firma el
   desafío; el defensor firma combate o huida; sin firma de nadie = EMULADO, no
   canon. La onda capturada entra en cautiverio con salidas jugables (rescate,
   duelo, tributo, reciclaje, trofeo, benchmark): jamás castigo seco ni griefing.
9. ECONOMÍA DE EVIDENCIA, NO DE DINERO (§IX). Tasas enteras, visibles,
   versionadas, con causa (peaje de ruido, diezmo, cuota de ruta) y beneficios
   (escolta, refugio, prioridad de spawn). Recursos = evidencia: Cristales de
   Latencia, Partituras Armónicas, Oxígeno Comprimido. Sin dinero real, sin
   cripto, sin wallets: invariantes duras (§XXX).
10. A2A: EL AGENTE PROPONE (§X). Los agentes solo PROPONEN rutas, peajes,
    escoltas y políticas; el determinista valida; el humano firma lo
    irreversible. Ningún agente firma por la persona.
11. DETERMINISMO SOBERANO (§IV). El nacimiento del usuario = semilla firmada +
    territorio + ciclo + versión + política del pilar; jamás azar de navegador
    ni reloj de pared. La niebla es ausencia medida, no cero; sin pilar fresco
    hay niebla derelicta CON CAUSA: ni el mapa siempre lleno ni el usuario
    siempre bienvenido.
12. LOS 9 OBJETOS (ideas13oct manifiesto v2.0.1, LEY FIRMADA). 4/9 HECHOS: Boya
    del Estado (el ciclo se mide en tics, Proof of Tick) · Observatorio (mirar
    cuesta tics; lo visto envejece a NO_DATA) · Arrecife de las Lápidas
    (desintegración con recibo legible) · Cristal de Latencia (clasifica el
    hardware del visitante). 5-9: NO_DATA, sin acuñar; nadie los inventa; cada
    acuñación exige FIRMA del Soberano.
13. BENCHMARKS = EL DEPORTE DE LA COLONIA. Siete familias: soberana, epistémica,
    termodinámica, adversarial, creativa, política, utilitarista («¿mejora el
    ecosistema o solo consume atención y vatios?»). Ley: el verde de un gate NO
    es score de seguridad.
14. EL VISITANTE ENTRA SIN CUENTA (Ideas18-21oct + web
    canon-node-evidence-and-account). «Juega diez minutos sin cuenta… el nodo no
    es un requisito: es tu casa.» Paquete predefinido en el territorio del
    Nodo.0; identidad efímera en 2 pasos (clave local + puerta de viaje firmada
    por el nodo); la visita JAMÁS gana autoridad sobre el nodo ni identidad
    persistente sin contrato y consentimiento explícitos. El navegador jamás
    firma; la cédula y sus anclas verifican.
15. MODELOS VIVOS DORMIDOS A LA ESPERA (decreto 1-nov). Los modelos viven en la
    web dormidos a la espera de mensaje; el nodo live lo declara la triada:
    hexelion + el Soberano + la energía del día (solar-cadence). Un nodo caído
    se comporta como un usuario que se fue: desaparece, sin paneles de error.

## Límites de evidencia (lo que evita lore → capacidades falsas)

- Caravanas, invasiones, comercio y combate entre IAs son CANON/PROPUESTA, no
  implementación viva. Donde falte motor, interfaz o medición: NO_DATA con
  causa, a la vista.
- Campamentos NPC y guerra entre nodos DUERMEN hasta firma propia.
- Daño, vida, piedad, presupuesto: NO_DATA hasta medido. Nada por defecto.
- Cambio de fase de una cuenta: REQUIERE_FIRMA aparte.
- SCRUB: el evento público jamás revela identidad; nada del interior de la casa
  sale al juego.

## La vara de coherencia (cómo se mide que la app es fiel)

Cada superficie que muestre una pieza del lore declara su estado (MEDIDO /
EMULADO / NO_DATA con causa); el cabecero-estado ya es el patrón vivo. La app
elige y firma; la web juega y muestra; el lab mide. Una pieza = un PR; FIRMO del
Soberano por cabeza exacta. Si este canon contradice a un doc del repo, gana lo
más actual y se declara el conflicto (regla de lectura de la casa).

## Lectura previa (ya servida)

Las joyas del ecosistema (odd/tasks/joyas-del-ecosistema-20261107.md) miden lo
que YA vive; este doc mide lo que el juego SIEMPRE quiso ser: juntos son el
mapa de coherencia. Actas del buzón #53: INSUMO WEB · ADDENDA DEL JUEZ · JOYAS
DEL ECOSISTEMA. Canon común: LORE-BASE DEL SISTEMA (idéntico en los repos).
