(function (root) {
  'use strict';
  var doc = root.document, H = root.PreceptorFaceHooks, Bt = root.PreceptorBattle;
  if (!H || !Bt || !H.army) { return; }
  var $ = function (id) { return doc.getElementById(id); };
  var fight = Bt.create(), loop = 0, playing = false, list = Bt.patrols(), wins = {};
  function quiet() { return root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches; }
  function verdict(g) { return g === 'asalto' ? 'you win' : g === 'defensa' ? 'the patrol holds' : 'a draw'; }

  function cards() {
    var ul = $('foes'), squad = H.army.squad();
    while (ul.firstChild) { ul.removeChild(ul.firstChild); }
    list.forEach(function (p) {
      var li = doc.createElement('li'), b = doc.createElement('button');
      b.type = 'button'; b.className = 'foe'; b.dataset.foe = p.id;
      b.innerHTML = '<b></b><span></span>';
      b.firstChild.textContent = p.name;
      b.lastChild.textContent = p.n + ' waves · Level ' + p.tc.slice(2) + (wins[p.id] ? ' · beaten' : '');
      b.setAttribute('aria-label', 'Fight the ' + p.name + ': ' + p.n + ' waves of level ' + p.tc.slice(2) + (wins[p.id] ? ', already beaten' : ''));
      b.disabled = !squad.length || (fight.b.on && !fight.done());
      b.addEventListener('click', function () { start(p); });
      li.appendChild(b); ul.appendChild(li);
    });
    $('foe-note').textContent = squad.length ? 'Your squad: ' + squad.length + ' of up to 10 waves. Choose a patrol to fight; the battle plays by itself.' : 'You need at least one wave: NO_DATA (Army empty). Hatch an egg from your Profile.';
  }

  function update() {
    var s = fight.summary(), on = s.on && !s.result;
    doc.body.dataset.battle = s.on ? 'on' : '';
    $('b-pause').textContent = playing ? 'Pause' : 'Play';
    $('b-pause').disabled = !on; $('b-step').disabled = !on || playing;
    $('b-back').classList.toggle('go', !!s.result);
    Array.prototype.forEach.call(doc.querySelectorAll('[data-form]'), function (b) { b.setAttribute('aria-pressed', String(b.dataset.form === s.form)); });
    var ul = $('b-life');
    while (ul.firstChild) { ul.removeChild(ul.firstChild); }
    s.troops.forEach(function (x) {
      var li = doc.createElement('li'), mine = x.side === 'yours';
      if (mine && on && !s.orders.length && x.life > 0) {
        var b = doc.createElement('button'); b.type = 'button'; b.className = 'mini2';
        b.textContent = 'Withdraw ' + x.name + ' (' + x.life + ')';
        b.addEventListener('click', function () { if (fight.withdraw(x.i)) { H.bubble('Order: withdraw your ' + x.name + ' before tick ' + fight.b.orders[0].tick + '. It fits the receipt.'); update(); } });
        li.appendChild(b);
      } else { li.textContent = (mine ? 'Yours · ' : 'Patrol · ') + x.name + ' ' + x.life + '/' + x.max; }
      ul.appendChild(li);
    });
    $('b-tick').textContent = s.on ? (s.result ? 'Verdict after ' + s.result.rondas + ' ticks: ' + verdict(s.result.gana) + '.' : 'Tick ' + s.tick + ' of 40') : '';
    $('b-receipt').textContent = s.receipt || '';
    cards();
    H.render();
  }

  function finish() {
    var s = fight.summary();
    playing = false;
    H.panel.mark('battle', s.verified && s.verified.ok ? 'LIVE' : 'NO_DATA');
    if (s.won) { wins[s.patrol] = true; }
    H.bubble('Battle over: ' + verdict(s.result.gana) + ' after ' + s.result.rondas + ' ticks. Receipt (' + s.receipt.length + ' B), replayed from tick 0: ' + (s.verified.ok ? 'verified.' : 'NO_DATA, ' + s.verified.motivo + '.'));
    H.say('Battle over: ' + verdict(s.result.gana) + '.');
    H.buzz([40, 30, 40]);
    if (s.won && H.won) { H.won(); }
    doc.dispatchEvent(new root.CustomEvent('preceptor:battle', { detail: s }));
  }

  function step() {
    if (!fight.step()) { return; }
    var s = fight.summary();
    H.say('Tick ' + s.tick + '.');
    if (fight.done()) { finish(); }
    update();
  }
  function play() {
    root.cancelAnimationFrame(loop);
    playing = true;
    if (quiet()) { while (!fight.done()) { step(); } playing = false; update(); return; }
    var n = 0;
    function tick() { if (!playing) { return; } n++; if (n % 20 === 0) { step(); } if (!fight.done() && playing) { loop = root.requestAnimationFrame(tick); } }
    loop = root.requestAnimationFrame(tick);
    update();
  }

  function start(p) {
    root.cancelAnimationFrame(loop);
    if (!fight.begin(p, H.army.squad())) { return; }
    H.focus(Bt.field);
    H.panel.mark('battle', 'LIVE');
    H.bubble('You face the ' + p.name + ' (' + p.n + ' waves). Your squad stands in ' + Bt.formNames[fight.b.form] + '. Rounds are seeded, so this battle replays the same for everyone.');
    if (H.sound()) { fight.sonar(root.AtlasSintesis); }
    play();
  }
  function back() { root.cancelAnimationFrame(loop); playing = false; fight.b.on = false; update(); }

  $('b-pause').addEventListener('click', function () { if (playing) { playing = false; root.cancelAnimationFrame(loop); update(); } else { play(); } });
  $('b-step').addEventListener('click', step);
  $('b-back').addEventListener('click', back);
  Array.prototype.forEach.call(doc.querySelectorAll('[data-form]'), function (b) { b.addEventListener('click', function () { fight.form(b.dataset.form); update(); }); });
  H.army.on(cards);
  new root.MutationObserver(function () { if (doc.body.dataset.view !== 'battle' && fight.done()) { back(); } }).observe(doc.body, { attributes: true, attributeFilter: ['data-view'] });
  H.extra(function (g, toScreen, z) { fight.paint(g, toScreen, z, quiet()); }, function () { return fight.b.on ? fight.frame() : null; });
  H.battle = { summary: fight.summary, start: function (id) { var p = list.filter(function (x) { return x.id === id; })[0]; if (p) { start(p); } }, step: step, play: play, back: back, patrols: function () { return list; } };
  update();
})(window);
