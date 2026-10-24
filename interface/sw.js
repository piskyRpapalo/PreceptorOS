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
const Cache = "preceptoros-armazon-v113";
const Armazon = ["/", "/face/basic.html", "/face/atlantis.html", "/face/zombie.html", "/face/face.js", "/face/face_world.js", "/face/face_paint.js", "/face/face_battle.js", "/face/face_panel.js", "/face/face_fight.js", "/face/face_hud.js", "/face/face.css", "/face/bubble/tabla_semantica.js", "/face/bubble/comic_%74okens.js", "/face/bubble/comic_accents.js", "/face/bubble/valores.js", "/face/bubble/gacha.js", "/face/bubble/comic_atoms.js", "/face/bubble/bubble_light.js", "/face/bubble/bubble_language.js", "/face/bubble/bubble_bestiary.js", "/face/bubble/bubble_world.js", "/face/bubble/core.js", "/face/bubble/isometric_floor_projection.js", "/face/bubble/world_camera.js", "/face/bubble/map_zoom.js", "/face/bubble/fog_of_war.js", "/face/bubble/atlas-coord.js", "/face/bubble/canon.js", "/face/bubble/combate_ticks.js", "/face/bubble/escuadron.js", "/face/bubble/wave_render.js", "/face/bubble/worm_transition.js", "/face/bubble/escena.js", "/face/bubble/sea-floor.js", "/face/bubble/gdpr-art25-ephemeral-crab.js", "/face/bubble/crab_render_hd.js",
                 "/dashboard.html", "/dashboard.css?v=58", "/dashboard.js?v=49",
                 "/app.html", "/app.css?v=3", "/app.js?v=5", "/creation_publish.js?v=1", "/zonas.js?v=1",
                 "/transicion.js?v=2", "/sting.js?v=1", "/manifest.json",
                 // La brújula conserva su módulo y SVG. La hoja ornamental
                 // quedó en legacy; la estructura mínima no carga ese CSS.
                 "/compass.js?v=39", "/assets/compass.svg?v=39",
                 // La consola: sin estas dos, sin red el home pediria piezas
                 // que no estan y la barra no saldria.
                 "/consola.css?v=4", "/consola.js?v=4"];

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
