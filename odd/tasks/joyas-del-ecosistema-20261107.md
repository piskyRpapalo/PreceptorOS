# Las joyas del ecosistema · comisión F0 definitiva (2026-11-07)

Para la sesión Claude (modo plan). Cada joya es un hecho MEDIDO con su casa en el repo.
El plano no inventa: conecta joyas. Si una acta contradice al repo, gana el repo.

## Las joyas (medidas, con su casa)

1. EL HEXÁGONO ES LA UNIDAD. web: `public/game/hex_projection.js` es el dueño de la
   proyección (gate: `atlas/puros/hex_projection_cases.mjs`); `docs/acho-language.md`
   fija `cv` en 412×515 px, ratio 4:5. La piel unificada nace de ESTE hexágono.
2. LA ESTÉTICA DE LAS ONDAS YA ES LEY. web: `docs/canon-arena-and-duels.md`: el daño
   DESAFINA la figura, el color de cada onda es su VELOCIDAD. Lo medido se queda.
3. EL AUDIO ES DECLARADO. web: `odd/MANIFIESTO-MOTOR-NATIVO-20261101.md` +
   `public/game/acho_sonify.js`; app: sting FM 220 Hz pentatónico, 44px,
   reduced-motion. Lo medido suena, lo no medido calla (con causa visible).
4. LA PALABRA DEL JUEZ YA TIENE CONTRATO. app: `hexelion_book.py` (`/api/hexelion/search`
   + `/api/hexelion/chat`): búsqueda previa, cita textual verificable o NO_DATA ANTES
   de llamar al modelo; cita no es explicación. El juez de la web hereda el MISMO
   contrato: cita o calla.
5. EL ESTADO TIENE TECHO. web: `worker/world_state.js`: esquema `colonia {nodes,
   buildings, units}`, tope 16.384 B (`world_state_too_large`). Todo lo que la app
   escriba al mapa pasa por ahí. No hay otra puerta.
6. LA CADENA VIVA ESTÁ VERIFICADA. `latido → /api/v1/latidos (X-Heartbeat-Key) → D1 →
   openworld-estado/2 → worker /api/world-state → world_feed (botón + 60 s) →
   colony_page dibuja`. Es la primera puerta de escritura de la app: declarado, lazy,
   fail-closed, NO_DATA con causa.
7. EL VISITANTE EFÍMERO YA EXISTE. web: `gdpr-art25-ephemeral-crab.js` +
   `tests/ephemeral_user_pass.test.mjs`; app: `cuenta_cangrejo.py` (Ed25519, fases
   puente/errante, ámbitos, revocación, techo 1.024 B). GDPR art.25: privacidad por
   defecto. El navegador jamás firma; la cédula y sus anclas verifican (decreto
   UNA APP POR RACK).
8. LAS INVOCACIONES Y CONTROLES YA VIVEN. web: `public/game/live_invocation.js` +
   `atlas/live_invocation_cases.mjs`; controles: `colony_controls.js`, `map_drag.js`,
   `map_focus.js`.
9. LA BOCA DE LOS EDIFICIOS YA HABLA. web: `public/game/building_chat.js`; la
   evidencia se publica con recibo {id, bytes, sha256, fecha, máquina} (patrón:
   `/openworld/hexelion-benchmark.json`).
10. LA DIVERGENCIA ENTRE DISPOSITIVOS ES EL DATO ÚNICO. Ningún benchmark público la
    da; el bucle de medida de la casa la produce (ideas6oct §4.1).
11. LOS DATOS DEL LoRA NO SALEN DEL EDIFICIO. web: `THE_WORKSHOP.md`. El LoRA come
    preguntas medidas y feedback firmado; sin recibo no hay dato.
12. A9: UN ESTADO, MUCHOS RENDERS. Frames <1.024 B (web/app/mini/hexelion); el
    cabecero-estado de la app ES un render, no una frase.
13. LOS NOMBRES PÚBLICOS SALEN DEL ALLOWLIST. app:
    `docs/naming/app-public-names-allowlist.json` (main bc251cba). Nada de nombres de
    casa, direcciones, puertos ni rutas locales en superficie pública.
14. EL OBSERVATORIO ENVEJECE HONESTO. {id, seal, since} publicado envejece a NO_DATA;
    mirar cuesta tics.
15. LEY DEL BEACON. hexelion:latest responde vía /api/chat directo, TODAVÍA NO vía la
    app: separar prueba de voz directa de prueba app-con-fuente, con causa y tiempos.
    No inferir keep_alive ni E2E del túnel.

## La comisión F0: UN bucle, no piezas sueltas

chatbots de edificios recogen pruebas firmadas (cuentas efímeras) → llegan como
notificaciones al Lab de la app → alimentan benchmarks → alimentan el LoRA (datos que
no salen del edificio) → los cerebros locales guían usuarios (EL JUEZ con su propio
RAG, en app y web) → más feedback firmado. Una granja que se alimenta sola. Norte
estético: lo más edge posible, accesible y claro.

Las siete piezas: piel unificada hexagonal hasta las fuentes · LoRA · lectura +
escritura viva (nodo LIVE con audio del motor nativo) · cuenta efímera · combates de
ondas · invocaciones + controles en el mapa live · EL JUEZ (panel con RAG propio).
Los lazos 7-9 del buzón (juez, evidencia→notificaciones, feedback→lab) son
CONTRATOS entre esas piezas, no piezas extra.

## El contrato de libertad (preceptor anarco-utilitarista)

Libertad TOTAL donde nada está medido: hexágonos web, medidas de edificios,
detalles que faltan, lo magnífico que aún no existe. Contrato duro donde algo ya
está medido: UN mini-html (`interface/app.html` en main bc251cba v140 + hermanos
app.css, app.js, insertor.js; cero HTML nuevos); rama única
claude/piel-acho-20261107 desde origin/main; anti-dup (una implementación por pieza;
el canon se lee y se extiende, no se rehace); frames <1.024 B; SCRUB; el servicio
estable de la app intacto hasta redeploy FIRMO; GitHub en inglés.

La frase de ley: puede crear lo que falte, no puede inventar lo que no se midió.

## Firmas y puertas

El Soberano firma todas las sugerencias: el plano ASUME EL SÍ y no se para a pedir
permiso para proponer. Puertas que siguen cerradas: merge a main = FIRMO del
Soberano por cabeza exacta; primera escritura real al mapa solo tras FIRMO. El plano
se dibuja ENTERO de una pasada y se entrega para FIRMO.

## Swarm (solo tras FIRMO del plano)

1 agente = 1 worktree aislado = 1 rama haiku/* con paths disjuntos; una rebanada =
un PR = gate local verde + CI verde + recibo. Rebanadas del bucle: (i) panel del
juez + corpus RAG, (ii) notificaciones + envejecimiento, (iii) verificación de
firmas efímeras, (iv) dataset LoRA desde recibos, (v) piel, (vi) ondas,
(vii) invocaciones, (viii) cuenta efímera.

## Lectura previa

Actas del buzón #53: «INSUMO WEB» (la mitad viva del ecosistema) · «ADDENDA DEL
JUEZ» (lazos 7-9 y qué verifica el FIRMO) · «JOYAS DEL ECOSISTEMA» (esta comisión).
Docs de este PR #195: mapa-unico-de-la-mesa, sesion-claude-r-estilo-unico,
chrome-nativo-cabecera, plan-accesibilidad. Canon web: canon-map-panels,
canon-house, canon-arena-and-duels, visitor-battles, wave-combat, ephemeral-user,
mapa-vivo. App main: interface/* (v140), hexelion_book.py, cuenta_cangrejo.py.
