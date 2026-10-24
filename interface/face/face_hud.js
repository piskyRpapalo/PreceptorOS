(function (root) {
  'use strict';
  var doc = root.document, B = root.AtlasBubble, P = root.AtlasComicAtoms;
  var V = 'preceptoros.bubble/1';

  function iconFrame(kind, skin) {
    var items;
    if (kind === 'task') { items = [{ o: 'wave', x: 32, y: 32, h: [[1, 20, 20, 0], [-4, 6, 6, 0]], f: skin.lit }]; }
    else if (kind === 'follow') { items = [{ o: 'ribbon', pts: [[10, 48], [22, 26], [40, 38], [54, 14]], s: skin.path, lw: 6 }, { o: 'blob', x: 54, y: 14, rx: 6, ry: 6, rough: 0, f: skin.path }]; }
    else if (kind === 'whole') { items = [{ o: 'blob', x: 32, y: 34, rx: 22, ry: 13, rough: 0, f: skin.sand }, { o: 'arcs', x: 32, y: 32, r: [26, 26], n: 4, arc: 50, ph: -25, s: 'ink', lw: 4 }]; }
    else {
      items = [{ o: 'ribbon', pts: [[10, 24], [20, 24], [34, 12], [34, 52], [20, 40], [10, 40]], closed: true, f: skin.sand, s: 'ink', lw: 3 }];
      if (kind === 'speaker-on') { items.push({ o: 'arcs', x: 36, y: 32, r: [10, 20], n: 2, arc: 70, ph: -35, s: 'ink', lw: 4 }); }
      else { items.push({ o: 'ribbon', pts: [[40, 22], [56, 42]], s: 'vermilion.base', lw: 5 }, { o: 'ribbon', pts: [[56, 22], [40, 42]], s: 'vermilion.base', lw: 5 }); }
    }
    return { v: V, id: 'icon-' + kind, t: 0, cv: [64, 64], atoms: [{ k: kind, r: kind + ' icon', i: items }], bands: [skin.lit, skin.path, skin.sand, 'ink', 'vermilion.base'].filter(function (b, j, a) { return a.indexOf(b) === j; }), change: ['rest'], sound: 'NO_DATA', soundCause: 'icon is silent', motion: 'NO_DATA' };
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
    var spk = doc.getElementById('speaker'), radio = doc.getElementById('radio'), line = doc.getElementById('radio-line'), on = false, lastSaid = '';
    function screen() {
      var t = function (id) { var e = doc.getElementById(id); return e ? e.textContent.trim() : ''; };
      var log = doc.querySelectorAll('#log li'), last = log.length ? log[log.length - 1].lastChild.textContent : '';
      var c = doc.getElementById('counter'), map = doc.getElementById('mapwin').getAttribute('aria-label');
      return [t('say'), map, c && !c.hidden ? 'Distance left ' + t('c-dist') + '. Time left ' + t('c-time') + '.' : '', 'Panel: ' + t('sheet-title') + '.', last ? 'Last message: ' + last : ''].filter(Boolean);
    }
    var tail = 'Shortcuts: the star icon takes a task, the path icon walks, the map icon shows the whole map; Chat, Battle and Info are the panel tabs.';
    function broadcast(texts) {
      line.textContent = texts.join(' ') + ' · ' + tail;
      if (!say(texts.concat([tail]))) { line.textContent += ' · Voice: NO_DATA, cause: no local voice on this device; the text above is the radio.'; }
    }
    function setOn(v) {
      on = v;
      spk.setAttribute('aria-pressed', String(on));
      spk.lastChild.textContent = on ? 'Screen reader on' : 'Screen reader off';
      paintIcon(spk.firstChild, iconFrame(on ? 'speaker-on' : 'speaker', skin));
      radio.hidden = !on;
      if (on) { lastSaid = doc.getElementById('say').textContent; broadcast(screen()); } else if (root.speechSynthesis) { root.speechSynthesis.cancel(); }
    }
    spk.addEventListener('click', function () { setOn(!on); });
    doc.getElementById('radio-again').addEventListener('click', function () { broadcast(screen()); });
    new root.MutationObserver(function () {
      var now = doc.getElementById('say').textContent;
      if (on && now && now !== lastSaid) { lastSaid = now; broadcast([now]); }
    }).observe(doc.getElementById('say'), { childList: true, characterData: true, subtree: true });
    setOn(false);
    return { show: show, ask: ask, read: read, screen: screen, dismiss: function () { offer.hidden = true; onYes = onNo = null; }, reader: function () { return on; }, open: function () { return !offer.hidden; } };
  }

  var Hud = { create: create, iconFrame: iconFrame };
  if (typeof module === 'object' && module.exports) { module.exports = Hud; } else { root.PreceptorHud = Hud; }
})(typeof module === 'object' && module.exports ? this : window);
