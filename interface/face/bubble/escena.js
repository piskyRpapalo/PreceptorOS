
(function (raiz) {
  'use strict';

  var G=raiz.AtlasGacha,O=raiz.AtlasOnda||{},F=(raiz.AtlasValores&&raiz.AtlasValores.fluidez)||{};
  var TONOS=['hsl(35 75% 58%)','hsl(140 45% 55%)','hsl(275 55% 68%)','hsl(210 12% 68%)'];
  var BRILLO={normal:0,magico:5,raro:10,unico:16},EVENTO_MS=560,HONDO=[[7,12,24],[12,24,44],[20,42,70],[34,70,104]],MC=null,MCX=null;
  function initMC(w,h){if(!MC||MC.width!==w||MC.height!==h){var c=raiz.document.createElement('canvas');c.width=w;c.height=h;MC=c;MCX=c.getContext('2d')}}
  function applyMelt(g,s){if(quieto||!F.melt_alfa)return;initMC(g.canvas.width,g.canvas.height);MCX.save();MCX.globalAlpha=F.melt_alfa||.93;var t=s?s%10000/10000:0,r=F.melt_rotacion||.0001,w=g.canvas.width/2,h=g.canvas.height/2;MCX.translate(w,h);MCX.scale(1+Math.sin(t*6.2832)*.0001,1+Math.sin(t*6.2832)*.0001);MCX.rotate(Math.sin(t*6.2832)*r);MCX.translate(-w,-h);MCX.drawImage(g.canvas,0,0);MCX.restore();g.drawImage(MC,0,0)}
  function hash(x,y,s){
    var h = Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(s, 974634719);
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  }
  function ruido(x, y, s) {
    var xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi;
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
    var a = hash(xi, yi, s), b = hash(xi + 1, yi, s), c = hash(xi, yi + 1, s), d = hash(xi + 1, yi + 1, s);
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy;
  }
  function fbm(x, y, s) { return ruido(x, y, s) * 0.55 + ruido(x * 2.1, y * 2.1, s + 7) * 0.3 + ruido(x * 4.3, y * 4.3, s + 13) * 0.15; }

  function textura(w, h, f, pal) {
    var c = raiz.document.createElement('canvas'); c.width = w; c.height = h;
    var g = c.getContext('2d'), im = g.createImageData(w, h), n = pal.length - 1, e = new Float32Array(w * h), x, y;
    for (y = 0; y < h; y++) { for (x = 0; x < w; x++) { e[y * w + x] = f(x, y) * n; } }
    for (y = 0; y < h; y++) {
      for (x = 0; x < w; x++) {
        var i = y * w + x, v = e[i], q = Math.max(0, Math.min(n, Math.round(v))), d = (v - q) / 8, p = pal[q];
        [[1, 0], [2, 0], [-1, 1], [0, 1], [1, 1], [0, 2]].forEach(function (o) {
          var X = x + o[0], Y = y + o[1];
          if (X >= 0 && X < w && Y < h) { e[Y * w + X] += d; }
        });
        if (p) { im.data.set([p[0], p[1], p[2], 255], i * 4); }
      }
    }
    g.putImageData(im, 0, 0);
    return c;
  }
  function pega(g, tex, W, H) { g.imageSmoothingEnabled = false; g.drawImage(tex, 0, 0, W, H); }

  function limite(arm) {
    var l = 0;
    arm.forEach(function (h) { l += Math.max(Math.abs(h[1]), Math.abs(h[2])); });
    return Math.max(1, l);
  }

  function afina(arm, d, t) {
    if (!d) { return arm; }
    return arm.map(function (h, j) {
      var tuerce = ((j * 7 + 3) % 11 - 5) / 5, estira = 1 + d * ((j * 5 + 1) % 7 - 3) * 0.14;
      return [h[0], h[1] * estira, h[2] * (2 - estira), h[3] + d * tuerce * 14 + Math.sin(t * 0.004 + j) * d * 3];
    });
  }
  function figura(g,a,x,y,r,o){var k=r/limite(a)*(o.escala==null?1:o.escala),c=Math.cos(o.giro||0),s=Math.sin(o.giro||0),n=o.puntos||120,d=o.desafina||0,A=afina(a,d,o.t||0),z=d*r*.07,f=o.color;if(o.vidaFraccion!=null&&O.colorVida)f=O.colorVida(o.vidaFraccion,o.color,o.arm);g.save();g.globalAlpha=o.alfa==null?1:o.alfa;g.strokeStyle=f;g.lineWidth=o.grosor||2;g.lineJoin='round';o.brillo&&(g.shadowColor=f,g.shadowBlur=o.brillo);g.beginPath();for(var i=0;i<=n;i++){var u=i/n*6.2832,p=G.punto(A,u),Z=z*Math.sin(u*13+(o.t||0)*.01),px=p[0]*k+Z*Math.cos(u),py=p[1]*k+Z*Math.sin(u);g[i?'lineTo':'moveTo'](x+px*c-py*s,y-(px*s+py*c))}g.stroke();g.restore()}
  function tono(t) { return TONOS[G.caracter(t).color]; }

  function rapidez(v) { return 'hsl(' + Math.round(210 - Math.max(0, Math.min(1, (v - 3) / 10)) * 185) + ' 80% 62%)'; }
  function mini(lienzo, t, color) {
    var g = lienzo.getContext('2d'), w = lienzo.width;
    g.clearRect(0, 0, w, lienzo.height);
    figura(g, G.espectro(t), w / 2, lienzo.height / 2, w * 0.42, { color: color || tono(t), grosor: Math.max(1.2, w / 60),
                                                               brillo: BRILLO[t.rareza] * w / 120 });
  }
  function unidades(tropas, lado) {
    return tropas.map(function (x, i) {
      var t = G.tirada(x.semilla, x.tc);
      return { t: t, lado: lado, i: i, vida: t.stats.vida, max: t.stats.vida, vel: t.stats.velocidad, arm:t.stats.armadura,
               masa: 1 + (t.stats.inercia || 0) / 8, color: tono(t), brillo: BRILLO[t.rareza], muere: null, flash: 0,
               tiembla: null, x: 0, y: 0, hx: 0, hy: 0, vx: 0, vy: 0, r: 10 };
    });
  }


  function escena(lienzo, def, asa, combate, op) {
    op = op || {};
    var g = lienzo.getContext('2d'), U = [unidades(def, 0), unidades(asa, 1)], ev = combate.registro;
    var todos = U[0].concat(U[1]), vt = 0, ultimo = null, vel = 1, hechos = 0, raf = 0, acabado = false, vivo = true;
    var pops = [], chispas = [], ondas = [], ronda = 0, dpr = raiz.devicePixelRatio || 1, finVt = 0, fondo = null, fw = 0;
    var col = op.colores || {}, quieto = !!op.quieto;

    function mide() {
      var w = Math.max(200, lienzo.clientWidth || 320), h = Math.round(Math.min(440, Math.max(280, w * 0.75)));
      if (lienzo.width !== Math.round(w * dpr)) { lienzo.width = Math.round(w * dpr); }
      if (lienzo.height !== Math.round(h * dpr)) { lienzo.height = Math.round(h * dpr); lienzo.style.height = h + 'px'; }
      var W = lienzo.width, H = lienzo.height;
      if (fw !== W) {
        fw = W;
        var s = Math.round(ev.length + U[0].length * 31);
        fondo = textura(Math.ceil(W / (3 * dpr)), Math.ceil(H / (3 * dpr)), function (x, y) {
          return Math.min(1, fbm(x / 22, y / 14, s) * 0.8 + y / H * dpr * 0.6);
        }, HONDO);
      }
      [0, 1].forEach(function (l) {
        var n = U[l].length, paso = H / (n + 1);
        U[l].forEach(function (u, i) {
          var fila = n > 3 ? (i % 2 ? 0.07 : -0.02) : 0;
          u.hx = W * (l ? 0.2 + fila : 0.8 - fila); u.hy = paso * (i + 1) + H * 0.03;
          if (!u.x) { u.x = u.hx; u.y = u.hy; }
          u.r = Math.min(W * 0.09, paso * 0.44, 66 * dpr);
        });
      });
    }
    function impacta(e, conEfectos) {
      var a = U[e[1]][e[2]], t = U[1 - e[1]][e[3]];
      ronda = e[0];
      if (e[4] < 0) {
        if (conEfectos) { pops.push({ x: t.x, y: t.y - t.r, txt: op.fallo || 'miss', c: col.fallo || '#9aa', v: vt }); }
        return;
      }
      t.vida = Math.max(0, t.vida - e[4]);
      if (!conEfectos) { if (!t.vida) { t.muere = -1e9; } return; }
      t.flash = 1; t.tiembla = vt;

      var dx = t.x - a.x, dy = t.y - a.y, L = Math.hypot(dx, dy) || 1, f = 9 * dpr * Math.min(3, e[4] / 4) / t.masa;
      t.vx += dx / L * f; t.vy += dy / L * f;
      ondas.push({ x: t.x, y: t.y, r: t.r, c: rapidez(a.vel), v: vt });
      pops.push({ x: t.x, y: t.y - t.r, txt: '-' + e[4], c: col.dano || a.color, v: vt });
      if (op.sonido) { op.sonido(t.vida ? 'golpe' : 'cae', a.t); }
      if (!t.vida) {
        t.muere = vt;
        for (var i = 0; i < 30; i++) {
          var p = G.punto(t.t.armonicos, i / 30 * 2 * Math.PI), k = t.r / limite(t.t.armonicos);
          chispas.push({ x: t.x + p[0] * k, y: t.y - p[1] * k, vx: p[0] * k * 0.004, vy: -p[1] * k * 0.004, c: t.color, v: vt });
        }
      }
    }
    function avanza() {
      var k = Math.min(ev.length, Math.floor(vt / EVENTO_MS + 0.5));
      while (hechos < k) { impacta(ev[hechos], !quieto); hechos++; }
      if (!acabado && hechos >= ev.length && vt > ev.length * EVENTO_MS + 800) {
        acabado = true; finVt = vt;
        if (op.sonido) { op.sonido(combate.gana === 'asalto' ? 'gana' : 'pierde'); }
        if (op.alFin) { op.alFin(combate); }
      }
    }

    function mueve(e, fase, dt, t) {
      todos.forEach(function (u, idx) {
        var tx = u.hx + Math.sin(t * 0.0007 + idx * 1.7) * u.r * 0.35, ty = u.hy + Math.cos(t * 0.0009 + idx) * u.r * 0.25;
        if (e && e[1] === u.lado && e[2] === u.i && fase < 0.5) {
          var o = U[1 - e[1]][e[3]]; tx += (o.x - u.x) * 0.3; ty += (o.y - u.y) * 0.3;
        }
        var k = dt / 16, m = u.masa;
        u.vx = (u.vx + (tx - u.x) * 0.05 * k / m) * Math.pow(0.86, k); u.vy = (u.vy + (ty - u.y) * 0.05 * k / m) * Math.pow(0.86, k);
        u.x += u.vx * k; u.y += u.vy * k;
      });
    }

    function proyectil(a, b, s, t) {
      var fa = Math.abs(a.t.armonicos[0][0]) % 3 + 1, fb = Math.abs((a.t.armonicos[1] || a.t.armonicos[0])[0]) % 4 + 2;
      var R = a.r * 0.32, c = rapidez(a.vel);
      g.save(); g.strokeStyle = c; g.lineWidth = 1.5 * dpr; g.shadowColor = c; g.shadowBlur = 10 * dpr;
      for (var e = 0; e < 4; e++) {
        var q = Math.max(0, s - e * 0.07), cx = a.x + (b.x - a.x) * q, cy = a.y + (b.y - a.y) * q - Math.sin(Math.PI * q) * a.r * 0.8;
        g.globalAlpha = 1 - e * 0.24; g.beginPath();
        for (var i = 0; i <= 48; i++) {
          var u = i / 48 * 2 * Math.PI, rr = R * (1 - e * 0.18);
          g[i ? 'lineTo' : 'moveTo'](cx + Math.sin(fa * u + t * 0.006) * rr, cy + Math.sin(fb * u) * rr);
        }
        g.stroke();
      }
      g.restore();
    }
    function frente(W, H, t) {
      var v = [0, 1].map(function (l) { return U[l].reduce(function (s, u) { return s + u.vida / u.max; }, 0) / U[l].length; });
      var x0 = W * (0.5 + (v[1] - v[0]) * 0.3), yo = op.yo == null ? 1 : op.yo;
      [0, 1].forEach(function (k) {
        g.strokeStyle = k === yo ? (col.tuya || '#c98a4b') : (col.suya || '#8b5cf6'); g.lineWidth = 1.4 * dpr; g.beginPath();
        for (var y = 0; y <= H; y += 6 * dpr) {
          g[y ? 'lineTo' : 'moveTo'](x0 + Math.sin(y / (16 * dpr) + t * 0.004 * (k ? 1 : -1)) * (5 + 4 * k) * dpr, y);
        }
        g.stroke();
      });
    }
    function pinta(ts,dt){var W=lienzo.width,H=lienzo.height,t=quieto?0:ts;quieto?g.clearRect(0,0,W,H):applyMelt(g,semilla);fondo&&pega(g,fondo,W,H);
      frente(W, H, t);
      var cur = Math.floor(vt / EVENTO_MS), e = cur < ev.length ? ev[cur] : null, fase = (vt % EVENTO_MS) / EVENTO_MS;
      if (!quieto) { mueve(e, fase, dt, t); } else { todos.forEach(function (u) { u.x = u.hx; u.y = u.hy; }); }
      todos.forEach(function (u, idx) {
        var m = u.muere === null ? 1 : Math.max(0, 1 - (vt - u.muere) / 600);
        if (m <= 0) { return; }
        var dx = 0;
        if (!quieto && u.tiembla !== null && vt - u.tiembla < 260) { dx = Math.sin(vt * 0.12) * 4 * dpr * (1 - (vt - u.tiembla) / 260); }
        var gira=quieto?0:t*.00045*(1+u.vel/12)*(u.lado?1:-1)*(acabado&&u.vida?3:1),respira=quieto?1:1+.035*Math.sin(t*.002+idx),fo=u.flash*(1+Math.sin(t*.002*Math.PI*(O.pulsoNota?O.pulsoNota((((raiz.AtlasValores||{}).sonidos||{}).pop||{}).f||660):4))*.5);
        figura(g,G.lod(u.t),u.x+dx,u.y,u.r,{color:u.color,giro:gira,alfa:m,grosor:1.8*dpr,brillo:u.brillo+fo*18*dpr,t:t,desafina: Math.min(1, (1 - u.vida / u.max)*.8+u.flash*.35),escala:respira*(.4+.6*m),vidaFraccion:u.vida/u.max,arm:u.arm});
        if (raiz.AtlasEscuadron) { raiz.AtlasEscuadron.pinta(g, u, { r: u.r, dpr: dpr, giro: gira, alfa: m, t: t, quieto: quieto }); }
        u.flash = Math.max(0, u.flash - 0.05);
      });
      if (!quieto && e && fase > 0.3 && fase < 0.8) { proyectil(U[e[1]][e[2]], U[1 - e[1]][e[3]], (fase - 0.3) / 0.5, t); }
      ondas = ondas.filter(function (o) { return vt - o.v < 450; });
      ondas.forEach(function (o) {
        var d = (vt - o.v) / 450;
        g.strokeStyle = o.c; g.lineWidth=(1-d)*4*dpr*(1+(O.pulso?O.pulso(vt-o.v):0)); g.beginPath(); g.arc(o.x, o.y, o.r * (0.6 + d * 1.2), 0, 2 * Math.PI); g.stroke();
      });
      chispas = chispas.filter(function (c) { return vt - c.v < 900; });
      chispas.forEach(function (c) {
        var d = vt - c.v; g.globalAlpha = 1 - d / 900; g.fillStyle = c.c;
        g.fillRect(c.x + c.vx * d, c.y + c.vy * d, 2 * dpr, 2 * dpr);
      });
      g.globalAlpha = 1;
      g.font = '700 ' + Math.round(15 * dpr) + 'px ui-monospace, monospace'; g.textAlign = 'center';
      pops = pops.filter(function (p) { return vt - p.v < 800; });
      pops.forEach(function (p) {
        var d = vt - p.v; g.globalAlpha = 1 - d / 800; g.fillStyle = p.c; g.fillText(p.txt, p.x, p.y - d * 0.04 * dpr);
      });
      g.globalAlpha = 1; g.fillStyle = col.texto || '#ccc';
      if (ronda && op.ronda) { g.fillText(op.ronda.replace('{r}', ronda), W / 2, 20 * dpr); }
      if (acabado && op.letrero) {
        var l = op.letrero(combate), a2 = quieto ? 1 : Math.min(1, (vt - finVt) / 500);
        g.save(); g.globalAlpha = a2; g.fillStyle = 'rgba(7,12,24,.72)'; g.fillRect(0, H / 2 - 30 * dpr, W, 56 * dpr);
        g.fillStyle = l.color || col.texto || '#ddd';
        g.font = '700 ' + Math.round(Math.min(W / 8, 46 * dpr)) + 'px ui-monospace, monospace';
        g.fillText(l.texto, W / 2, H / 2 + 12 * dpr); g.restore();
      }
    }
    function cuadro(ts) {
      if (!vivo) { return; }
      raf = raiz.requestAnimationFrame(cuadro);
      var visible = lienzo.offsetParent !== null && !raiz.document.hidden;
      var dt = ultimo === null ? 16 : Math.min(100, ts - ultimo);
      ultimo = ts;
      if (!visible) { return; }
      mide();
      if (!acabado || !quieto) { vt += quieto ? 1e9 : dt * vel; }
      avanza();
      pinta(ts, dt);
    }
    function reinicia() {
      todos.forEach(function (u) { u.vida = u.max; u.muere = null; u.flash = 0; u.tiembla = null; u.vx = u.vy = 0; });
      vt = 0; hechos = 0; acabado = false; pops = []; chispas = []; ondas = []; ronda = 0;
    }
    raf = raiz.requestAnimationFrame(cuadro);
    return {
      velocidad: function (v) { vel = v; },
      salta: function () {
        while (hechos < ev.length) { impacta(ev[hechos], false); hechos++; }
        vt = Math.max(vt, ev.length * EVENTO_MS + 801); pops = []; chispas = []; ondas = [];
      },
      otra: reinicia,
      para: function () { vivo = false; raiz.cancelAnimationFrame(raf); }
    };
  }

  var AtlasEscena = { TONOS: TONOS, BRILLO: BRILLO, EVENTO_MS: EVENTO_MS, figura: figura, mini: mini, tono: tono, escena: escena,
                      textura: textura, pega: pega, fbm: fbm, hash: hash, rapidez: rapidez };
  raiz.AtlasEscena = AtlasEscena;
})(this);
