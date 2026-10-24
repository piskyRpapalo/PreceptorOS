(function (root) {
  'use strict';
  var doc = root.document;
  var heads = {
    chat: ['Chat', 'LIVE', 'this page: the Preceptor answers; no model is connected'],
    battle: ['Battle', 'NO_DATA', 'combate_ticks: seeded rounds, receipt verified by replay'],
    info: ['Info', 'LIVE', 'this page: sound, voice, layouts and the machine view']
  };

  function create(onShow) {
    var tabs = Array.prototype.slice.call(doc.querySelectorAll('[role=tab]')), now = 'chat', opened = {}, switches = 0, worm = null, run = 0;
    var seal = {};
    Object.keys(heads).forEach(function (k) { seal[k] = heads[k][1]; });

    function center(el) { var q = el.getBoundingClientRect(); return [Math.round(q.left + q.width / 2), Math.round(q.top + q.height / 2)]; }
    function quiet() { return root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches; }
    function hue(s) { var S = root.AtlasSemantica, d = S && S.de ? S.de(s) : null; return d ? d.hue : null; }

    function crawl(a, b, id) {
      var W = root.AtlasWorm;
      if (!W || quiet()) { return; }
      if (!worm) { worm = doc.createElement('canvas'); worm.className = 'worm'; worm.setAttribute('aria-hidden', 'true'); doc.body.appendChild(worm); }
      var S = { ciclo: switches, intentos: opened[id], delta: (doc.getElementById('sheet-' + id).textContent.length - doc.getElementById('sheet-' + a.id).textContent.length), sello: seal[id] };
      var A = center(a.el), B = center(b), turn = ++run, frame = 0, d = Math.min(2, root.devicePixelRatio || 1), h = hue(seal[id]);
      var color = h === null ? 'rgba(150,160,180,.85)' : 'hsl(' + h + ' 70% 60%)';
      function draw() {
        if (turn !== run) { return; }
        frame++;
        var p = Math.min(1, frame / 24), gu = W.gusano(S, A, B, p), g = worm.getContext('2d'), scale = 4 * p * (1 - p) + 0.35, head = Math.round(p * 24);
        worm.width = Math.round(root.innerWidth * d); worm.height = Math.round(root.innerHeight * d);
        g.clearRect(0, 0, worm.width, worm.height);
        for (var s = 0; s < gu.segmentos; s++) {
          var q = gu.puntos[Math.max(0, head - s * 2)];
          g.beginPath(); g.arc(q[0] * d, q[1] * d, (7 - s * 0.45) * d * scale, 0, 2 * Math.PI);
          g.fillStyle = color; g.globalAlpha = 1 - s / (gu.segmentos + 1); g.fill();
        }
        if (p < 1) { root.requestAnimationFrame(draw); } else { g.clearRect(0, 0, worm.width, worm.height); }
      }
      root.requestAnimationFrame(draw);
    }

    function head(id) {
      doc.getElementById('sheet-title').textContent = heads[id][0];
      doc.getElementById('sheet-seal').textContent = seal[id];
      doc.getElementById('sheet-seal').dataset.seal = seal[id];
      doc.getElementById('sheet-source').textContent = 'Source: ' + heads[id][2];
    }

    function show(id, focus) {
      if (!heads[id]) { return; }
      var from = { id: now, el: doc.getElementById('tab-' + now) }, to = doc.getElementById('tab-' + id);
      if (id !== now) { switches++; }
      opened[id] = (opened[id] || 0) + 1;
      tabs.forEach(function (t) { var on = t.id === 'tab-' + id; t.setAttribute('aria-selected', String(on)); t.tabIndex = on ? 0 : -1; });
      Object.keys(heads).forEach(function (k) { doc.getElementById('sheet-' + k).hidden = k !== id; });
      if (id !== now) { crawl(from, to, id); }
      now = id;
      head(id);
      if (focus) { to.focus(); }
      if (onShow) { onShow(id); }
    }

    function mark(id, s) { seal[id] = s; if (id === now) { head(id); } }

    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { show(t.id.slice(4), false); });
      t.addEventListener('keydown', function (e) {
        var k = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
        if (k) { e.preventDefault(); show(tabs[(i + k + tabs.length) % tabs.length].id.slice(4), true); }
      });
    });
    head(now);
    return { show: show, mark: mark, now: function () { return now; }, switches: function () { return switches; } };
  }

  root.PreceptorPanel = Object.freeze({ create: create, heads: heads });
})(window);
