(function (raiz) {
  'use strict';

    var HEX = { x: 0, y: 0 };
  var ANILLO = { tc1: 330, tc2: 400, tc3: 460, tc4: 520 };
  function h32(hex) { return parseInt(String(hex).slice(0, 8), 16) >>> 0; }

    function sitioLugar(l, sha, pub) {
    if (l.npc) {
      var a = (l.orden * 48 + 95) * Math.PI / 180, r = ANILLO[l.tc] || 400;
      return { x: Math.round(Math.cos(a) * r), y: Math.round(Math.sin(a) * r) };
    }
    var ang = (h32(sha(l.de)) % 360) * Math.PI / 180;
    var d = pub ? ((h32(sha(pub)) ^ h32(sha(l.de))) >>> 0) / 4294967296 : 0.5;
    return { x: Math.round(Math.cos(ang) * (300 + 700 * d)), y: Math.round(Math.sin(ang) * (300 + 700 * d)) };
  }
  function sitioCasa(pub, sha) {
    if (!pub) { return null; }
    var h = h32(sha('atlas.casa-sitio/1:' + pub)), a = (h % 360) * Math.PI / 180, r = 560 + (h >>> 9) % 160;
    return { x: Math.round(Math.cos(a) * r), y: Math.round(Math.sin(a) * r) };
  }
  function sitioNodo(nodo) { return nodo === 'nodo.0.hexelion' ? HEX : null; }   
    function despejado(e) {
    var c = [];
    (e.nodos || []).forEach(function (n) {
      var m = n.aparato.medidas, k = Object.keys(m).filter(function (x) { return m[x].estado === 'MEDIDO'; }).length;
      var s = sitioNodo(n.nodo);
      if (k && s) { c.push({ x: s.x, y: s.y, r: 380 + 160 * k, que: n.nodo }); }
    });
    var casa = sitioCasa(e.pub, e.sha);
    if (casa) { c.push({ x: casa.x, y: casa.y, r: 360, que: 'casa' }); }
    (e.lugares || []).forEach(function (l) {
      if ((e.luchados || {})[l.clave] || !l.npc) { var s = sitioLugar(l, e.sha, e.pub); c.push({ x: s.x, y: s.y, r: 200, que: l.clave }); }
    });
    return c;
  }
    function niebla(x, y, circ) {
    var m = 1;
    for (var i = 0; i < circ.length; i++) {
      var dx = x - circ[i].x, dy = y - circ[i].y, d = Math.sqrt(dx * dx + dy * dy) - circ[i].r;
      m = Math.min(m, Math.max(0, Math.min(1, (d + 90) / 90)));
    }
    return m;
  }
  function huella(circ) { return circ.map(function (c) { return c.x + ',' + c.y + ',' + c.r; }).join(';'); }

    var CLASES_ANCLA = ['enlace-rack', 'parte-cuerpo', 'prisma', 'eco-superficie'];
  function anclas(e) {
    var out = [], casa = sitioCasa(e.pub, e.sha);
    (e.nodos || []).forEach(function (n) {
      if (n.nodo === 'nodo.0.hexelion') { return; }
      var s = sitioNodo(n.nodo);
      if (!s) { return; }
      out.push({ id: 'rack:' + n.nodo, clase: 'enlace-rack', x: s.x, y: s.y, a: { x: HEX.x, y: HEX.y } });
    });
    if (casa) {
      out.push({ id: 'cuerpo:casa', clase: 'parte-cuerpo', x: casa.x, y: casa.y - 60, a: null });
      out.push({ id: 'prisma:casa', clase: 'prisma', x: casa.x + 60, y: casa.y, a: null });
    }
    out.push({ id: 'eco:hexelion', clase: 'eco-superficie', x: HEX.x, y: HEX.y - 90, a: null });
    return out;
  }

  var AtlasNiebla = { despejado: despejado, niebla: niebla, huella: huella, sitioLugar: sitioLugar, sitioCasa: sitioCasa,
                      sitioNodo: sitioNodo, HEX: HEX, ANILLO: ANILLO, anclas: anclas, CLASES_ANCLA: CLASES_ANCLA };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasNiebla; } else { raiz.AtlasNiebla = AtlasNiebla; }
})(this);
