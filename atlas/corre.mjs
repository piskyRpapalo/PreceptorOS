// atlas/corre.mjs · el motor de theGame al otro lado de una TUBERIA (2026-09-28).
//
//   node atlas/corre.mjs      y se le habla por stdin, una orden JSON por linea; contesta una por linea.
//
// POR QUE UNA TUBERIA Y NO UN PUERTO. La doctrina D68 de esta app: «ni un socket: un puerto
// local es indistinguible de un tunel». El motor de la conversacion ya se habla asi (proceso hijo,
// entrada y salida estandar); el del juego tambien. Nadie mas que quien lanzo el proceso puede
// hablarle.
//
// ANTES DE JUGAR, LA HUELLA. Cada fichero del motor se compara con `MANIFIESTO.json` (lo escribe
// `bin/traer-motor` desde la web). Si uno no casa, no se juega: FALLO_INTEGRIDAD con el nombre.
// Una copia editada a mano seria otro juego que dice ser este.
//
// ORDENES: inicial{ley} · ciclos{n} · legales · aplica{accion} · final · base{ley,cada,decisiones}
//          · piloto (la regla fija) · gana{p,h} (el criterio del juez).
// Puro por dentro: el motor no ve reloj ni azar; todo lo que pasa es funcion de las ordenes.
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createInterface } from 'node:readline';

const AQUI = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const di = (o) => process.stdout.write(JSON.stringify(o) + '\n');

let man;
try { man = JSON.parse(readFileSync(join(AQUI, 'MANIFIESTO.json'), 'utf8')); }
catch (e) { di({ ok: false, estado: 'NO_DATA', motivo: 'sin MANIFIESTO.json: correr bin/traer-motor' }); process.exit(3); }
const malos = Object.entries(man.ficheros).filter(([f, h]) => {
  try { return createHash('sha256').update(readFileSync(join(AQUI, f))).digest('hex') !== h; } catch (e) { return true; }
}).map(([f]) => f);
if (malos.length) { di({ ok: false, estado: 'FALLO_INTEGRIDAD', motivo: 'no casan con el manifiesto: ' + malos.join(', ') }); process.exit(3); }

const M = require(join(AQUI, 'atlas-motor.js'));
const Pa = require(join(AQUI, 'atlas-partida.js'));
const Pi = require(join(AQUI, 'atlas-piloto.js'));
const J = require(join(AQUI, 'juez.js'));
const SIN_DIA = 'sin-dia';
const BANDAS = ['arrecife', 'ruinas', 'bosque', 'nucleo'];
/* Lo que puede proponer un modelo: el enum de atlas.accion/1 SIN invocar (no gasta). */
const ENUM = ['esperar', 'recoger', 'reparar', 'aplazar', 'bajar_a'];

let e = null, ley = null, min = 0;
const ins = (x) => { const i = Pa.instantanea(x, M); delete i.eventos; return i; };
const metr = (x, m) => {
  let xp = 0; x.xp.forEach((v) => { xp += v; });
  return { fase: M.fase(x), nucleo: M.nivelNucleo(x), integridad_min: m, xp };
};
function forma(a) {
  if (!a || ENUM.indexOf(a.accion) < 0) { return 'accion fuera del enum'; }
  if (a.accion === 'bajar_a' && BANDAS.indexOf(a.banda) < 0) { return 'banda fuera del enum'; }
  if (a.accion !== 'bajar_a' && 'banda' in a) { return 'banda sin bajar_a'; }
  return '';
}
function legales(x) {
  const out = [{ accion: 'esperar' }];
  for (const a of [{ accion: 'recoger' }, { accion: 'reparar' }, { accion: 'aplazar' }, ...BANDAS.map((b) => ({ accion: 'bajar_a', banda: b }))]) {
    if (!J.sinEfecto(M, Pa, x, a)) { out.push(a); }
  }
  return out;
}
function base(l, cada, n) {
  let x = M.inicial(l), m = x.integridad;
  for (let d = 0; d < n; d++) {
    const p = Pi.decide(Pa.instantanea(x, M), M);
    if (Pi.valida(p) && p.accion !== 'esperar') { x = J.aplicar(M, x, p); }
    m = Math.min(m, x.integridad);
    for (let i = 0; i < cada; i++) { x = M.ciclo(x, l); m = Math.min(m, x.integridad); }
  }
  return metr(x, m);
}

di({ ok: true, listo: true, contenido_v: man.contenido_v, web_commit: man.web_commit });
const rl = createInterface({ input: process.stdin });
rl.on('line', (linea) => {
  let o;
  try { o = JSON.parse(linea); } catch (x) { di({ ok: false, motivo: 'orden no es JSON' }); return; }
  try {
    if (o.op === 'inicial') {
      ley = { nd: !!o.ley.nd, integridad_max: o.ley.integridad_max, dano: o.ley.dano };
      e = M.inicial(ley); min = e.integridad; di({ ok: true, ins: ins(e) });
    } else if (!e && o.op !== 'base') {
      di({ ok: false, motivo: 'primero inicial' });
    } else if (o.op === 'ciclos') {
      for (let i = 0; i < o.n; i++) { e = M.ciclo(e, ley); min = Math.min(min, e.integridad); }
      di({ ok: true, ins: ins(e) });
    } else if (o.op === 'legales') {
      di({ ok: true, legales: legales(e) });
    } else if (o.op === 'aplica') {
      const f = forma(o.accion);
      if (f) { di({ ok: false, invalida: true, motivo: f }); return; }
      const antes = JSON.stringify(Pa.final(e, M));
      if (o.accion.accion !== 'esperar') { e = J.aplicar(M, e, o.accion); }
      min = Math.min(min, e.integridad);
      di({ ok: true, cambio: JSON.stringify(Pa.final(e, M)) !== antes, ins: ins(e) });
    } else if (o.op === 'final') {
      di({ ok: true, final: metr(e, min) });
    } else if (o.op === 'piloto') {
      /* La propuesta de la regla fija para el estado de ahora: sirve para probar la tuberia entera
         sin cargar ningun modelo, y dice que es la regla (no se hace pasar por un modelo). */
      const p = Pi.decide(Pa.instantanea(e, M), M);
      di({ ok: true, accion: Pi.valida(p) ? (p.banda ? { accion: p.accion, banda: p.banda } : { accion: p.accion }) : { accion: 'esperar' } });
    } else if (o.op === 'gana') {
      /* El criterio del juez de la web (nucleo > fase > integridad_min > xp): una sola fuente. */
      di({ ok: true, gana: J.gana(o.p, o.h) });
    } else if (o.op === 'base') {
      di({ ok: true, base: base(o.ley, o.cada, o.decisiones) });
    } else {
      di({ ok: false, motivo: 'orden desconocida: ' + o.op });
    }
  } catch (x) { di({ ok: false, motivo: String(x && x.message) }); }
});
