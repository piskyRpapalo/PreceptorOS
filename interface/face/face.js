(function (root) {
  'use strict';
  var V = 'preceptoros.bubble/1';
  var stopsXY = [[62, 376], [140, 398], [206, 404], [272, 398], [350, 376]];
  var homeStop = 2;
  var starSpots = [{ at: 0, x: 62, y: 214 }, { at: 1, x: 140, y: 132 }, { at: 3, x: 272, y: 132 }, { at: 4, x: 350, y: 214 }];
  var starH = [[1, 30, 30, 0], [-4, 9, 9, 0]];
  var crabH = [[1, 44, 26, 0], [5, 7, 7, 32], [-3, 7, 7, -32]];
  var changeList = ['rest', 'walk left', 'walk right', 'home', 'to star 4', 'ask star 4', 'sound on', 'sound off', 'free text: NO_DATA'];
  var actionList = ['left', 'right', 'ask', 'home', 'star1', 'star2', 'star3', 'star4', 'sound', 'read', 'say'];
  var words = {
    hello: 'Hi! I am your Preceptor. Someone new arrives, plays, and in under five minutes their own node speaks for them: safe, local, no cloud.',
    how: 'Walk the crab to a star. Each star is one question for me.',
    stars: [
      ['Rack status', 'I cannot see a rack from this page, so I will not guess. Rack status: NO_DATA. Cause: no rack is paired with this preview.'],
      ['Energy budget', 'No energy reading reaches this page. Energy budget: NO_DATA. Cause: no meter is connected.'],
      ['Node measures', 'No node is paired yet, so there is nothing measured to read. Node measures: NO_DATA. Cause: no node is paired.'],
      ['Study laws', 'Three laws. Your data stays yours. Sensors tell the truth, and what is not measured says NO_DATA. The machine proposes; you sign.']
    ],
    home: 'Back in the middle of the island. Pick a star.',
    free: 'No model is connected to this preview, so I cannot answer free text yet: NO_DATA. The stars work without one.',
    tail: 'Shortcuts: Rack status, Energy budget, Node measures, Study laws.'
  };

  function starAt(stop) {
    for (var i = 0; i < starSpots.length; i++) { if (starSpots[i].at === stop) { return i; } }
    return -1;
  }

  function uniq(list) { return list.filter(function (b, j, a) { return a.indexOf(b) === j; }); }

  function sceneFrame(skin, st) {
    var c = stopsXY[st.stop], x = c[0], y = c[1], lit = starAt(st.stop), stars = [], i, s, it;
    for (i = 0; i < starSpots.length; i++) {
      s = starSpots[i];
      it = { o: 'wave', x: s.x, y: s.y, h: starH, f: i === lit ? skin.lit : skin.star };
      if (i === lit) { it.sc = 1.4; }
      stars.push(it);
    }
    return {
      v: V, id: 'face', t: st.stop,
      atoms: [
        { k: 'isle', r: 'island, path', i: [{ o: 'blob', x: 206, y: 410, rx: 196, ry: 84, f: skin.land }, { o: 'ribbon', pts: stopsXY, s: skin.path, lw: 9 }] },
        { k: 'stars', r: lit >= 0 ? 'star ' + (lit + 1) + ' lit' : 'four stars', i: stars },
        { k: 'crab', r: 'crab at ' + (st.stop + 1), i: [{ o: 'wave', x: x, y: y - 34, h: crabH, f: skin.body }, { o: 'arcs', x: x, y: y - 42, r: [13, 13], n: 2, arc: 24, ph: 168, s: 'ink', lw: 9 }] }
      ],
      bands: uniq([skin.land, skin.path, skin.star, skin.lit, skin.body, 'ink']),
      change: [st.change || 'rest'],
      sound: st.sound ? 'star voice' : 'NO_DATA',
      soundCause: st.sound ? 'vozDe star h' : 'sound off',
      motion: 'on input'
    };
  }

  function headFrame(skin) {
    return {
      v: V, id: 'head', t: 0, cv: [120, 120],
      atoms: [{ k: 'head', r: 'the Preceptor smiles', i: [
        { o: 'arcs', x: 60, y: 60, r: [50, 50], n: 3, arc: 70, ph: 195, s: skin.path, lw: 5 },
        { o: 'blob', x: 60, y: 62, rx: 38, ry: 40, f: skin.face },
        { o: 'blob', x: 47, y: 56, rx: 5, ry: 7, f: 'ink' }, { o: 'blob', x: 73, y: 56, rx: 5, ry: 7, f: 'ink' },
        { o: 'ribbon', pts: [[47, 76], [60, 85], [73, 76]], s: 'ink', lw: 4 }] }],
      bands: uniq([skin.path, skin.face, 'ink']), change: ['rest'], sound: 'NO_DATA', soundCause: 'avatar is silent', motion: 'NO_DATA'
    };
  }

  function joyFrame(skin, dx, dy) {
    return {
      v: V, id: 'joy', t: 0, cv: [168, 168],
      atoms: [
        { k: 'base', r: 'joystick, four arrows', i: [
          { o: 'blob', x: 84, y: 84, rx: 74, ry: 74, rough: 0, f: skin.land },
          { o: 'arcs', x: 84, y: 84, r: [58, 58], n: 4, arc: 36, ph: -18, s: 'ink', lw: 5 }] },
        { k: 'knob', r: dx || dy ? 'knob pushed' : 'knob centered', i: [{ o: 'blob', x: 84 + dx, y: 84 + dy, rx: 30, ry: 30, rough: 0, f: skin.body }] }
      ],
      bands: uniq([skin.land, 'ink', skin.body]), change: ['joystick'], sound: 'NO_DATA', soundCause: 'joystick is silent', motion: 'follows the finger'
    };
  }

  function bytes(o) {
    var s = JSON.stringify(o);
    return typeof TextEncoder === 'function' ? new TextEncoder().encode(s).length : Buffer.byteLength(s, 'utf8');
  }

  var Face = { changeList: changeList, stopsXY: stopsXY, starSpots: starSpots, homeStop: homeStop, actionList: actionList, words: words, sceneFrame: sceneFrame, headFrame: headFrame, joyFrame: joyFrame, bytes: bytes, starAt: starAt };

  if (typeof module === 'object' && module.exports) { module.exports = Face; return; }

  var doc = root.document, B = root.AtlasBubble, P = root.AtlasComicAtoms, A = root.AtlasSintesis;
  var skin = JSON.parse(doc.getElementById('skin').textContent);
  var st = { stop: homeStop, sound: false, change: 'rest', said: words.how };
  var $ = function (id) { return doc.getElementById(id); };
  var scene = $('scene'), joy = $('joy'), log = $('log'), say = $('say'), packet = $('packet'), machine = $('machine');
  var touch = typeof root.navigator.vibrate === 'function' ? 'vibrate' : 'NO_DATA: this device has no vibration';
  var voices = function () { return root.speechSynthesis ? root.speechSynthesis.getVoices().filter(function (v) { return v.localService && /^en/i.test(v.lang); }) : []; };

  function paint(canvas, frame) {
    var cv = frame.cv || [412, 515], dpr = Math.min(3, root.devicePixelRatio || 1);
    if (canvas.width !== cv[0] * dpr) { canvas.width = cv[0] * dpr; canvas.height = cv[1] * dpr; }
    var ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = B.band(skin.sea);
    ctx.fillRect(0, 0, cv[0], cv[1]);
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    P.paint(ctx, B.compile(frame));
  }

  function theme() {
    var r = doc.documentElement.style, u = skin.ui, k;
    for (k in u) { if (Object.prototype.hasOwnProperty.call(u, k)) { r.setProperty('--' + k, B.band(u[k])); } }
  }

  function bubble(who, text) {
    var li = doc.createElement('li');
    li.className = who;
    li.innerHTML = '<span class="who"></span><span class="txt"></span>';
    li.firstChild.textContent = who === 'me' ? 'You' : 'Preceptor';
    li.lastChild.textContent = text;
    log.appendChild(li);
    while (log.children.length > 6) { log.removeChild(log.firstChild); }
    log.scrollTop = log.scrollHeight;
  }

  function render() {
    var f = sceneFrame(skin, st), n = bytes(f), lit = starAt(st.stop);
    paint(scene, f);
    packet.textContent = JSON.stringify(f);
    machine.textContent = JSON.stringify(f, null, 1);
    $('bytes').textContent = n + ' B of 1,024 B';
    scene.setAttribute('aria-label', 'Island scene. ' + f.atoms.map(function (a) { return a.r; }).join('. ') + '.');
    say.textContent = lit >= 0 ? 'The crab is on star ' + (lit + 1) + ': ' + words.stars[lit][0] + '. The Preceptor answered in the chat.' : st.said;
    doc.body.dataset.stop = st.stop;
    var ks = doc.querySelectorAll('.skins a');
    for (var j = 0; j < ks.length; j++) { if (ks[j].textContent.toLowerCase() === skin.name) { ks[j].setAttribute('aria-current', 'page'); } }
    var bs = doc.querySelectorAll('[data-act^="star"]');
    for (var i = 0; i < bs.length; i++) { bs[i].setAttribute('aria-current', String(i === lit)); }
    $('sound').setAttribute('aria-pressed', String(st.sound));
    $('sound').lastChild.textContent = st.sound ? 'Sound on' : 'Sound off';
    $('touch').textContent = touch;
  }

  function buzz(p) { if (touch === 'vibrate') { root.navigator.vibrate(p); } }

  function voice(i) {
    if (!st.sound || !A) { return; }
    A.activa(true);
    A.suena(A.vozDe({ armonicos: starH.map(function (h, j) { return [h[0], h[1] + 2 * i * j, h[2], h[3]]; }) }));
    root.setTimeout(function () { A.suena('pop'); }, 620);
  }

  function arrive(change) {
    var lit = starAt(st.stop);
    st.change = change;
    if (lit >= 0) {
      st.said = words.stars[lit][1];
      bubble('pre', st.said);
      buzz([30, 40, 30]); voice(lit);
    } else if (st.stop === homeStop) {
      st.said = words.home;
    } else { st.said = 'On the path. Keep walking to a star.'; buzz(15); }
    render();
  }

  function act(name, arg) {
    var lit = starAt(st.stop), m;
    if (name === 'left' && st.stop > 0) { st.stop--; arrive('walk left'); }
    else if (name === 'right' && st.stop < stopsXY.length - 1) { st.stop++; arrive('walk right'); }
    else if (name === 'home') { st.stop = homeStop; arrive('home'); }
    else if ((m = /^star([1-4])$/.exec(name))) { st.stop = starSpots[+m[1] - 1].at; arrive('to star ' + m[1]); }
    else if (name === 'ask') { if (lit >= 0) { arrive('ask star ' + (lit + 1)); } else { st.said = words.how; render(); } }
    else if (name === 'sound') { st.sound = !st.sound; st.change = st.sound ? 'sound on' : 'sound off'; render(); }
    else if (name === 'read') { read(); }
    else if (name === 'say' && arg) { bubble('me', String(arg).slice(0, 280)); st.said = words.free; bubble('pre', words.free); st.change = 'free text: NO_DATA'; render(); }
    return state();
  }

  function read() {
    var vs = voices(), out = $('readout');
    if (!vs.length) { out.textContent = 'Read aloud: NO_DATA. Cause: no local English voice on this device.'; return; }
    root.speechSynthesis.cancel();
    [st.said, words.tail].forEach(function (t) { var u = new root.SpeechSynthesisUtterance(t); u.voice = vs[0]; u.lang = vs[0].lang; root.speechSynthesis.speak(u); });
    out.textContent = 'Reading aloud with a local voice: answer first, then the shortcuts.';
  }

  function state() {
    var f = sceneFrame(skin, st), lit = starAt(st.stop);
    return { skin: skin.name, stop: st.stop, station: st.stop, star: lit >= 0 ? lit + 1 : null, said: st.said, bytes: bytes(f), frame: f, actions: actionList.slice(),
      channels: { eye: 'canvas', text: 'aria-live and packet', ear: st.sound ? 'core.js FM' : 'NO_DATA: sound is off', touch: touch } };
  }

  function stick() {
    var o = null, fired = false, R = 40;
    function draw(dx, dy) { paint(joy, joyFrame(skin, Math.round(dx), Math.round(dy))); }
    function dir(dx, dy) { return Math.abs(dx) >= Math.abs(dy) ? (dx < 0 ? 'left' : 'right') : (dy < 0 ? 'ask' : 'home'); }
    function rel(e) { var b = joy.getBoundingClientRect(), k = 168 / b.width; return [(e.clientX - b.left) * k - 84, (e.clientY - b.top) * k - 84]; }
    joy.addEventListener('pointerdown', function (e) { joy.setPointerCapture(e.pointerId); o = rel(e); fired = false; e.preventDefault(); });
    joy.addEventListener('pointermove', function (e) {
      if (!o) { return; }
      var p = rel(e), dx = p[0] - o[0], dy = p[1] - o[1], d = Math.hypot(dx, dy);
      if (d > R) { dx *= R / d; dy *= R / d; }
      draw(dx, dy);
      if (!fired && d > 28) { fired = true; act(dir(dx, dy)); }
    });
    function end() {
      if (o && !fired && Math.hypot(o[0], o[1]) > 22) { act(dir(o[0], o[1])); }
      o = null; draw(0, 0);
    }
    joy.addEventListener('pointerup', end);
    joy.addEventListener('pointercancel', function () { o = null; draw(0, 0); });
    joy.addEventListener('keydown', function (e) {
      var k = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'ask', ArrowDown: 'home', Enter: 'ask', ' ': 'ask' }[e.key];
      if (!k) { return; }
      e.preventDefault();
      draw(k === 'left' ? -R : k === 'right' ? R : 0, k === 'ask' ? -R : k === 'home' ? R : 0);
      act(k);
      draw(0, 0);
    });
    draw(0, 0);
  }

  doc.addEventListener('click', function (e) {
    var b = e.target.closest('[data-act]');
    if (b) { act(b.getAttribute('data-act')); }
  });
  $('ask').addEventListener('submit', function (e) {
    e.preventDefault();
    var i = $('reply');
    if (i.value.trim()) { act('say', i.value.trim()); i.value = ''; }
  });

  try {
    theme();
    paint($('head'), headFrame(skin));
    bubble('pre', words.hello);
    stick();
    render();
    root.preceptorFace = Object.freeze({ state: state, act: act, actions: actionList.slice() });
  } catch (err) {
    say.textContent = 'NO_DATA: the scene could not be drawn. Cause: ' + err.message;
  }
})(typeof module === 'object' && module.exports ? this : window);
