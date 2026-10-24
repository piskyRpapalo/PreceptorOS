(function (root) {
  'use strict';
  var doc = root.document, B = root.AtlasBubble, P = root.AtlasComicAtoms, A = root.AtlasSintesis, Wd = root.PreceptorWorld;
  var $ = function (id) { return doc.getElementById(id); };
  var skin = JSON.parse($('skin').textContent);
  var places = Wd.places, actionList = ['start', 'follow', 'up', 'down', 'left', 'right', 'whole', 'sound', 'read', 'say'];
  var words = {
    hello: 'Hi! I am your Preceptor. Someone new arrives, plays, and in under five minutes their own node speaks for them: safe, local, no cloud.',
    how: 'This is the living map. You are the crab. Press Start task.',
    tap: 'A dashed path goes to the task. Tap the path, or press Follow the path.',
    end: 'All three places are measured and the fog is gone. Walk anywhere with the joystick.',
    free: 'No model is connected to this preview, so I cannot answer free text yet: NO_DATA. The tasks work without one.',
    tail: 'Shortcuts: Start task, Follow the path, Whole map, Sound, Read aloud.'
  };
  var st = { at: Wd.homeAt.slice(), moves: 0, dir: -1, met: null, task: 0, step: 0, path: null, route: null, walking: false, sound: false, change: 'rest', said: words.how, whole: false };
  var map = $('map'), joy = $('joy'), log = $('log'), say = $('say');
  var touch = typeof root.navigator.vibrate === 'function' ? 'vibrate' : 'NO_DATA: this device has no vibration';
  var mapItems = null, cam = { x: 0, y: 0, z: 1 }, timer = 0, held = null;

  function band(n) { return B.band(n); }
  function theme() { var r = doc.documentElement.style, u = skin.ui, k; for (k in u) { if (Object.prototype.hasOwnProperty.call(u, k)) { r.setProperty('--' + k, band(u[k])); } } }
  function dpr() { return Math.min(3, root.devicePixelRatio || 1); }

  function paintSmall(canvas, frame) {
    var cv = frame.cv, d = dpr(), ctx = canvas.getContext('2d');
    if (canvas.width !== cv[0] * d) { canvas.width = cv[0] * d; canvas.height = cv[1] * d; }
    ctx.setTransform(d, 0, 0, d, 0, 0);
    ctx.clearRect(0, 0, cv[0], cv[1]);
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    P.paint(ctx, B.compile(frame));
  }

  function frameNow() {
    return Wd.stateFrame(skin, { at: st.at, dir: st.dir, step: st.step, task: st.task, path: st.path, change: st.change, sound: st.sound, walking: st.walking });
  }
  function castNow() {
    return Wd.castFrame(skin, { at: st.at, moves: st.moves, step: st.step, change: st.change });
  }

  function view() {
    var w = map.clientWidth || 320, h = map.clientHeight || 400, z = st.whole ? Math.min(w / Wd.W, h / Wd.H) : Math.max(w / 560, h / 700);
    cam.z = z;
    cam.x = Wd.clamp(st.at[0] - w / z / 2, Math.min(0, Wd.W - w / z), Math.max(0, Wd.W - w / z));
    cam.y = Wd.clamp(st.at[1] - h / z / 2, Math.min(0, Wd.H - h / z), Math.max(0, Wd.H - h / z));
    if (st.whole) { cam.x = (Wd.W - w / z) / 2; cam.y = (Wd.H - h / z) / 2; }
    return [w, h];
  }

  function paintMap(f) {
    var wh = view(), d = dpr(), ctx = map.getContext('2d'), items, i;
    if (map.width !== Math.round(wh[0] * d) || map.height !== Math.round(wh[1] * d)) { map.width = Math.round(wh[0] * d); map.height = Math.round(wh[1] * d); }
    ctx.setTransform(d, 0, 0, d, 0, 0);
    ctx.fillStyle = band(skin.sea);
    ctx.fillRect(0, 0, wh[0], wh[1]);
    ctx.setTransform(d * cam.z, 0, 0, d * cam.z, -cam.x * d * cam.z, -cam.y * d * cam.z);
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    if (!mapItems) { mapItems = B.compile(Wd.mapFrame(skin)).concat(B.compile(Wd.nodesFrame(skin)), B.compile(Wd.gridFrame(skin))); }
    P.paint(ctx, mapItems);
    var cf = castNow();
    if (cf) { P.paint(ctx, B.compile(cf)); }
    items = B.compile(f);
    for (i = 0; i < items.length; i++) {
      ctx.setLineDash(items[i].o === 'ribbon' ? [16, 13] : []);
      P.paint(ctx, [items[i]]);
    }
    ctx.setLineDash([]);
  }

  function bubble(who, text) {
    var li = doc.createElement('li');
    li.className = who;
    li.innerHTML = '<span class="who"></span><span class="txt"></span>';
    li.firstChild.textContent = who === 'me' ? 'You' : 'Preceptor';
    li.lastChild.textContent = text;
    log.appendChild(li);
    while (log.children.length > 8) { log.removeChild(log.firstChild); }
    log.scrollTop = log.scrollHeight;
  }

  function count() {
    if (!st.route) { return null; }
    return Wd.counter(st.route.steps - st.step, st.route.units);
  }

  function render() {
    var f = frameNow(), n = Wd.bytes(f), c = count(), done = st.task >= places.length;
    paintMap(f);
    $('packet').textContent = JSON.stringify(f);
    $('machine').textContent = JSON.stringify(f, null, 1);
    $('machine-map').textContent = [Wd.mapFrame(skin), Wd.nodesFrame(skin), Wd.gridFrame(skin), castNow()].filter(Boolean).map(function (x) { return JSON.stringify(x); }).join('\n');
    $('bytes').textContent = n + ' B of 1,024 B';
    map.setAttribute('aria-label', 'The living map. ' + f.atoms.map(function (a) { return a.r; }).join('. ') + '.');
    say.textContent = st.said;
    $('start').disabled = st.walking || done;
    $('start').lastChild.textContent = done ? 'All tasks done' : 'Start task ' + (st.task + 1) + ': ' + places[st.task].name;
    $('follow').disabled = !st.path || st.walking;
    $('whole').setAttribute('aria-pressed', String(st.whole));
    $('sound').setAttribute('aria-pressed', String(st.sound));
    $('sound').lastChild.textContent = st.sound ? 'Sound on' : 'Sound off';
    $('counter').hidden = !c;
    if (c) {
      $('c-dist').textContent = c.tiles + ' tiles';
      $('c-time').textContent = c.steps + ' steps';
      $('c-real').textContent = c.realTime;
      $('c-yard').textContent = c.yardstick + '. This route: ' + c.mapUnits + ' map units, ' + st.route.steps + ' steps.';
    }
    var ts = doc.querySelectorAll('#tasks li');
    for (var i = 0; i < ts.length; i++) { ts[i].dataset.state = i < st.task ? 'done' : i === st.task ? 'now' : 'later'; ts[i].lastChild.textContent = i < st.task ? 'measured' : i === st.task ? 'now' : 'in the fog'; }
    $('touch').textContent = touch;
  }

  function buzz(p) { if (touch === 'vibrate') { root.navigator.vibrate(p); } }
  function voice(i) {
    if (!st.sound || !A) { return; }
    A.activa(true);
    A.suena(A.vozDe({ armonicos: Wd.starH.map(function (h, j) { return [h[0], h[1] + 3 * i * j, h[2], h[3]]; }) }));
    root.setTimeout(function () { A.suena('pop'); }, 620);
  }

  function meet() {
    var m = Wd.castMeet(skin, { at: st.at, moves: st.moves });
    if (m && m !== st.met) { bubble('pre', m); }
    st.met = m;
  }

  function stopWalk() { st.walking = false; if (timer) { root.cancelAnimationFrame(timer); timer = 0; } }

  function arriveCheck() {
    if (st.task >= places.length) { return false; }
    var place = places[st.task], p = place.at;
    if (Math.hypot(st.at[0] - p[0], st.at[1] - p[1]) > 30) { return false; }
    st.task++;
    stopWalk();
    st.path = null; st.route = null; st.step = 0;
    st.change = 'arrived';
    st.said = place.done;
    bubble('pre', place.done);
    bubble('pre', st.task < places.length ? places[st.task].task + ' Press Start task.' : words.end);
    buzz([30, 40, 30]); voice(st.task);
    return true;
  }

  function start() {
    if (st.walking || st.task >= places.length) { return; }
    st.path = Wd.route(st.at, places[st.task]);
    st.route = null; st.step = 0; st.change = 'path';
    st.said = places[st.task].task + ' ' + words.tap;
    bubble('pre', st.said);
    render();
  }

  function follow() {
    if (!st.path || st.walking) { return; }
    st.route = Wd.walk(st.path); st.step = 0; st.walking = true; st.change = 'step 0 of ' + st.route.steps;
    var c = count(), reduce = root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches, tick = 0;
    st.said = 'Walking to ' + places[st.task].name + ': ' + c.tiles + ' tiles, ' + c.steps + ' steps. Real time: NO_DATA, no clock is read.';
    bubble('pre', st.said);
    function frame() {
      tick++;
      if (reduce || tick % 4 === 0) {
        st.step = reduce ? st.route.steps : st.step + 1;
        if (st.route.at[st.step][0] !== st.at[0]) { st.dir = st.route.at[st.step][0] > st.at[0] ? 1 : -1; }
        st.at = st.route.at[st.step].slice();
        st.moves++;
        meet();
        st.change = 'step ' + st.step + ' of ' + st.route.steps;
        if (st.step >= st.route.steps) {
          st.walking = false; timer = 0;
          if (!arriveCheck()) { st.said = 'You reached the end of the path.'; }
          render();
          return;
        }
        render();
      }
      timer = root.requestAnimationFrame(frame);
    }
    render();
    timer = root.requestAnimationFrame(frame);
  }

  function move(dx, dy, n) {
    if (st.walking) { stopWalk(); st.route = null; st.step = 0; st.said = 'You took the joystick. Press Start task to draw the path again.'; }
    st.at = [Wd.clamp(Math.round(st.at[0] + dx * n), 20, Wd.W - 20), Wd.clamp(Math.round(st.at[1] + dy * n), 20, Wd.H - 20)];
    if (dx) { st.dir = dx > 0 ? 1 : -1; }
    st.moves++;
    meet();
    st.change = 'joystick';
    if (!arriveCheck() && st.path) { st.path = Wd.route(st.at, places[st.task]); st.route = null; }
    render();
  }

  function act(name, arg) {
    var T = 2 * Wd.tile;
    if (name === 'start') { start(); }
    else if (name === 'follow') { follow(); }
    else if (name === 'left') { move(-1, 0, T); }
    else if (name === 'right') { move(1, 0, T); }
    else if (name === 'up') { move(0, -1, T); }
    else if (name === 'down') { move(0, 1, T); }
    else if (name === 'whole') { st.whole = !st.whole; st.change = st.whole ? 'whole map' : 'near view'; render(); }
    else if (name === 'sound') { st.sound = !st.sound; st.change = st.sound ? 'sound on' : 'sound off'; render(); }
    else if (name === 'read') { read(); }
    else if (name === 'say' && arg) { bubble('me', String(arg).slice(0, 280)); st.said = words.free; bubble('pre', words.free); st.change = 'free text'; render(); }
    return state();
  }

  function read() {
    var vs = root.speechSynthesis ? root.speechSynthesis.getVoices().filter(function (v) { return v.localService && /^en/i.test(v.lang); }) : [], out = $('readout');
    if (!vs.length) { out.textContent = 'Read aloud: NO_DATA. Cause: no local English voice on this device.'; return; }
    root.speechSynthesis.cancel();
    [st.said, words.tail].forEach(function (t) { var u = new root.SpeechSynthesisUtterance(t); u.voice = vs[0]; u.lang = vs[0].lang; root.speechSynthesis.speak(u); });
    out.textContent = 'Reading aloud with a local voice: the answer first, then the shortcuts.';
  }

  function state() {
    var f = frameNow();
    return { skin: skin.name, layout: skin.layout, at: st.at.slice(), task: st.task < places.length ? places[st.task].id : null, done: st.task, walking: st.walking,
      path: !!st.path, counter: count(), said: st.said, bytes: Wd.bytes(f), frame: f, actions: actionList.slice(),
      channels: { eye: 'canvas', text: 'aria-live and packet', ear: st.sound ? 'core.js FM' : 'NO_DATA: sound is off', touch: touch } };
  }

  function stick() {
    var on = false, R = 40, dir = [0, 0], tick = 0;
    function draw(dx, dy) { paintSmall(joy, Wd.joyFrame(skin, Math.round(dx), Math.round(dy))); }
    function rel(e) { var b = joy.getBoundingClientRect(), k = 168 / b.width; return [(e.clientX - b.left) * k - 84, (e.clientY - b.top) * k - 84]; }
    function pump() {
      if (!on) { return; }
      tick++;
      if (tick % 4 === 0 && (dir[0] || dir[1])) { move(dir[0], dir[1], Wd.tile); }
      held = root.requestAnimationFrame(pump);
    }
    function aim(p) {
      var d = Math.hypot(p[0], p[1]), dx = p[0], dy = p[1];
      if (d > R) { dx *= R / d; dy *= R / d; }
      draw(dx, dy);
      dir = d > 18 ? [p[0] / d, p[1] / d] : [0, 0];
    }
    function end() { on = false; dir = [0, 0]; if (held) { root.cancelAnimationFrame(held); held = null; } draw(0, 0); }
    joy.addEventListener('pointerdown', function (e) { joy.setPointerCapture(e.pointerId); on = true; e.preventDefault(); aim(rel(e)); tick = 3; held = root.requestAnimationFrame(pump); });
    joy.addEventListener('pointermove', function (e) { if (on) { aim(rel(e)); } });
    joy.addEventListener('pointerup', end);
    joy.addEventListener('pointercancel', end);
    joy.addEventListener('keydown', function (e) {
      var k = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down' }[e.key];
      if (k) { e.preventDefault(); act(k); }
    });
    draw(0, 0);
  }

  map.addEventListener('click', function (e) {
    if (!st.path || st.walking) { return; }
    var b = map.getBoundingClientRect(), x = cam.x + (e.clientX - b.left) / cam.z, y = cam.y + (e.clientY - b.top) / cam.z;
    var near = Wd.walk(st.path).at.some(function (q) { return Math.hypot(q[0] - x, q[1] - y) < 34 / Math.min(1, cam.z); });
    if (near) { follow(); }
  });
  doc.addEventListener('click', function (e) { var b = e.target.closest('[data-act]'); if (b && !b.disabled) { act(b.getAttribute('data-act')); } });
  $('ask').addEventListener('submit', function (e) { e.preventDefault(); var i = $('reply'); if (i.value.trim()) { act('say', i.value.trim()); i.value = ''; } });
  if (root.ResizeObserver) { new root.ResizeObserver(function () { if (!st.walking) { render(); } }).observe(map); }

  try {
    theme();
    doc.body.dataset.layout = skin.layout;
    paintSmall($('head'), Wd.headFrame(skin));
    var ks = doc.querySelectorAll('.skins a');
    for (var j = 0; j < ks.length; j++) { if (ks[j].getAttribute('href').slice(-skin.name.length - 6) === '/' + skin.name + '.html' || ks[j].getAttribute('href') === skin.name + '.html') { ks[j].setAttribute('aria-current', 'page'); } }
    bubble('pre', words.hello);
    bubble('pre', places[0].task + ' Press Start task.');
    stick();
    render();
    root.preceptorFace = Object.freeze({ state: state, act: act, actions: actionList.slice() });
  } catch (err) {
    say.textContent = 'NO_DATA: the map could not be drawn. Cause: ' + err.message;
  }
})(window);
