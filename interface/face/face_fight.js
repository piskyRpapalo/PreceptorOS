(function (root) {
  'use strict';
  var doc = root.document, H = root.PreceptorFaceHooks, Bt = root.PreceptorBattle;
  if (!H || !Bt) { return; }
  var $ = function (id) { return doc.getElementById(id); };
  var fight = Bt.create(), loop = 0, field = [486, 200];
  function quiet() { return root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches; }

  function update() {
    var s = fight.summary(), on = s.on && !s.result;
    $('b-start').textContent = s.on ? 'Start again' : 'Start battle';
    $('b-step').disabled = !on; $('b-play').disabled = !on;
    Array.prototype.forEach.call(doc.querySelectorAll('#b-withdraw button'), function (b, i) { b.textContent = 'Withdraw ' + s.troops[i].name; b.disabled = !on || s.orders.length >= 1 || !(s.troops[i] && s.troops[i].life > 0); });
    Array.prototype.forEach.call(doc.querySelectorAll('[data-form]'), function (b) { b.setAttribute('aria-pressed', String(b.dataset.form === s.form)); });
    $('b-life').innerHTML = '';
    s.troops.forEach(function (x) { var li = doc.createElement('li'); li.textContent = (x.side === 'yours' ? 'Yours · ' : 'Enemy · ') + x.name + ': life ' + x.life + ' of ' + x.max; $('b-life').appendChild(li); });
    $('b-tick').textContent = s.on ? 'Tick ' + s.tick + (s.orders.length ? ' · order: withdraw troop ' + (s.orders[0].i + 1) + ' before tick ' + s.orders[0].tick : '') + (s.result ? ' · verdict: ' + verdict(s.result.gana) : '') : 'No battle yet: NO_DATA.';
    $('b-receipt').textContent = s.receipt ? s.receipt : '';
    H.render();
  }
  function verdict(g) { return g === 'defensa' ? 'your squad holds' : g === 'asalto' ? 'the enemy wave wins' : 'a draw'; }

  function finish() {
    var s = fight.summary();
    H.panel.mark('battle', s.verified && s.verified.ok ? 'LIVE' : 'NO_DATA');
    H.bubble('Battle over: ' + verdict(s.result.gana) + ' after ' + s.result.rondas + ' ticks (life per mille ' + s.result.vida_por_mil.join(' vs ') + '). Receipt, ' + s.receipt.length + ' B: ' + s.receipt + ' Replayed from tick 0: ' + (s.verified.ok ? 'verified.' : 'NO_DATA, ' + s.verified.motivo + '.'));
    H.say('Battle over: ' + verdict(s.result.gana) + '. The receipt is in the chat and verified by replay.');
    H.buzz([40, 30, 40]);
    if (s.result.gana === 'defensa' && H.won) { H.won(); }
  }

  function start() {
    root.cancelAnimationFrame(loop);
    fight.begin();
    H.focus(field);
    doc.body.dataset.battle = 'on';
    H.panel.mark('battle', 'LIVE');
    H.bubble('A wave rises at the rift. ' + (root.PreceptorArmySquad && root.PreceptorArmySquad.length ? 'Your adopted waves' : 'Three Codex troops (your Army is empty)') + ' answer in ' + Bt.formNames[fight.b.form] + ' formation. Rounds are seeded: the same battle replays the same for everyone.');
    H.say('Battle at the rift, tick 0. Press Next tick or Play to the end.');
    if (H.sound()) { fight.sonar(root.AtlasSintesis); }
    var n = 0;
    function grow() { n++; fight.b.reveal = n; update(); if (n < 36 && fight.b.reveal) { loop = root.requestAnimationFrame(grow); } else { fight.b.reveal = 0; update(); } }
    if (quiet()) { update(); } else { loop = root.requestAnimationFrame(grow); }
  }
  function step() {
    if (!fight.step()) { return; }
    var s = fight.summary();
    H.say('Tick ' + s.tick + ': ' + s.troops.map(function (x) { return x.name + ' ' + x.life; }).join(', ') + '.');
    if (fight.done()) { finish(); }
    update();
  }
  function play() {
    root.cancelAnimationFrame(loop);
    if (quiet()) { while (!fight.done()) { step(); } return; }
    var n = 0;
    function tick() { n++; if (n % 24 === 0) { step(); } if (!fight.done()) { loop = root.requestAnimationFrame(tick); } }
    loop = root.requestAnimationFrame(tick);
  }

  $('b-start').addEventListener('click', start);
  $('b-back').addEventListener('click', function () { doc.body.dataset.battle = ''; });
  $('b-step').addEventListener('click', step);
  $('b-play').addEventListener('click', play);
  Array.prototype.forEach.call(doc.querySelectorAll('#b-withdraw button'), function (b, i) {
    b.addEventListener('click', function () { if (fight.withdraw(i)) { H.bubble('Order: withdraw ' + fight.troops()[i].name + ' before tick ' + fight.b.orders[0].tick + '. It fits the 200-byte receipt.'); update(); } });
  });
  Array.prototype.forEach.call(doc.querySelectorAll('[data-form]'), function (b) { b.addEventListener('click', function () { fight.form(b.dataset.form); update(); }); });
  H.extra(function (g, toScreen, z) { fight.paint(g, toScreen, z, quiet()); }, function () { return fight.b.on ? fight.frame() : null; });
  H.battle = { summary: fight.summary, start: start, step: step, play: play, withdraw: function (i) { return fight.withdraw(i); } };
  update();
})(window);
