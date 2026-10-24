(function (root) {
'use strict';
const { cos, sin, tan, exp, sqrt, hypot, floor, ceil, round, imul, min, max, PI } = Math;
const NODE = typeof module === 'object' && !!module.exports;
const VERSION = 'preceptoros.bubble/1', CANVAS = [412, 515], LIGHT = [-0.35, -0.94];
const STYLES = ['volume', 'etch', 'clear'], PRIMS = ['wave', 'blob', 'ribbon', 'arcs', 'field', 'wall', 'text', 'keep', 'neck'];
const SUBS = ['brillo', 'base', 'sombra', 'contorno'], MAX = 8, words = Object.create(null);
const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
const lib = (n) => (NODE ? require('./' + { AtlasGacha: 'gacha', AtlasComicTokens: 'comic_tokens', AtlasComicAccents: 'comic_accents', AtlasSemantica: 'tabla_semantica' }[n] + '.js') : root[n]);
const light = () => {
 if (!NODE) return root.AtlasBubbleLight || null;
 try { return require('./bubble_light.js'); } catch (e) { if (e.code === 'MODULE_NOT_FOUND') return null; throw e; }
};
const num = (v, d) => (typeof v === 'number' && isFinite(v) ? v : d);
const nums = (it, keys) => keys.split(' ').every((k) => typeof it[k] === 'number' && isFinite(it[k]));
const pair = (v) => (Array.isArray(v) && v.length === 2 && typeof v[0] === 'number' && typeof v[1] === 'number' ? v : null);
const rd = (x) => round(x * 100) / 100, f2 = (x) => String(rd(x));
const circ = (x, y, r, fill, stroke, lw) => ({ op: 'circle', x: rd(x), y: rd(y), r: rd(r), fill, stroke, lw: lw || 0, shadow: null });
const txt = (x, y, text, size, fill) => ({ op: 'text', x, y, text, size, weight: 'bold', align: 'center', fill });
const path = (d, fill, stroke, lw) => ({ op: 'path', d, fill, stroke, lw: lw || 0, shadow: null });
const grupo = (o, items, x, y, rot) => ({ op: 'group', x: x || 0, y: y || 0, rot: rot || 0, s: 1, o, items });
const xform = (pts, sc, rot, x, y) => {
 const r = rot * PI / 180, c = cos(r), s = sin(r);
 return pts.map((q) => [x + q[0] * sc * c - q[1] * sc * s, y + q[0] * sc * s + q[1] * sc * c]);
};

function band(name) {
 const K = lib('AtlasComicTokens'), n = String(name), cut = n.lastIndexOf('.');
 if (has(K.NEUTRAL, n)) return K.NEUTRAL[n];
 const head = n.slice(0, max(cut, 0)), sub = n.slice(cut + 1);
 if (SUBS.includes(sub)) {
  const A = lib('AtlasComicAccents'), S = lib('AtlasSemantica');
  if (has(A.ACCENTS, head)) return A.ACCENTS[head].bands[sub];
  if (has(S.TABLA, head)) return S.bandas(S.TABLA[head], S.SAT, S.LUZ)[sub];
 }
 throw new Error('unknown band: ' + n);
}

const brilloOf = (f) => {
 if (f === 'cyan') return band('paper');
 const cut = String(f).lastIndexOf('.');
 return f === 'paper' || f === 'ink' || f === 'ocean' || cut < 0 ? null : band(String(f).slice(0, cut) + '.brillo');
};

function hash32(s) {
 let h = 0x811c9dc5;
 const t = String(s);
 for (let i = 0; i < t.length; i++) h = imul(h ^ t.charCodeAt(i), 0x01000193);
 return h >>> 0;
}

function rng(key) {
 let a = hash32(key) | 0;
 return () => {
  a = (a + 0x6d2b79f5) | 0;
  let t = imul(a ^ (a >>> 15), 1 | a);
  t = (t + imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
 };
}
function wavePoints(h, n) {
 const m = n === undefined ? 96 : n, G = lib('AtlasGacha'), out = [];
 for (let i = 0; i < m; i++) out.push(G.punto(h, 2 * PI * i / m));
 return out;
}

function smoothPath(pts, closed) {
 const n = pts.length;
 if (!n) return '';
 const P = (q) => f2(q[0]) + ' ' + f2(q[1]);
 let d = 'M' + P(pts[0]);
 for (let i = 0, segs = closed ? n : n - 1; i < segs; i++) {
  const p0 = closed ? pts[(i + n - 1) % n] : pts[max(0, i - 1)], p1 = pts[i];
  const p2 = closed ? pts[(i + 1) % n] : pts[i + 1], p3 = closed ? pts[(i + 2) % n] : pts[min(n - 1, i + 2)];
  d += 'C' + f2(p1[0] + (p2[0] - p0[0]) / 6) + ' ' + f2(p1[1] + (p2[1] - p0[1]) / 6) + ' ' +
   f2(p2[0] - (p3[0] - p1[0]) / 6) + ' ' + f2(p2[1] - (p3[1] - p1[1]) / 6) + ' ' + P(p2);
 }
 return closed ? d + 'Z' : d;
}

function depthOf(it) {
 const d = it.d === undefined ? 0 : it.d;
 if (d !== 0 && d !== 1 && d !== 2) throw new Error('bubble: depth ' + d);
 return d;
}
const strokeOf = (it, depth) => (depth === 2
 ? { stroke: band('cyan'), lw: num(it.lw, 2.5) }
 : { stroke: band(it.s || 'ink'), lw: num(it.lw, depth === 0 ? 3.5 : 3.0) });
const note = (o, k, cause) => { compile.notes.push({ o, k, cause }); };
const bad = (it) => { note(String(it.o), String(it.k ?? ''), 'NO_DATA · parametros de ' + it.o); return null; };

function shape(sc, name, pts, closed, it, extra) {
 const depth = depthOf(it), st = strokeOf(it, depth), d = smoothPath(pts, closed), g = grupo(name, []);
 const filled = closed && depth < 2 && it.f != null, vetas = depth < 2 && extra ? extra : [];
 if (closed) g.contour = pts;
 if (filled && light()) {
  const dark = it.f === 'ink' || it.f === 'ocean';
  sc.jobs.push({ g, pts, vetas, opts: {
   light: sc.light, style: sc.style, depth, fill: band(it.f), shadow: band(dark ? 'cyan' : 'ink'),
   ink: band('ink'), stroke: st.stroke, lw: num(it.lw, undefined), rim: band('cyan'),
   highlight: brilloOf(it.f), toPath: smoothPath } });
  return g;
 }
 if (filled) g.items.push(path(d, band(it.f), null, 0));
 g.items.push(path(d, null, st.stroke, st.lw), ...vetas);
 return g;
}

function finalize(sc) {
 const LG = light();
 sc.jobs.forEach((j) => {
  LG.apply(j.g.items, j.pts, Object.assign({ textBoxes: sc.boxes }, j.opts));
  j.g.items.push(...j.vetas);
 });
 sc.jobs = [];
}

function neck(a, b, k, p, side) {
 if (!pair(a) || !pair(b) || !a.every(Number.isFinite) || !b.every(Number.isFinite) || !Number.isFinite(k) || k < 0 || !Number.isFinite(p) || p < 0 || p > 1 || (side !== undefined && side !== -1 && side !== 1)) throw new Error('bubble: neck');
 const dx = b[0] - a[0], dy = b[1] - a[1], len = hypot(dx, dy) || 1, width = k * 4 * p * (1 - p) * (side || 1);
 return Array.from({ length: 25 }, (_, i) => { const t = i / 24, q = width * sin(PI * t); return [rd(a[0] + dx * t - dy / len * q), rd(a[1] + dy * t + dx / len * q)]; });
}

const PRIM = {
 neck: (sc, it) => (pair(it.a) && pair(it.b) && it.a.every(Number.isFinite) && it.b.every(Number.isFinite) && nums(it, 'k p') && it.k >= 0 && it.p >= 0 && it.p <= 1 && (it.side === undefined || it.side === -1 || it.side === 1)
  ? shape(sc, 'neck', neck(it.a, it.b, it.k, it.p, it.side), false, it)
  : bad(it)),
 wave: (sc, it) => (nums(it, 'x y') && Array.isArray(it.h) && it.h.length
  ? shape(sc, 'wave', xform(wavePoints(it.h, 96), num(it.sc, 1), num(it.rot, 0), it.x, it.y), true, it)
  : bad(it)),
 blob: (sc, it, r) => {
  if (!nums(it, 'x y rx ry') || !(it.rx > 0 && it.ry > 0)) return bad(it);
  const m = min(it.rx, it.ry), rough = min(1, max(0, num(it.rough, 0.25))), h = [[1, it.rx, it.ry, 0]], harm = [];
  let s = 0, suma = 0;
  for (let k = 2; k <= 5; k++) {
   const u1 = r(), u2 = r(), u3 = r();
   harm.push([k, rough * 0.12 * m * u1 / k, u2, u3]);
   s += rough * 0.12 * m * u1;
  }
  const techo = 0.45 * m, esc = s > techo ? techo / s : 1;
  for (const q of harm) { const a = q[1] * esc; h.push([q[0], a, a * (0.6 + 0.4 * q[2]), q[3] * 64]); suma += q[0] * a; }
  const g = shape(sc, 'blob', xform(wavePoints(h, 96), num(it.sc, 1), num(it.rot, 0), it.x, it.y), true, it);
  g.bound = { sum: suma, limit: techo };
  return g;
 },
 ribbon: (sc, it) => {
  const p = Array.isArray(it.pts) ? it.pts : [];
  return p.length < 2 || !p.every((q) => pair(q)) ? bad(it) : shape(sc, 'ribbon', p, !!it.closed, it, null);
 },
 arcs: (sc, it) => {
  if (!nums(it, 'x y n arc ph') || !Array.isArray(it.r) || typeof it.r[0] !== 'number') return bad(it);
  const r0 = it.r[0], r1 = num(it.r[1], r0), n = max(1, floor(it.n));
  let d = '';
  for (let i = 0; i < n; i++) {
   const rad = r0 + (r1 - r0) * (n > 1 ? i / (n - 1) : 0), a0 = (it.ph + i * 360 / n) * PI / 180, a1 = a0 + it.arc * PI / 180;
   d += 'M' + f2(it.x + rad * cos(a0)) + ' ' + f2(it.y + rad * sin(a0)) + 'A' + f2(rad) + ' ' + f2(rad) +
    ' 0 ' + (it.arc > 180 ? 1 : 0) + ' 1 ' + f2(it.x + rad * cos(a1)) + ' ' + f2(it.y + rad * sin(a1));
  }
  const st = strokeOf(it, depthOf(it));
  return grupo('arcs', [path(d, null, st.stroke, st.lw)]);
 },
 field: (sc, it, r) => {
  if (!has(FIELDS, it.kind)) return bad(it);
  const items = FIELDS[it.kind](sc, it, r);
  return items ? grupo('field', items) : null;
 },
 wall: (sc, it, r) => {
  const side = it.side === undefined ? 'right' : it.side;
  if (!pair(it.x) || !pair(it.y) || !(it.y[1] > it.y[0]) || (side !== 'left' && side !== 'right')) return bad(it);
  const [x0] = it.x, [y0, y1] = it.y, H = y1 - y0, s = side === 'left' ? 1 : -1, per = num(it.per, 0);
  const tn = tan(num(it.tilt, 0) * PI / 180), ph = [r() * 2 * PI, r() * 2 * PI, r() * 2 * PI];

  const edge = (y) => {
   const t = y - y0;
   let v = x0 + t * tn;
   for (let j = 1; j <= 3; j++) v += (6 / j) * sin(2 * PI * j * t / H + ph[j - 1]);
   for (let j = 1; per > 0 && j * per <= H; j++) { const dt = t - j * per; v += s * 7 * exp(-dt * dt / 25); }
   return v;
  };
  const sideX = s > 0 ? -40 : sc.cv[0] + 40, lip = it.lip === undefined ? 'round' : it.lip, R = 24;
  const P = [[sideX, y0]];
  let top = y0;
  if (lip === 'round' && H > 48) {
   const yA = y0 + R, cx = edge(yA) - s * R, t1 = s > 0 ? 0 : -PI;
   for (let q = 0; q <= 8; q++) { const th = -PI / 2 + (t1 + PI / 2) * q / 8; P.push([cx + R * cos(th), yA + R * sin(th)]); }
   top = yA;
  } else P.push([edge(y0), y0]);
  const N = min(400, max(24, ceil(H / 4)));
  for (let q = 1; q <= N; q++) { const yy = top + (y0 + H - top) * q / N; P.push([edge(yy), yy]); }
  P.push([sideX, y0 + H]);
  let vd = '';
  for (let v = 0; v < floor(num(it.vein, 0)); v++) {
   const vp = [];
   for (let k = 0; k < 5; k++) { const vy = y0 + H * (0.1 + 0.2 * k + 0.1 * r()), dx = 20 + 50 * r(); vp.push([edge(vy) - s * dx, vy]); }
   vd += smoothPath(vp, false);
  }
  return shape(sc, 'wall', P, true, it, vd ? [path(vd, null, band('ink'), 1.2)] : []);
 },
 text: (sc, it) => {
  if (!nums(it, 'x y') || typeof it.tx !== 'string') return bad(it);
  const sz = num(it.sz, 16), w = num(it.w, 0.6 * sz * it.tx.length), rot = num(it.rot, 0), items = [];
  if (Array.isArray(it.sh)) items.push(txt(num(it.sh[0], 0), num(it.sh[1], 0), it.tx, sz, band(it.sh[2])));
  items.push(txt(0, 0, it.tx, sz, band(it.f || 'ink')));
  sc.boxes.push(xform([[-w / 2, -sz * 0.7], [w / 2, -sz * 0.7], [w / 2, sz * 0.7], [-w / 2, sz * 0.7]], 1, rot, it.x, it.y));
  return grupo('text', items, it.x, it.y, rot);
 },
};

const FIELDS = {
 halftone: (sc, it) => {
  const x = it.x === undefined ? [0, sc.cv[0]] : it.x, y = it.y === undefined ? [0, sc.cv[1]] : it.y;
  const rs = String(it.r === undefined ? '5|3|1.5|0' : it.r).split('|').map(Number), st = num(it.step, 12), a = num(it.a, 45) * PI / 180;
  if (!pair(x) || !pair(y) || !(x[1] > x[0] && y[1] > y[0]) || !(st >= 2) || rs.some((v) => !isFinite(v))) return bad(it);
  const H = y[1] - y[0], K = ceil(hypot(x[1] - x[0], H) / st) + 1;
  if (K > 400) return bad(it);
  const c0 = cos(a), c1 = sin(a), cx = (x[0] + x[1]) / 2, cy = (y[0] + y[1]) / 2, fill = band(it.f || 'cyan'), out = [];
  for (let i = -K; i <= K; i++) for (let j = -K; j <= K; j++) {
   const px = cx + st * (i * c0 - j * c1), py = cy + st * (i * c1 + j * c0);
   if (px < x[0] || px > x[1] || py < y[0] || py > y[1]) continue;
   const rr = rs[min(rs.length - 1, floor((py - y[0]) / H * rs.length))];
   if (rr > 0) out.push(circ(px, py, rr, fill, null));
  }
  return out;
 },
 bubbles: (sc, it, r) => {
  if (!nums(it, 'x y')) return bad(it);
  const n = max(0, floor(num(it.n, 3))), h = num(it.h, 200), rr = Array.isArray(it.r) ? it.r : [4, 10], out = [];
  const ocean = band('ocean'), cy = band('cyan'), paper = band('paper');
  for (let i = 0; i < n; i++) {
   const t = n > 1 ? i / (n - 1) : 0, dx = (r() - 0.5) * 8, br = num(rr[0], 4) + (num(rr[1], 10) - num(rr[0], 4)) * r();
   const bx = it.x + dx, by = it.y - h * t, ra = 0.6 * br, P = (deg) => [bx + ra * cos(deg * PI / 180), by + ra * sin(deg * PI / 180)];
   const pa = P(190), pb = P(230);
   out.push(circ(bx, by, br, ocean, cy, 2), path('M' + f2(pa[0]) + ' ' + f2(pa[1]) + 'A' + f2(ra) + ' ' + f2(ra) + ' 0 0 1 ' + f2(pb[0]) + ' ' + f2(pb[1]), null, paper, 1.6));
  }
  return out;
 },
 snow: (sc, it, r) => {
  const n = max(0, floor(num(it.n, 0))), fill = band(it.f || 'paper'), out = [];
  for (let i = 0; i < n; i++) { const x = r() * sc.cv[0], y = r() * sc.cv[1], rad = 1 + 0.5 * r(); out.push(circ(x, y, rad, fill, null)); }
  return out;
 },
 phyllo: (sc, it) => {
  if (!nums(it, 'x y n c r')) return bad(it);
  const n = max(1, floor(it.n)), fill = band(it.f || 'paper'), stroke = it.s ? band(it.s) : null, out = [];
  for (let i = 0; i < n; i++) {
   const ang = i * 137.508 * PI / 180, dist = it.c * sqrt(i);
   out.push(circ(it.x + dist * cos(ang), it.y + dist * sin(ang), it.r * (1 - 0.5 * i / n), fill, stroke, num(it.lw, 1.5)));
  }
  return out;
 },
 school: (sc, it, r) => {
  if (!pair(it.x) || !pair(it.y)) return bad(it);
  const n = max(0, floor(num(it.n, 0))), body = [[-9, 0], [-3, -4], [5, -3], [9, 0], [5, 3], [-3, 4]];
  let d = '';
  for (let i = 0; i < n; i++) {
   const px = it.x[0] + (it.x[1] - it.x[0]) * r(), py = it.y[0] + (it.y[1] - it.y[0]) * r(), k = 0.8 + 0.4 * r(), rot = (r() - 0.5) * 40;
   const tl = (p, closed) => smoothPath(xform(p, k, rot, px, py), closed);
   d += tl(body, true) + tl([[8, 0], [14, -4]], false) + tl([[8, 0], [14, 4]], false);
  }
  return d ? [path(d, null, band(it.s || 'cyan'), num(it.lw, 1.2))] : [];
 },
};

function keep(sc, it, out) {
 const k = String(it.k ?? ''), cut = k.indexOf(':');
 const sid = cut < 0 ? k : k.slice(0, cut), names = cut < 0 ? null : k.slice(cut + 1).split('|'), map = sc.prev || {};
 if (!Object.keys(map).length) return note('keep', k, 'NO_DATA · keep sin prev');
 if (!has(map, sid)) return note('keep', k, 'NO_DATA · keep sin seccion ' + sid);
 const atoms = section(map[sid], map, sc.fd + 1, names);
 if (names && !atoms.length) return note('keep', k, 'NO_DATA · keep sin coincidencia');
 atoms.forEach((a) => out.push(...a.items));
}

function item(sc, ai, it, out, wd) {
 if (wd > MAX) throw new Error('bubble: anidamiento excesivo');
 if (!it || typeof it.o !== 'string') return note('?', String(ai), 'NO_DATA · item sin o');
 const key = it.seed != null && it.seed !== '' ? String(it.seed) : sc.frame.id + ':' + ai;
 if (has(words, it.o)) {
  const kids = words[it.o](it, { key, rng: rng(key), frame: sc.frame, atom: ai, band, depth: wd });
  if (!Array.isArray(kids)) throw new Error('bubble: palabra sin lista ' + it.o);
  kids.forEach((kid, j) => item(sc, ai, Object.assign({}, kid, kid.seed == null ? { seed: key + '/' + j } : {}), out, wd + 1));
  return;
 }
 if (it.o === 'keep') return keep(sc, it, out);
 if (!has(PRIM, it.o)) return note(it.o, String(ai), 'NO_DATA · primitiva');
 const g = PRIM[it.o](sc, it, rng(key));
 if (g) out.push(g);
}

function section(frame, prev, fd, only) {
 if (fd > MAX) throw new Error('bubble: keep en bucle');
 if (!frame || frame.v !== VERSION || !Array.isArray(frame.atoms)) throw new Error('bubble: marco no admitido');
 const cv = pair(frame.cv ?? CANVAS), lg = pair(frame.light ?? LIGHT), style = frame.style ?? 'volume';
 if (!cv || !lg || !STYLES.includes(style)) throw new Error('bubble: cv, light o style');
 const sc = { frame, prev, fd, cv, light: lg, style, boxes: [], jobs: [] }, res = [];
 frame.atoms.forEach((atom, ai) => {
  if (only && !only.includes(String(atom && atom.k))) return;
  const items = [];
  (atom && Array.isArray(atom.i) ? atom.i : []).forEach((it) => item(sc, ai, it, items, 0));
  res.push({ k: atom && atom.k, items });
 });
 finalize(sc);
 return res;
}

function compile(frame) {
 compile.notes = [];
 const prev = frame?.prev ?? {}, out = [];
 section(frame, prev, 0, null).forEach((a) => out.push(...a.items));
 return out;
}

function define(name, fn) {
 if (typeof name !== 'string' || PRIMS.includes(name) || typeof fn !== 'function') throw new Error('bubble: define ' + name);
 words[name] = fn;
}
const AtlasBubble = Object.freeze({ compile, define, words: () => Object.keys(words), hash32, rng, wavePoints, smoothPath, neck, band });
if (NODE) module.exports = AtlasBubble; else root.AtlasBubble = AtlasBubble;
})(typeof module === 'object' && module.exports ? this : (this || window));
