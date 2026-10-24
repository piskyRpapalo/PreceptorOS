(function (root) {
  'use strict';
  var B = root.AtlasBubble, P = root.AtlasComicAtoms, C = root.AtlasCamara, N = root.AtlasNiebla, Z = root.AtlasMapZoom, Wd = root.PreceptorWorld;
  var root2 = Math.SQRT2;

  function create(canvas, win, skin) {
    var terrain = null, standing = null, names = null, fog = null, fogKey = '', zoom = Z ? Z.crea(win) : { factor: function () { return 1; } };
    var view = { e: 0, f: 0, z: 1, W: 0, H: 0, k: 1 };
    var minis = {}, nminis = 0, composite = { crab: 1, wanderer: 1 };
    function dpr() { return Math.min(2, root.devicePixelRatio || 1); }
    function band(n) { return B.band(n); }
    function compileAll() {
      terrain = [Wd.seaFrame(skin), Wd.islesFrame(skin, 0), Wd.islesFrame(skin, 1), Wd.islesFrame(skin, 2), Wd.islesFrame(skin, 3)].map(function (f) { return B.compile(f); });
      standing = Wd.standFrame(skin);
      names = Wd.namesFrame(skin);
    }

    function frameView(at, whole) {
      var W = root.innerWidth, H = root.innerHeight, r = win.getBoundingClientRect(), z, cam;
      var base = whole ? Math.min(r.width / 1110, r.height / 640) : r.width / 330;
      z = base * (whole ? 1 : zoom.factor());
      cam = whole ? { x: Wd.worldSize / 2, y: Wd.worldSize / 2 } : { x: at[0], y: at[1] };
      var o = C.aPantalla(cam, W, H, z, 0, 0);
      view = { W: W, H: H, z: z, cam: cam, k: 1, e: o[0] + (r.left + r.width / 2 - W / 2), f: o[1] + (r.top + r.height / 2 - H / 2), ox: r.left + r.width / 2 - W / 2, oy: r.top + r.height / 2 - H / 2 };
      return view;
    }

    function anchorOf(it) {
      if (typeof it.x === 'number' && typeof it.y === 'number') { return [it.x, it.y]; }
      if (Array.isArray(it.x) && Array.isArray(it.y)) { return [(it.x[0] + it.x[1]) / 2, (it.y[0] + it.y[1]) / 2]; }
      return null;
    }
    function shift(it, a) {
      var o = {}, k;
      for (k in it) { if (Object.prototype.hasOwnProperty.call(it, k)) { o[k] = it[k]; } }
      if (typeof o.x === 'number') { o.x -= a[0]; o.y -= a[1]; }
      else if (Array.isArray(o.x)) { o.x = [o.x[0] - a[0], o.x[1] - a[0]]; o.y = [o.y[0] - a[1], o.y[1] - a[1]]; }
      if (Array.isArray(o.pts)) { o.pts = o.pts.map(function (q) { return [q[0] - a[0], q[1] - a[1]]; }); }
      return o;
    }
    function mini(items, seed) {
      var key = JSON.stringify(items) + seed;
      if (!minis[key]) {
        if (nminis > 300) { minis = {}; nminis = 0; }
        minis[key] = B.compile({ v: 'preceptoros.bubble/1', id: seed, t: 0, atoms: [{ k: 'piece', r: 'piece', i: items }] }); nminis++;
      }
      return minis[key];
    }
    function upright(ctx, frame, d, dashed) {
      var v = view;
      frame.atoms.forEach(function (atom) {
        var list = atom.i || [], free = list.filter(function (it) { return !anchorOf(it); });
        if (free.length) {
          ctx.setTransform(d * v.z, 0, 0, d * v.z, d * v.e, d * v.f);
          ctx.setLineDash(dashed ? [16 / v.z * v.k, 13 / v.z * v.k] : []);
          P.paint(ctx, B.compile({ v: 'preceptoros.bubble/1', id: frame.id, t: 0, atoms: [{ k: atom.k, r: atom.r, i: free }] }));
          ctx.setLineDash([]);
        }
        var fixed = list.filter(anchorOf), groups = composite[atom.k] && fixed.length ? [fixed] : fixed.map(function (it) { return [it]; });
        groups.forEach(function (g) {
          var a = anchorOf(g[0]);
          ctx.setTransform(d * v.k, 0, 0, d * v.k, d * (v.e + v.z * a[0]), d * (v.f + v.z * a[1]));
          P.paint(ctx, mini(g.map(function (it) { return shift(it, a); }), frame.id + ':' + atom.k));
        });
      });
    }
    function toScreen(x, y) { var p = Wd.iso(x, y); return [view.e + view.z * p[0], view.f + view.z * p[1]]; }

    function toWorld(sx, sy) { return C.aMundo(view.cam, view.W, view.H, view.z, sx - view.ox, sy - view.oy); }

    function brume(ctx, circles, d) {
      var s = 10, w = Math.ceil(view.W / s), h = Math.ceil(view.H / s), key = JSON.stringify(circles) + [view.e, view.f, view.z, w, h].join(':');
      if (key !== fogKey) {
        fogKey = key;
        fog = fog || root.document.createElement('canvas');
        fog.width = w; fog.height = h;
        var g = fog.getContext('2d'), im = g.createImageData(w, h), rgb = rgbOf(band(skin.brume)), x, y, k = 0, q, v;
        for (y = 0; y < h; y++) {
          for (x = 0; x < w; x++) {
            q = toWorld(x * s + s / 2, y * s + s / 2);
            v = N.niebla(q[0], q[1], circles);
            im.data[k++] = rgb[0]; im.data[k++] = rgb[1]; im.data[k++] = rgb[2]; im.data[k++] = Math.round(v * 0.66 * 255);
          }
        }
        g.putImageData(im, 0, 0);
      }
      ctx.setTransform(d, 0, 0, d, 0, 0);
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(fog, 0, 0, w * s, h * s);
    }
    function rgbOf(c) { var g = root.document.createElement('canvas').getContext('2d'); g.fillStyle = c; var t = g.fillStyle; return t.charAt(0) === '#' ? [1, 3, 5].map(function (i) { return parseInt(t.slice(i, i + 2), 16); }) : t.match(/[\d.]+/g).slice(0, 3).map(Number); }

    function paint(state, whole) {
      if (!terrain) { compileAll(); }
      var v = frameView(state.at, whole), d = dpr(), ctx = canvas.getContext('2d'), m = C.matriz(v.z), i;
      if (canvas.width !== Math.round(v.W * d) || canvas.height !== Math.round(v.H * d)) { canvas.width = Math.round(v.W * d); canvas.height = Math.round(v.H * d); }
      ctx.setTransform(d, 0, 0, d, 0, 0);
      ctx.fillStyle = band(skin.sea);
      ctx.fillRect(0, 0, v.W, v.H);
      ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.setTransform(d * m[0], d * m[1], d * m[2], d * m[3], d * v.e, d * v.f);
      for (i = 0; i < terrain.length; i++) { P.paint(ctx, terrain[i]); }
      upright(ctx, standing, d, false);
      if (state.cast) { upright(ctx, state.cast, d, false); }
      upright(ctx, names, d, false);
      brume(ctx, state.circles, d);
      upright(ctx, state.frame, d, true);
      if (state.extra) { ctx.setTransform(d, 0, 0, d, 0, 0); state.extra(ctx, toScreen, v.k); }
      return v;
    }

    return { paint: paint, toWorld: toWorld, toScreen: toScreen, view: function () { return view; } };
  }

  root.PreceptorPaint = Object.freeze({ create: create });
})(window);
