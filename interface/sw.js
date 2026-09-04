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
const Cache = "aurelius-armazon-v58";
const Armazon = ["/", "/dashboard.html", "/dashboard.css", "/dashboard.js",
                 "/app.html", "/app.css", "/app.js", "/manifest.json",
                 // La brujula entera, SVG incluido. Sin el .svg cacheado, sin
                 // red no se dibuja ninguna rosa y el `catch` de compass.js se
                 // lo traga en silencio: la brujula desapareceria justo cuando
                 // el producto promete funcionar sin conexion.
                 "/compass.css?v=39", "/compass.js?v=39", "/assets/compass.svg?v=39"];

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
