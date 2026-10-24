(function (root) {
  'use strict';
  var B = root.AtlasBubble, P = root.AtlasComicAtoms, C = root.AtlasCamara, N = root.AtlasNiebla, Z = root.AtlasMapZoom, Wd = root.PreceptorWorld;
  var root2 = Math.SQRT2;

  function create(canvas, win, skin) {
    var terrain = null, standing = null, names = null, fog = null, fogKey = '', zoom = Z ? Z.crea(win) : { factor: function () { return 1; } };
    var view = { e: 0, f: 0, z: 1, W: 0, H: 0, cx: 0, cy: 0 };
    function dpr() { return Math.min(2, root.devicePixelRatio || 1); }
    function band(n) { return B.band(n); }
    function compileAll() {
      terrain = [Wd.seaFrame(skin), Wd.islesFrame(skin, 0), Wd.islesFrame(skin, 1), Wd.islesFrame(skin, 2), Wd.islesFrame(skin, 3)].map(function (f) { return B.compile(f); });
      standing = B.compile(Wd.standFrame(skin));
      names = B.compile(Wd.namesFrame(skin));
    }

    function frameView(at, whole) {
      var W = root.innerWidth, H = root.innerHeight, r = win.getBoundingClientRect(), z, cam;
      var base = whole ? Math.min(r.width / 1110, r.height / 640) : r.width / 330;
      z = base * (whole ? 1 : zoom.factor());
      cam = whole ? { x: Wd.worldSize / 2, y: Wd.worldSize / 2 } : { x: at[0], y: at[1] };
      var o = C.aPantalla(cam, W, H, z, 0, 0);
      view = { W: W, H: H, z: z, cam: cam, e: o[0] + (r.left + r.width / 2 - W / 2), f: o[1] + (r.top + r.height / 2 - H / 2), ox: r.left + r.width / 2 - W / 2, oy: r.top + r.height / 2 - H / 2 };
      return view;
    }

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
      var v = frameView(state.at, whole), d = dpr(), ctx = canvas.getContext('2d'), m = C.matriz(v.z), i, items;
      if (canvas.width !== Math.round(v.W * d) || canvas.height !== Math.round(v.H * d)) { canvas.width = Math.round(v.W * d); canvas.height = Math.round(v.H * d); }
      ctx.setTransform(d, 0, 0, d, 0, 0);
      ctx.fillStyle = band(skin.sea);
      ctx.fillRect(0, 0, v.W, v.H);
      ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.setTransform(d * m[0], d * m[1], d * m[2], d * m[3], d * v.e, d * v.f);
      for (i = 0; i < terrain.length; i++) { P.paint(ctx, terrain[i]); }
      ctx.setTransform(d * v.z, 0, 0, d * v.z, d * v.e, d * v.f);
      P.paint(ctx, standing);
      if (state.cast) { P.paint(ctx, B.compile(state.cast)); }
      P.paint(ctx, names);
      brume(ctx, state.circles, d);
      ctx.setTransform(d * v.z, 0, 0, d * v.z, d * v.e, d * v.f);
      items = B.compile(state.frame);
      for (i = 0; i < items.length; i++) {
        ctx.setLineDash(items[i].o === 'ribbon' ? [16, 13] : []);
        P.paint(ctx, [items[i]]);
      }
      ctx.setLineDash([]);
      return v;
    }

    return { paint: paint, toWorld: toWorld, view: function () { return view; } };
  }

  root.PreceptorPaint = Object.freeze({ create: create });
})(window);
