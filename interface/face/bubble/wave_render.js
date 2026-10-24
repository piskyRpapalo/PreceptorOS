
(function (raiz) {
  'use strict';

  var G = raiz.AtlasGacha, CACHE = {}, NCACHE = 0;
  var V = raiz.AtlasValores || {};
  var F = V.fluidez || {};
  var TAU = Math.PI * 2;


  var MELT_CANVAS = null;
  var MELT_CTX = null;


  function initMeltCanvas(w, h) {
    if (MELT_CANVAS && MELT_CANVAS.width === w && MELT_CANVAS.height === h) {
      return;
    }
    var cv = raiz.document.createElement('canvas');
    cv.width = w; cv.height = h;
    MELT_CANVAS = cv;
    MELT_CTX = cv.getContext('2d');
  }


  function applyMelt(g, semilla) {
    if (!F.melt_alfa) return;

    var w = g.canvas.width;
    var h = g.canvas.height;
    initMeltCanvas(w, h);


    MELT_CTX.save();
    MELT_CTX.globalAlpha = F.melt_alfa || 0.93;


    var zoom = F.melt_zoom || 1.0005;
    var rot = F.melt_rotacion || 0.0001;
    var t = semilla ? (semilla % 10000) / 10000 : 0;

    MELT_CTX.translate(w/2, h/2);
    MELT_CTX.scale(1 + Math.sin(t * Math.PI * 2) * 0.0001, 1 + Math.sin(t * Math.PI * 2) * 0.0001);
    MELT_CTX.rotate(Math.sin(t * Math.PI * 2) * rot);
    MELT_CTX.translate(-w/2, -h/2);


    MELT_CTX.drawImage(g.canvas, 0, 0);
    MELT_CTX.restore();


    g.drawImage(MELT_CANVAS, 0, 0);
  }



  function colorVida(fraccion, base, armadura) {
    if (fraccion == null) fraccion = 1;
    var hueBase = F.vida_hue_base || 270;
    var hueCobre = F.vida_hue_cobre || 30;
    var lMax = F.escudo_lightness_base || 72, lMin = F.escudo_lightness_min || 40;
    var hue = hueBase + (hueCobre - hueBase) * (1 - fraccion);
    var escudo = armadura == null ? 1 : Math.max(0, Math.min(1, armadura / (F.escudo_ref || 24)));
    var lightness = lMin + (lMax - lMin) * escudo;
    return [Math.round(hue) % 360, 70, Math.round(lightness)];
  }


  function pulso(ms) {
    var S = raiz.AtlasSintesis, max = F.pulso_brillo_max;

    if (S && S.envolvente && S.receta) { var r = S.receta('pop', 0); return max && r ? max * S.envolvente(r, ms / 1000) / r.gan : 0; }
    var p = (V.sonidos || {}).pop;
    if (!p || !max || ms < 0 || ms >= p.dur * 1000) { return 0; }
    return max * Math.pow(0.0001 / p.gan, ms / (p.dur * 1000));
  }


  var BUFFERS = {};
  var BUFFER_CONFIG = {
    2: { escala: 1.0, anchoMax: null },
    1: { escala: 0.5, anchoMax: null },
    0: { escala: 0.25, anchoMax: 320 }
  };


  var DITHER_PATTERN = F.dither_patron || [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 13, 5, 15, 7];
  var DITHER_CANVAS = null;
  var DITHER_READY = false;

  function initDither() {
    if (DITHER_READY || !F.dither_on) return;
    var cv = raiz.document.createElement('canvas');
    cv.width = 4; cv.height = 4;
    var g = cv.getContext('2d');
    var imgData = g.createImageData(4, 4);
    for (var i = 0; i < 16; i++) {
      var val = DITHER_PATTERN[i] / 15;
      var idx = i * 4;
      imgData.data[idx] = imgData.data[idx+1] = imgData.data[idx+2] = Math.round(val * 255);
      imgData.data[idx+3] = 255;
    }
    g.putImageData(imgData, 0, 0);
    DITHER_CANVAS = cv;
    DITHER_READY = true;
  }


  function getBuffer(g, nivel) {
    nivel = nivel == null ? 2 : Math.max(0, Math.min(2, Math.floor(nivel)));
    var config = BUFFER_CONFIG[nivel];

    if (nivel === 2) {
      return g;
    }

    var key = 'buffer_' + nivel;
    if (!BUFFERS[key]) {
      var ancho = g.canvas.width;
      var alto = g.canvas.height;
      var escala = config.escala;
      var anchoBuffer = Math.min(config.anchoMax || ancho, Math.ceil(ancho * escala));
      var altoBuffer = Math.ceil(alto * escala);

      var cv = raiz.document.createElement('canvas');
      cv.width = anchoBuffer;
      cv.height = altoBuffer;
      BUFFERS[key] = cv.getContext('2d');
    }

    return BUFFERS[key];
  }


  function applyDither(g, nivel) {
    if (!F.dither_on || nivel >= 2) return;
    initDither();
    if (!DITHER_READY) return;

    var w = g.canvas.width;
    var h = g.canvas.height;
    var pattern = g.createPattern(DITHER_CANVAS, 'repeat');
    g.globalCompositeOperation = 'source-in';
    g.fillStyle = pattern;
    g.fillRect(0, 0, w, h);
    g.globalCompositeOperation = 'source-over';
  }


  function wobble(x, y, nivel) {
    if (nivel >= 2) return { x: x, y: y };
    var paso = F.paso_grid ? F.paso_grid[nivel] : [1, 2, 4][nivel];
    return { x: Math.round(x / paso) * paso, y: Math.round(y / paso) * paso };
  }


  function renderToReal(g, bufferG, nivel) {
    if (nivel >= 2) return;

    var bufferCanvas = bufferG.canvas;
    var realCanvas = g.canvas;


    if (F.dither_on && nivel < 2) {
      applyDither(bufferG, nivel);
    }


    g.imageSmoothingEnabled = false;
    g.drawImage(bufferCanvas, 0, 0, realCanvas.width, realCanvas.height);
    g.imageSmoothingEnabled = true;
  }


  function pulsoNota(f) {
    var hz = Math.abs(f) || 4;
    while (hz >= 6) { hz /= 2; }
    while (hz < 2) { hz *= 2; }
    return hz;
  }
  function limite(arm) {
    var l = 0;
    arm.forEach(function (h) { l += Math.max(Math.abs(h[1]), Math.abs(h[2])); });
    return Math.max(1, l);
  }

  function vivos(arm, o) {
    var t = o.t || 0, n = arm.length, c = o.crece == null ? 1 : o.crece, d = o.desafina || 0;
    return arm.map(function (h, j) {
      var peso = Math.max(0, Math.min(1, c * n - j)), late = o.respira === false ? 1 : 1 + 0.05 * Math.sin(t * 0.0011 * (j + 1) + j * 1.7);
      var tuerce = d ? ((j * 7 + 3) % 11 - 5) / 5 * d * 14 : 0;
      return [h[0], h[1] * peso * late, h[2] * peso * late, h[3] + tuerce];
    });
  }
  function puntos(arm, n) {
    var p = [];
    for (var i = 0; i <= n; i++) { p.push(G.punto(arm, i / n * TAU)); }
    return p;
  }
  function color(c, a) {
    if (typeof c === 'string') { return c; }
    return 'hsla(' + c[0] + ' ' + c[1] + '% ' + c[2] + '% / ' + (a == null ? 1 : a) + ')';
  }

  function trazo(g, P, x, y, k, cs, sn, ancho, variable) {
    var n = P.length - 1, med = 0, L = [];
    for (var i = 1; i <= n; i++) { var dx = P[i][0] - P[i - 1][0], dy = P[i][1] - P[i - 1][1]; L.push(Math.sqrt(dx * dx + dy * dy)); med += L[i - 1]; }
    med = med / n || 1;
    function px(p) { return x + (p[0] * cs - p[1] * sn) * k; }
    function py(p) { return y - (p[0] * sn + p[1] * cs) * k; }
    if (!variable) {
      g.lineWidth = ancho; g.beginPath();
      for (var j = 0; j <= n; j++) { g[j ? 'lineTo' : 'moveTo'](px(P[j]), py(P[j])); }
      g.stroke(); return;
    }
    for (var s = 1; s <= n; s++) {
      g.lineWidth = ancho * Math.max(0.45, Math.min(1.7, 1.35 - (L[s - 1] / med - 1) * 0.5));
      g.beginPath(); g.moveTo(px(P[s - 1]), py(P[s - 1])); g.lineTo(px(P[s]), py(P[s])); g.stroke();
    }
  }

  function dibuja(g, arm, x, y, r, o) {
    o = o || {};
    var q = o.calidad == null ? 2 : o.calidad;
    var nivel = Math.max(0, Math.min(2, Math.floor(q)));


    var bufferG = g, isBuffer = false;


    var targetG = isBuffer ? bufferG : g;

    var A = vivos(arm, o), k = r / limite(arm) * (o.escala == null ? 1 : o.escala);
    var n = q >= 2 ? 220 : q >= 1 ? 140 : 80, P = puntos(A, n), giro = o.giro || 0, gr = o.grosor || 2, alfa = o.alfa == null ? 1 : o.alfa;
    var c = o.color || [270, 70, 72], brillo = o.brillo == null ? 0.8 : o.brillo;


    targetG.save(); targetG.lineJoin = 'round'; targetG.lineCap = 'round';
    targetG.globalCompositeOperation = 'lighter';

    var est = q >= 1 ? (o.estela || 0) : 0;
    for (var e = est; e >= 1; e--) {
      var ge = giro - e * (o.pasoEstela || 0.06);
      targetG.strokeStyle = color(c, alfa * 0.18 * (1 - e / (est + 1)));
      trazo(targetG, P, x, y, k, Math.cos(ge), Math.sin(ge), gr * 0.8, false);
    }
    var cs = Math.cos(giro), sn = Math.sin(giro);
    if (brillo > 0 && q >= 1) {
      targetG.strokeStyle = color(c, alfa * 0.07 * brillo); trazo(targetG, P, x, y, k, cs, sn, gr * 7, false);
      targetG.strokeStyle = color(c, alfa * 0.16 * brillo); trazo(targetG, P, x, y, k, cs, sn, gr * 3.2, false);
    }
    targetG.strokeStyle = color(c, alfa); trazo(targetG, P, x, y, k, cs, sn, gr, q >= 2);
    if (o.face) { drawFace(g, x, y, r, o); }
    if (q >= 1) {
      var blanco = typeof c === 'string' ? 'rgba(255,255,255,' + 0.35 * alfa + ')' : color([c[0], c[1] * 0.4, 92], 0.35 * alfa);
      targetG.strokeStyle = blanco; trazo(targetG, P, x, y, k, cs, sn, Math.max(0.6, gr * 0.35), false);
    }
    targetG.restore();


    if (isBuffer) {
      renderToReal(g, bufferG, nivel);
    }
  }


  function drawFace(g, x, y, r, o) {
    o = o || {};
    var fr = Math.max(2, r * 0.16), ex = r * 0.34, ey = r * 0.1;
    var palette = raiz.AtlasComicTokens.NEUTRAL, alpha = g.globalAlpha;
    g.save();
    g.strokeStyle = palette.ink;
    g.fillStyle = palette.paper;
    [-1, 1].forEach(function (s) {
      g.beginPath(); g.arc(x + s * ex, y - ey, fr, 0, 2 * Math.PI);
      g.globalAlpha = alpha * 0.9; g.fill(); g.globalAlpha = alpha * 0.85; g.stroke();
      g.beginPath(); g.arc(x + s * ex, y - ey + fr * 0.15, fr * 0.4, 0, 2 * Math.PI);
      g.globalAlpha = alpha * 0.95; g.fillStyle = palette.ink; g.fill(); g.fillStyle = palette.paper;
    });
    g.beginPath(); g.arc(x, y + r * 0.22, r * 0.3, 0.15 * Math.PI, 0.85 * Math.PI);
    g.globalAlpha = alpha * 0.85; g.lineWidth = Math.max(1, fr * 0.5); g.stroke();
    g.restore();
  }

  function sprite(arm, r, c, clave, dpr) {
    var key = clave + ':' + Math.round(r) + ':' + (dpr || 1);
    if (CACHE[key]) { return CACHE[key]; }
    if (NCACHE > 120) { CACHE = {}; NCACHE = 0; }
    var lado = Math.ceil(r * 2.6), cv = raiz.document.createElement('canvas');
    cv.width = cv.height = lado;
    dibuja(cv.getContext('2d'), arm, lado / 2, lado / 2, r, { color: c, grosor: Math.max(1.2, r / 14), brillo: 1, respira: false, calidad: 2 });
    CACHE[key] = cv; NCACHE++;
    return cv;
  }
  function pegaSprite(g, cv, x, y) { g.drawImage(cv, x - cv.width / 2, y - cv.height / 2); }

  var TONOS = [[35, 80, 62], [140, 55, 58], [275, 65, 72], [205, 30, 74]];
  function tono(t) { return TONOS[G.caracter(t).color]; }

  function riqueza(arm) { return arm.filter(function (h) { return Math.abs(h[1]) + Math.abs(h[2]) > 0; }).length; }


  function medidor() {
    var ult = null, media = 16.7, n = 0;
    return {
      cuadro: function (ts) { if (ult !== null) { var d = Math.min(200, ts - ult); media = media * 0.95 + d * 0.05; n++; } ult = ts; },
      fps: function () { return n > 30 ? Math.round(1000 / media) : null; },
      nivel: function (q) { var f = n > 60 ? 1000 / media : 60; return f < 40 ? 0 : f < 50 ? Math.min(q, 1) : q; }
    };
  }

  raiz.AtlasOnda = {
    dibuja: dibuja, drawFace: drawFace, pulsoNota: pulsoNota, sprite: sprite, pegaSprite: pegaSprite, tono: tono, riqueza: riqueza, medidor: medidor, limite: limite,

    applyMelt: applyMelt,

    colorVida: colorVida,
    pulso: pulso,

    buffer: getBuffer,
    getBuffer: getBuffer,
    applyDither: applyDither,
    wobble: wobble,
    renderToReal: renderToReal
  };
})(this);
