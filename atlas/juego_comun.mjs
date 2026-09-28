// atlas/juego_comun.mjs · lo que el LAB y la APP necesitan del juego y no debe existir dos veces.
//
// Vive en la web, fuera de `public/` (no pesa en la puerta del juego, que es una ley del mundo).
// Lo importan el laboratorio (`hexelion/laboratorio/problemas`, `opinion_juego.mjs`) desde la raiz de
// la web, y la app (`preceptor/atlas/corre.mjs`) desde su copia verificada por sha256
// (`bin/traer-motor`). Antes del 2026-09-28 cada uno llevaba su `legales()`: una regla escrita en
// dos sitios es como un dia el lab y la app discrepan sobre que jugada es legal sin que nadie lo vea.
//
// Puro: recibe el motor (M), la partida (Pa) y el juez (J) de la web; no importa nada por su cuenta.
import { createHash } from 'node:crypto';

export const BANDAS = ['arrecife', 'ruinas', 'bosque', 'nucleo'];
/* Lo que puede proponer un modelo o preguntarse un problema: `atlas.accion/1` SIN invocar (no gasta). */
export const ENUM = ['esperar', 'recoger', 'reparar', 'aplazar', 'bajar_a'];

/* Las acciones LEGALES en un estado: esperar siempre; las demas, solo si cambian algo (una accion
   sin efecto no es una jugada, es una alucinacion: lo mismo que dice el juez). */
export function legales(M, Pa, J, e) {
  const out = [{ accion: 'esperar' }];
  for (const a of [{ accion: 'recoger' }, { accion: 'reparar' }, { accion: 'aplazar' },
                   ...BANDAS.map((b) => ({ accion: 'bajar_a', banda: b }))]) {
    if (!J.sinEfecto(M, Pa, e, a)) { out.push(a); }
  }
  return out;
}

/* La forma de una accion propuesta; '' si esta bien. El permiso lo da el motor, no esto. */
export function forma(a) {
  if (!a || ENUM.indexOf(a.accion) < 0) { return 'accion fuera del enum'; }
  if (a.accion === 'bajar_a' && BANDAS.indexOf(a.banda) < 0) { return 'banda fuera del enum'; }
  if (a.accion !== 'bajar_a' && 'banda' in a) { return 'banda sin bajar_a'; }
  return '';
}

/* La HUELLA de un estado tal como la calcula la pestana (`atlas-opina.js`): sha256 del final
   serializado y escapado a ASCII. Si aqui y alli difieren, una opinion no se ata a su estado. */
export function huella(Pa, M, e) {
  const t = JSON.stringify(Pa.final(e, M)).replace(/[^\x20-\x7e]/g, (c) => '\\u' + ('000' + c.charCodeAt(0).toString(16)).slice(-4));
  return createHash('sha256').update(t).digest('hex');
}
