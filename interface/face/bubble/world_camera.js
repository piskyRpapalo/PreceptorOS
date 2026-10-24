(function (raiz) {
  'use strict';
    var I = (typeof module === 'object' && module.exports) ? require('./isometric_floor_projection.js') : raiz.IsometricFloor;
  var R2 = Math.SQRT2;

  var MARGEN = 70, FRENO = 0.9, REBOTE = 0.35;

  function crea(inicio) { return { x: inicio.x, y: inicio.y, vx: 0, vy: 0, choco: 0 }; }
    function dentro(x, y, circ) {
    var mejor = null, md = Infinity;
    for (var i = 0; i < circ.length; i++) {
      var c = circ[i], R = Math.max(1, c.r - MARGEN), dx = x - c.x, dy = y - c.y, d = Math.sqrt(dx * dx + dy * dy);
      if (d <= R) { return { x: x, y: y, fuera: false }; }
      if (d - R < md) { md = d - R; mejor = { x: c.x + dx / d * R, y: c.y + dy / d * R, fuera: true, nx: dx / d, ny: dy / d }; }
    }
    return mejor || { x: x, y: y, fuera: false };
  }
  function limita(cam, circ) {
    var p = dentro(cam.x, cam.y, circ);
    if (!p.fuera) { return false; }
    cam.x = p.x; cam.y = p.y;
    var vn = cam.vx * p.nx + cam.vy * p.ny;
    if (vn > 0) { cam.vx -= (1 + REBOTE) * vn * p.nx; cam.vy -= (1 + REBOTE) * vn * p.ny; }
    cam.choco++;
    return true;
  }
    function arrastra(cam, dx, dy, circ, quieto) {
    cam.x -= dx; cam.y -= dy;
    if (quieto) { cam.vx = 0; cam.vy = 0; } else { cam.vx = -dx; cam.vy = -dy; }
    return limita(cam, circ);
  }
    function empuja(cam, dx, dy, circ, quieto) {
    if (quieto) { cam.x += dx; cam.y += dy; return limita(cam, circ); }
    cam.vx += dx * (1 - FRENO); cam.vy += dy * (1 - FRENO);
    return false;
  }
    function planea(cam, x, y, circ, quieto) { cam.vx = 0; cam.vy = 0; return empuja(cam, x - cam.x, y - cam.y, circ, quieto); }
    function paso(cam, k, circ) {
    if (Math.abs(cam.vx) < 0.01 && Math.abs(cam.vy) < 0.01) { cam.vx = 0; cam.vy = 0; return false; }
    cam.x += cam.vx * k; cam.y += cam.vy * k;
    var f = Math.pow(FRENO, k); cam.vx *= f; cam.vy *= f;
    return limita(cam, circ);
  }
      function aPantalla(cam, W, H, z, x, y) { var p = I.proyecta(x - cam.x, y - cam.y, R2 * z); return [p.x + W / 2, p.y + H / 2]; }
  function aMundoDelta(dx, dy, z) { var q = I.aCelda(dx, dy, R2 * z); return [q.col, q.fila]; }
  function aMundo(cam, W, H, z, sx, sy) { var d = aMundoDelta(sx - W / 2, sy - H / 2, z); return [d[0] + cam.x, d[1] + cam.y]; }
    function vista(cam, W, H, z) {
    var e = [aMundo(cam, W, H, z, 0, 0), aMundo(cam, W, H, z, W, 0), aMundo(cam, W, H, z, 0, H), aMundo(cam, W, H, z, W, H)];
    var xs = e.map(function (q) { return q[0]; }), ys = e.map(function (q) { return q[1]; });
    return { x0: Math.min.apply(null, xs), y0: Math.min.apply(null, ys), x1: Math.max.apply(null, xs), y1: Math.max.apply(null, ys), z: z };
  }
    function matriz(z) { var k = z / R2; return [k, k / 2, -k, k / 2]; }

  var AtlasCamara = { crea: crea, arrastra: arrastra, empuja: empuja, planea: planea, paso: paso, limita: limita, dentro: dentro,
                      aMundoDelta: aMundoDelta, matriz: matriz,
                      vista: vista, aPantalla: aPantalla, aMundo: aMundo, MARGEN: MARGEN };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasCamara; } else { raiz.AtlasCamara = AtlasCamara; }
})(this);
