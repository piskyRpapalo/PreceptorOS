// Service worker · Solo cachea el armazón, jamás una respuesta de la memoria.
//
// Cachear /api/* haría que la interfaz enseñara recuerdos viejos como si
// fueran los de ahora, y que un contador de la frontera sobreviviera al texto
// que lo produjo. Un número correcto en el momento equivocado es un número
// falso, así que aquí solo entra lo que no cambia.
// La version del nombre no es decoracion. Se cachea "/" por el armazon, y "/"
// cambio de app.html a dashboard.html: sin subir esta version, el navegador
// siguio sirviendo la cara vieja aunque el servidor ya devolvia la nueva.
// Medido en un telefono el 2026-08-22 -- se veia la interfaz anterior y el
// servidor decia la verdad. **Al tocar cualquier fichero de esta lista, se
// sube el numero.** Es lo unico que hace que una actualizacion llegue.
// v46 (2026-09-04): las cuatro capas, el tema del sistema y el ancla del
// teclado tocaron dashboard.html, .css y .js -- los tres estan en la lista de
// abajo. Se subio despues de que el telefono lo demostrara: la prueba del
// Doogee devolvio la cara vieja --campo con el rotulo retirado y el hueco de
// conversacion sin la linea de bienvenida-- mientras el servidor ya servia la
// nueva. Es exactamente el fallo que el parrafo de arriba describe, cometido
// por quien lo acababa de leer. La marca `?v=` de las hojas no lo cubre: el
// que se sirve de la cache es `/dashboard.html`, que no lleva marca, y es el
// que arrastra a los demas.
// v94 (2026-10-03): la consola soberana toca dashboard.html y trae dos piezas
// nuevas, consola.css y consola.js, que entran en la lista con su `?v=`.
// v95 (2026-10-04): la consola suma la sugerencia del tier 1 y los canales;
// consola.js y consola.css suben a ?v=2.
// v96 (2026-10-04): niebla del primer arranque y el cuerpo del nodo;
// consola.js y consola.css suben a ?v=3.
// v99 (2026-10-16): la app conserva sus zonas en una pestaña y precachea el catálogo.
// v100 (2026-10-16): la puerta y el documento servido requieren caché renovada.
// v101 (2026-10-16): elimina el identificador privado anterior y renueva el caché.
// v102 (2026-10-16): la pestaña única precachea su proyector de transición.
// v104: local radio sting follows the accessible zone announcement.
// v105: the node credential export adds an explicit, signature-checked route.
// v106: signed creation import is explicit and local to the rack.
// v107 (2026-10-24): "/" pasa a ser la cara nueva (chat + joystick, encargo Norte 5);
// entran sus tres pieles, su hoja, su guion y las nueve piezas de la lengua.
// v108 (2026-10-24): la cara camina el mapa vivo: entra face_world.js y
// cambian face.js, face.css y las tres pieles (tres distribuciones).
// v109 (2026-10-24): la terminal zombie trae su vagabundo y Atlantis las
// criaturas canon del Codex: entra bubble_bestiary.js.
// v110 (2026-10-24): una sola ventana fija sobre el mapa isométrico vivo:
// entran face_paint.js y cinco piezas del mapa de la web (proyección, cámara,
// zoom, niebla y ciudad).
// v111 (2026-10-24): el panel con categorías y el gusano canon, y el combate
// de ondas (combate_ticks, escuadrón, wave_render) en la cara.
// v112 (2026-10-24): fondo marino canon bajo el mapa y el cangrejo canon que
// crece y cambia de color: entran escena, sea-floor y las dos piezas del cangrejo.
// v113 (2026-10-24): el joystick y los iconos del mapa entran en el mapa, el
// panel sube bajo el mapa y el busto sale del mapa: entra face_hud.js.
// v114 (2026-10-24): altavoz y radio que leen la pantalla, la frase guía pasa a
// la voz, y el soldado espacial de la terminal zombie: entra face_hero.js.
// v115 (2026-10-24): vistas por iconos (mapa, batalla, perfil, info) con el
// chat siempre abajo; Army canon, gacha firmada y revelación: entran face_army,
// face_canon.css y seis piezas canon (icons, db, panel, ficha, revela, auth).
// v116 (2026-10-25): tutorial guiado (Neutral obligatorio, elección de nodo),
// huevos por ciclos, taller, batalla contra patrullas: entran face_eggs,
// face_workshop, face_tutorial, face_views.css y la pieza canon taller.js.
// v118 (2026-10-25): the pending node-registration flow adds its script.
// v120: local node identity and the explicit Aduana building declaration.
// v132 (2026-11-06): the Hexelion chat renders verified memory citations.
// v133 (2026-11-06): rutas profundas de la pestana unica y puerta canonica
// /app; app.js sube a ?v=7 y el armazon precachea la puerta /app.
// v134 (2026-11-07): chat first, icon panels, and the app's pixel-face toggle.
// v135 (2026-11-07): remove pixel-face control from the app header.
// v136 (2026-11-07): remove panel collapse control and chat helper copy;
// report the measured reply model in the header.
// v137 (2026-11-07): anchored conversation composer and verified Hexelion chat.
// v138 (2026-11-07): lazy OpenWorld panel and accessible model catalogue.
// v139 (2026-11-07): global composer, panel-tag routing, temporary local help.
// v140 (2026-11-07): puerta al Lab local, consultada al abrir su panel.
// v141 (2026-11-07): retire legacy face precache; root and install open the app trunk.
// v142 (2026-11-07): self-contained app shell refresh; fixed World panel, 80% type, fitted tabs, and opt-in storage setting.
// v143 (2026-11-07): the team in Harness (team.js), app.js v15 sends the active agent.
// v148 (2026-11-08): HITL moves from Command to Boundary, as a folded button (hitl.js v2).
// v149 (2026-11-08): old firmas block retired from Command (firmas.js deprecated); HITL reads live on open.
// v151 (2026-11-08): HITL rows show the vigía state (hitl.js v5, hitl.css v4).
// v152 (2026-11-08): HITL texts in the nine languages (app.js v16).
// v153 (2026-11-09): HITL precached (Boundary worked only online); install.js and the 454 KB preceptoros-up.png out of the precache (no served page loads them).
// v154 (proposed): Talk preserves the draft on a verified failure; state does not equate the old motor to Hexelion.
// v155 (proposed after APP-LIVE-01): installed cream manifest/nav chrome.
// v156 (APP-LIVE-04): drop deprecated signatures renderer from the active app shell.
// v157 (APP-LIVE-05): retain last independently verified model after an attempted reply fails.
// v158 (APP-LIVE-06): «found no exact quote» is said by name, in nine languages (app.js v18).
// v159 (app-energy-01): local energy observation in Settings, one no-store read.
// v160 (app-energy-01): English-only controls, metadata and source/read parity.
// v161 (app-energy-02): local sensor answers appear in Talk without model inference.
// v162 (app-en-freeze-01): active English-only language on profile failure.
// 2026-11-11: HITL rows say why a PR is not advancing and can ask Hexelion (hitl.js v6, hitl.css v5). The cache name
// stays v161: only two versioned URLs change, and this file changing is what makes installed apps fetch them.
// 2026-11-11: the install icons are the preceptor's face in dots; their addresses carry ?v=2 so no device keeps the
// painted one. The cache name stays v161 (two open PRs and two tests pin it); this file changing refreshes the list.
// 2026-11-11: 3DFabrik takes the public gate's tab (the gate moves to Settings); Lab and Notebook fold by category.
// app.js and app.css carry a new version; the cache name moves to v162 (pinned by tests).
// 2026-11-12: Notebook operativo (read-only agents, cycles, WBR/MBR) reconciled onto this shell: notebook.js enters
// the list, app.js and app.css carry a new version. The cache name stays v162 (pinned by tests).
// 2026-11-12 (app router piece 01): Talk shows the shared thread with explicit identities and @name addresses a rack
// preceptor. conversacion.js enters the list; insertor.js, app.js and app.css carry new versions; the cache moves to v163.
// 2026-11-12 (notebook receipts 03): Notebook reads command receipts (notebook.js v2). Cache v164.
// 2026-11-12 (common panel header): every panel opens with title, status and refresh; app.js v24, app.css v17. Cache v165.
// 2026-11-12 (meta-harness 01): Notebook and Lab say what happened to each request (notebook.js v3), the door's
// no-answer receipts have their own identity (conversacion.js v2). app.js v25, app.css v18. Cache v166.
// 2026-11-12 (lab bench reader): Lab and Notebook show LAB bench-repro-01-v1 runs re-checked by lab_bench.py
// (notebook.js v4, app.js v26). Cache v167.
// 2026-11-12 (settings groups): Settings folds into four groups (this device and privacy, voice and creations,
// node identity, public gate and tray). Only the shell changes. Cache v168.
const Cache = "preceptoros-armazon-v168";
const Armazon = ["/assets/icono-192.png?v=2", "/assets/icono-512.png?v=2", "/assets/icono-512-maskable.png?v=2", "/", "/app", "/app.html", "/app.css?v=18", "/app.js?v=26", "/notebook.js?v=4", "/conversacion.js?v=2", "/energia_ui.js?v=2", "/modelos_web.js?v=3", "/keep_device.js?v=1", "/acho_motion.js?v=2", "/team.js?v=2", "/hitl.js?v=6", "/hitl.css?v=5", "/insertor.js?v=2", "/creation_publish.js?v=1", "/creation_voice.js?v=1", "/node_registration.js?v=1", "/node_building.js?v=1", "/zonas.js?v=1",
                 "/transicion.js?v=2", "/sting.js?v=1", "/manifest.json",
                 // La brújula conserva su módulo y SVG. La hoja ornamental
                 // quedó en legacy; la estructura mínima no carga ese CSS.
                 "/compass.js?v=39", "/assets/compass.svg?v=39"];

self.addEventListener("install", (e) => {
  // skipWaiting: sin esto, el service worker nuevo espera a que se cierren
  // todas las pestanas viejas. En un movil "cerrar la pestana" no es un gesto
  // que la gente haga, asi que la actualizacion no llegaba nunca.
  self.skipWaiting();
  e.waitUntil(caches.open(Cache).then((c) => c.addAll(Armazon)));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) =>
    Promise.all(ks.filter((k) => k !== Cache).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith("/api/")) return;   // nunca de la caché
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
