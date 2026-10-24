(function (root) {
  'use strict';
  var doc = root.document, B = root.AtlasBubble, P = root.AtlasComicAtoms;
  var V = 'preceptoros.bubble/1';

  function iconFrame(kind, skin) {
    var items;
    if (kind === 'task') { items = [{ o: 'wave', x: 32, y: 32, h: [[1, 20, 20, 0], [-4, 6, 6, 0]], f: skin.lit }]; }
    else if (kind === 'follow') { items = [{ o: 'ribbon', pts: [[10, 48], [22, 26], [40, 38], [54, 14]], s: skin.path, lw: 6 }, { o: 'blob', x: 54, y: 14, rx: 6, ry: 6, rough: 0, f: skin.path }]; }
    else { items = [{ o: 'blob', x: 32, y: 34, rx: 22, ry: 13, rough: 0, f: skin.sand }, { o: 'arcs', x: 32, y: 32, r: [26, 26], n: 4, arc: 50, ph: -25, s: 'ink', lw: 4 }]; }
    return { v: V, id: 'icon-' + kind, t: 0, cv: [64, 64], atoms: [{ k: kind, r: kind + ' icon', i: items }], bands: [skin.lit, skin.path, skin.sand, 'ink'].filter(function (b, j, a) { return a.indexOf(b) === j; }), change: ['rest'], sound: 'NO_DATA', soundCause: 'icon is silent', motion: 'NO_DATA' };
  }

  function paintIcon(canvas, frame) {
    var d = Math.min(3, root.devicePixelRatio || 1), g = canvas.getContext('2d');
    canvas.width = 64 * d; canvas.height = 64 * d;
    g.setTransform(d, 0, 0, d, 0, 0); g.lineJoin = 'round'; g.lineCap = 'round';
    P.paint(g, B.compile(frame));
  }

  function quiet() { return root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches; }

  function voices() { return root.speechSynthesis ? root.speechSynthesis.getVoices().filter(function (v) { return v.localService && /^en/i.test(v.lang); }) : []; }
  function say(texts) {
    var vs = voices();
    if (!vs.length) { return false; }
    root.speechSynthesis.cancel();
    texts.forEach(function (t) { var u = new root.SpeechSynthesisUtterance(t); u.voice = vs[0]; u.lang = vs[0].lang; root.speechSynthesis.speak(u); });
    return true;
  }

  function create(skin, soundOn) {
    function voice(text) { if (soundOn()) { say([text]); } }
    var toast = doc.getElementById('toast'), offer = doc.getElementById('offer'), run = 0, onYes = null, onNo = null;
    ['task', 'follow', 'whole'].forEach(function (k) { var c = doc.querySelector('[data-icon="' + k + '"]'); if (c) { paintIcon(c, iconFrame(k, skin)); } });

    function show(text) {
      var turn = ++run, frame = 0;
      toast.textContent = text;
      toast.hidden = false;
      toast.style.opacity = '1';
      voice(text);
      if (quiet()) { return; }
      function fade() {
        if (turn !== run) { return; }
        frame++;
        if (frame > 150) { toast.style.opacity = String(Math.max(0, 1 - (frame - 150) / 30)); }
        if (frame >= 180) { toast.hidden = true; return; }
        root.requestAnimationFrame(fade);
      }
      root.requestAnimationFrame(fade);
    }
    function ask(text, yes, no) {
      onYes = yes; onNo = no;
      doc.getElementById('offer-text').textContent = text;
      offer.hidden = false;
      voice(text + ' Accept or decline.');
      doc.getElementById('offer-yes').focus();
    }
    function close(ok) { offer.hidden = true; var f = ok ? onYes : onNo; onYes = onNo = null; if (f) { f(); } }
    doc.getElementById('offer-yes').addEventListener('click', function () { close(true); });
    doc.getElementById('offer-no').addEventListener('click', function () { close(false); });
    offer.addEventListener('keydown', function (e) { if (e.key === 'Escape') { e.preventDefault(); close(false); } });
    toast.addEventListener('click', function () { run++; toast.hidden = true; });
    function read(texts, out) {
      out.textContent = say(texts) ? 'Reading aloud with a local voice: the answer first, then the shortcuts.' : 'Read aloud: NO_DATA. Cause: no local English voice on this device.';
    }
    return { show: show, ask: ask, read: read, open: function () { return !offer.hidden; } };
  }

  var Hud = { create: create, iconFrame: iconFrame };
  if (typeof module === 'object' && module.exports) { module.exports = Hud; } else { root.PreceptorHud = Hud; }
})(typeof module === 'object' && module.exports ? this : window);
