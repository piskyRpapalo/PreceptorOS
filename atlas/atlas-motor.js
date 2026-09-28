/* preceptoros.org · theGame · el MOTOR de ATLAS, el Bosque Sumergido.

   LOGICA PURA. Ni DOM, ni red, ni reloj propio: recibe un estado y devuelve
   otro. Por eso se prueba fuera del navegador (`atlas/motor_casos.mjs`) y el
   mismo estado da siempre el mismo resultado. Quien pinta es `atlas-piso.js`.

   ENTEROS SIEMPRE. La curva de XP es la tabla OSRS canonica escrita como
   enteros (nivel 2 = 83, 10 = 1 154, 60 = 273 742, 99 = 13 034 431): subir de
   nivel no depende nunca de una coma flotante.

   v1 NO GUARDA NADA. El estado vive en la pestana y muere con ella; el sello
   del juego lo dice. Los eventos `atlas.evento/1` se quedan en memoria: el
   motor no conoce la red. */
(function (raiz) {
  'use strict';

  /* XP minima para cada nivel: XP[0] es el nivel 1, XP[98] el 99. */
  var XP = [0, 83, 174, 276, 388, 512, 650, 801, 969, 1154, 1358, 1584, 1833,
    2107, 2411, 2746, 3115, 3523, 3973, 4470, 5018, 5624, 6291, 7028, 7842,
    8740, 9730, 10824, 12031, 13363, 14833, 16456, 18247, 20224, 22406, 24815,
    27473, 30408, 33648, 37224, 41171, 45529, 50339, 55649, 61512, 67983,
    75127, 83014, 91721, 101333, 111945, 123660, 136594, 150872, 166636,
    184040, 203254, 224466, 247886, 273742, 302288, 333804, 368599, 407015,
    449428, 496254, 547953, 605032, 668051, 737627, 814445, 899257, 992895,
    1096278, 1210421, 1336443, 1475581, 1629200, 1798808, 1986068, 2192818,
    2421087, 2673114, 2951373, 3258594, 3597792, 3972294, 4385776, 4842295,
    5346332, 5902831, 6517253, 7195629, 7944614, 8771558, 9684577, 10692629,
    11805606, 13034431];
  var XP_TOPE = 200000000;

  /* Los siete oficios, en el orden de `skills` de `atlas-<lengua>.json`. */
  var OFICIOS = ['descenso', 'pesca', 'mineria', 'forja', 'herboristeria',
    'restauracion', 'ingenieria'];
  var O = {};
  OFICIOS.forEach(function (k, i) { O[k] = i; });

  /* Bandas de profundidad: luz que llega, consumo de oxigeno y su etiqueta
     para el evento. El arrecife recarga oxigeno en vez de gastarlo. */
  var BANDAS = {
    arrecife: { luz: 3, o2: 1, lab: '0-50' },
    ruinas: { luz: 2, o2: 2, lab: '50-150' },
    bosque: { luz: 1, o2: 4, lab: '150-300' },
    nucleo: { luz: 0, o2: 8, lab: '300+' }
  };
  var LUZ_MAX = 600, O2_MAX = 300, O2_RECARGA = 3;
  var COBRE_REPARAR = 10, REPARA = 25, INGENIERIA_NUCLEO = 60;
  var DIA_MS = 86400000, CICLO_MS = 1000;

  /* Cinco fases por nivel del Nucleo (la suma de los siete oficios), y cada
     cuantos ciclos se vuelve a abrir la grieta en cada una. */
  var FASES = [1, 10, 25, 45, 70];
  var REABRE = [180, 240, 300, 120, 600];

  var CATALOGO = {
    contenido_v: '2026-09-27.1',
    misiones: ['grieta-120', 'expedicion', 'cosecha', 'incubacion'],
    sectores: ['nucleo', 'forja', 'aguja', 'ojo', 'grieta'],
    profundidades: ['0-50', '50-150', '150-300', '300+']
  };

  function entero(x) { return typeof x === 'number' && isFinite(x) && Math.floor(x) === x; }

  function nivelDesdeXp(xp) {
    if (!entero(xp) || xp < 0) { throw new RangeError('XP invalida: ' + xp); }
    var n = 1;
    for (var i = 1; i < XP.length && xp >= XP[i]; i++) { n = i + 1; }
    return n;
  }
  function xpParaNivel(n) {
    if (!entero(n) || n < 1 || n > 99) { throw new RangeError('nivel invalido: ' + n); }
    return XP[n - 1];
  }
  function subeDeNivel(xp, ganada) {
    if (!entero(ganada) || ganada < 0) { throw new RangeError('XP ganada invalida: ' + ganada); }
    var antes = nivelDesdeXp(xp), nueva = Math.min(XP_TOPE, xp + ganada);
    return { xp: nueva, antes: antes, despues: nivelDesdeXp(nueva) };
  }

  /* Las leyes del mundo salen de medidas reales de la web
     (`atlas-mundo.json`). Sin ellas, leyes neutras y se dice. */
  function leyes(mundo) {
    var m = mundo || {}, nd = !mundo;
    var pruebas = entero(m.pruebas_web) ? m.pruebas_web : null;
    var arnes = typeof m.arnes_sw === 'string' ? m.arnes_sw.split('/') : null;
    var arnesOk = !arnes || (arnes.length === 2 && arnes[0] === arnes[1]);
    var pesado = entero(m.gzip_juego_b) && m.gzip_juego_b > 150 * 1024;
    return {
      nd: nd,
      integridad_max: 100 + (pruebas === null ? 0 : Math.floor(pruebas / 10)),
      dano: (arnesOk ? 1 : 2) * (pesado ? 2 : 1)
    };
  }

  function nivelNucleo(e) {
    var s = 0;
    e.xp.forEach(function (x) { s += x; });
    return nivelDesdeXp(Math.min(s, XP_TOPE));
  }
  function fase(e) {
    var n = nivelNucleo(e), f = 1;
    FASES.forEach(function (umbral, i) { if (n >= umbral) { f = i + 1; } });
    return f;
  }
  function siguienteFase(e) {
    var f = fase(e);
    return f < FASES.length ? { fase: f + 1, nivel: FASES[f] } : null;
  }

  function inicial(ley) {
    var l = ley || leyes(null);
    return {
      v: 1, t: 0, prof: 'ruinas', luz: 0, biomasa: 0, cobre: 0, flujo: 0,
      o2: O2_MAX, integridad: l.integridad_max, integridad_max: l.integridad_max,
      abierta: true, cierre: 0, xp: OFICIOS.map(function () { return 0; }),
      pendiente: null, eventos: [], subidas: [], avisos: []
    };
  }
  function copia(e) { return JSON.parse(JSON.stringify(e)); }

  function gana(e, oficio, cantidad) {
    if (!cantidad) { return; }
    var i = O[oficio], r = subeDeNivel(e.xp[i], cantidad);
    e.xp[i] = r.xp;
    if (r.despues > r.antes) { e.subidas.push({ oficio: oficio, nivel: r.despues }); }
  }

  /* El evento que un dia firmara la persona y leera la Aduana. Mismo
     esquema que la mision del laboratorio; aqui no sale de memoria. */
  function evento(e, tipo, mision, sector, resultado, dia) {
    var ev = {
      esquema: 'atlas.evento/1', contenido_v: CATALOGO.contenido_v,
      dia: dia || new Date().toISOString().slice(0, 10), tipo: tipo,
      mision: mision, sector: sector, profundidad: BANDAS[e.prof].lab,
      resultado: resultado, valoracion: null, nota: null
    };
    e.eventos.push(ev);
    if (e.eventos.length > 200) { e.eventos.shift(); }
    return ev;
  }

  /* Produccion de un ciclo: luz -> biomasa -> la Forja la hace cobre. */
  function produce(e, prof) {
    e.luz = Math.min(LUZ_MAX, e.luz + BANDAS[prof].luz);
    var g = Math.min(e.luz, 2);
    e.luz -= g; e.biomasa += g; gana(e, 'herboristeria', g);
    e.flujo = Math.floor(e.luz * 100 / LUZ_MAX);
    var k = Math.min(e.flujo >= 50 ? 2 : 1, Math.floor(e.biomasa / 5));
    if (k > 0) {
      e.biomasa -= 5 * k; e.cobre += k;
      gana(e, 'forja', 2 * k); gana(e, 'mineria', k);
    }
  }

  function ciclo(estado, ley) {
    var e = copia(estado), l = ley || leyes(null);
    e.integridad_max = l.integridad_max;
    produce(e, e.prof);
    if (e.prof === 'arrecife') {
      e.o2 = Math.min(O2_MAX, e.o2 + O2_RECARGA - BANDAS.arrecife.o2);
    } else {
      e.o2 -= BANDAS[e.prof].o2;
      gana(e, 'descenso', BANDAS[e.prof].o2 - 1);
      if (e.o2 <= 0) { e.o2 = 0; e.prof = 'arrecife'; e.avisos.push('ascenso'); }
    }
    if (e.abierta) {
      e.integridad = Math.max(0, e.integridad - l.dano);
    } else if (--e.cierre <= 0) {
      e.abierta = true; e.cierre = 0; e.avisos.push('grieta');
    }
    e.integridad = Math.min(e.integridad, e.integridad_max);
    e.t += 1;
    return e;
  }

  /* MIENTRAS DORMIAS: la pestana oculta produce desde el arrecife, sin grieta
     ni oxigeno, y nunca mas de 24 h. Lo producido espera a «Recoger». */
  function dormir(estado, ms) {
    if (!entero(ms) || ms < 0) { throw new RangeError('ms invalido: ' + ms); }
    var e = copia(estado);
    var p = e.pendiente || { ciclos: 0, biomasa: 0, cobre: 0, xp: 0 };
    var libres = Math.floor(DIA_MS / CICLO_MS) - p.ciclos;
    var n = Math.max(0, Math.min(Math.floor(ms / CICLO_MS), libres));
    var s = { luz: e.luz, biomasa: 0, cobre: 0, flujo: 0, xp: e.xp.slice(), subidas: [] };
    for (var i = 0; i < n; i++) { produce(s, 'arrecife'); }
    var xp = 0;
    s.xp.forEach(function (x, j) { xp += x - e.xp[j]; });
    p.ciclos += n; p.biomasa += s.biomasa; p.cobre += s.cobre;
    p.xp += xp + Math.floor(n / 60);
    p.dxp = (p.dxp || OFICIOS.map(function () { return 0; })).map(function (x, j) {
      return x + (s.xp[j] - e.xp[j]) + (j === O.pesca ? Math.floor(n / 60) : 0);
    });
    e.pendiente = p;
    return e;
  }

  function recoger(estado, dia) {
    var e = copia(estado), p = e.pendiente;
    if (!p || !p.ciclos) { evento(e, 'recoger', 'cosecha', 'forja', 'fallo', dia); return e; }
    e.biomasa += p.biomasa; e.cobre += p.cobre;
    (p.dxp || []).forEach(function (x, j) { gana(e, OFICIOS[j], x); });
    e.pendiente = null;
    evento(e, 'recoger', 'cosecha', 'forja', 'ok', dia);
    return e;
  }

  function reparar(estado, dia) {
    var e = copia(estado);
    if (!e.abierta || e.cobre < COBRE_REPARAR) {
      evento(e, 'reparar', 'grieta-120', 'grieta', 'fallo', dia);
      return e;
    }
    e.cobre -= COBRE_REPARAR;
    e.integridad = Math.min(e.integridad_max, e.integridad + REPARA);
    e.abierta = false;
    e.cierre = REABRE[fase(e) - 1];
    gana(e, 'restauracion', 40); gana(e, 'ingenieria', 15);
    evento(e, 'reparar', 'grieta-120', 'grieta', 'ok', dia);
    return e;
  }

  function aplazar(estado, dia) {
    var e = copia(estado);
    evento(e, 'aplazar', 'grieta-120', 'grieta', 'ok', dia);
    return e;
  }

  /* INVOCAR (theGame v1.5): gastar Cobre y Luz en una Treasure Class. Aqui
     solo se paga: que cae lo decide `gacha.js` con la semilla firmada, fuera
     del motor. Sin recursos, fallo y no se toca nada. */
  function invocar(estado, coste, dia) {
    var e = copia(estado), c = coste || {};
    if (!entero(c.cobre) || !entero(c.luz) || c.cobre < 0 || c.luz < 0) { throw new RangeError('coste invalido'); }
    var ok = e.cobre >= c.cobre && e.luz >= c.luz;
    if (ok) { e.cobre -= c.cobre; e.luz -= c.luz; e.flujo = Math.floor(e.luz * 100 / LUZ_MAX); }
    evento(e, 'invocar', 'incubacion', 'forja', ok ? 'ok' : 'fallo', dia);
    return e;
  }

  function puedeBajar(e, prof) {
    if (!BANDAS[prof]) { return 'banda'; }
    if (prof === 'nucleo' && nivelDesdeXp(e.xp[O.ingenieria]) < INGENIERIA_NUCLEO) { return 'ingenieria'; }
    if (prof !== 'arrecife' && e.o2 <= 0) { return 'oxigeno'; }
    return '';
  }
  function bajarA(estado, prof, dia) {
    var e = copia(estado), motivo = puedeBajar(e, prof);
    if (!motivo) { e.prof = prof; }
    evento(e, 'bajar_a', 'expedicion', 'ojo', motivo ? 'fallo' : 'ok', dia);
    return e;
  }

  var AtlasMotor = {
    XP: XP, OFICIOS: OFICIOS, BANDAS: BANDAS, FASES: FASES, CATALOGO: CATALOGO,
    LUZ_MAX: LUZ_MAX, O2_MAX: O2_MAX, COBRE_REPARAR: COBRE_REPARAR,
    INGENIERIA_NUCLEO: INGENIERIA_NUCLEO, DIA_MS: DIA_MS, CICLO_MS: CICLO_MS,
    nivelDesdeXp: nivelDesdeXp, xpParaNivel: xpParaNivel, subeDeNivel: subeDeNivel,
    leyes: leyes, inicial: inicial, ciclo: ciclo, dormir: dormir, recoger: recoger,
    reparar: reparar, aplazar: aplazar, bajarA: bajarA, puedeBajar: puedeBajar, invocar: invocar,
    fase: fase, siguienteFase: siguienteFase, nivelNucleo: nivelNucleo
  };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasMotor; }
  else { raiz.AtlasMotor = AtlasMotor; }
})(this);
