(function (root) {
  'use strict';
  var node = typeof module === 'object' && module.exports;
  var steps = [
    { id: 'key', name: 'Your key', say: 'Step 1: create your key. It signs every egg and every adoption. Tap the highlighted Profile icon, then Create my key.' },
    { id: 'beacon', name: 'The beacon', say: 'Step 2: walk to the beacon. Tap the highlighted star, accept, then tap the path icon.', reward: [100, 0, 'The beacon gives copper for two eggs.'] },
    { id: 'egg', name: 'An egg', say: 'Step 3: summon an egg. In your Profile, tap the highlighted Level 1 egg. It incubates for 20 cycles.' },
    { id: 'hatch', name: 'Hatch', say: 'Step 4: when the egg at the top is ready, tap it. It hatches and joins your Army.' },
    { id: 'fight', name: 'A battle', say: 'Step 5: open Battle and fight the highlighted Reef patrol. The battle plays by itself.', reward: [50, 0, 'The battle teaches your squad.'] },
    { id: 'node', name: 'Your node', say: 'Last step: choose your node. Hexelion and Doggee share the same numbers and show them with different eyes.' }
  ];
  var nodes = [{ id: 'hexelion', name: 'Node Hexelion', page: 'atlantis.html', look: 'the underwater world' }, { id: 'doggee', name: 'Node Doggee', page: 'zombie.html', look: 'the survival terminal' }];
  var Tut = { steps: steps, nodes: nodes };
  if (node) { module.exports = Tut; return; }

  var doc = root.document, H = root.PreceptorFaceHooks;
  if (!H || !H.economy || !H.army) { return; }
  var $ = function (id) { return doc.getElementById(id); };
  var skin = JSON.parse($('skin').textContent), start = skin.layout === 'quiet', E = null, said = -1, fought = false;

  function st() { return root.preceptorFace ? root.preceptorFace.state() : null; }
  function view() { return doc.body.dataset.view; }
  function idx() { for (var i = 0; i < steps.length; i++) { if (!isDone(i)) { return i; } } return steps.length; }
  function isDone(i) {
    var s = st(), id = steps[i].id;
    if (E.tut && E.tut.passed && E.tut.passed.indexOf(id) >= 0) { return true; }
    if (id === 'key') { return !!H.army.key(); }
    if (id === 'beacon') { return !!(s && s.done >= 1); }
    if (id === 'egg') { return H.economy.eggs().length > 0 || H.army.list().length > 0; }
    if (id === 'hatch') { return H.army.list().length > 0; }
    if (id === 'fight') { return fought; }
    return !!(E.tut && E.tut.node);
  }
  function target(i) {
    var id = steps[i].id, s = st(), v = view(), menu = $('identity-menu');
    if (id === 'key') { return v !== 'profile' ? '#tab-profile' : (menu && menu.matches(':popover-open') ? '#identity-menu button' : '#identity button'); }
    if (id === 'beacon') { return v !== 'map' ? '#tab-map' : !$('offer').hidden ? '#offer-yes' : s && s.walking ? null : s && s.path ? '#follow' : '#start'; }
    if (id === 'egg') { return v !== 'profile' ? '#tab-profile' : '[data-egg="tc1"]'; }
    if (id === 'hatch') { return '#eggs .egg.go'; }
    if (id === 'fight') { return v !== 'battle' ? '#tab-battle' : doc.body.dataset.battle === 'on' ? null : '[data-foe="arrecife"]'; }
    return null;
  }

  function mark(sel) {
    Array.prototype.forEach.call(doc.querySelectorAll('.tut-target'), function (n) { n.classList.remove('tut-target'); });
    if (sel) { Array.prototype.forEach.call(doc.querySelectorAll(sel), function (n) { n.classList.add('tut-target'); }); }
  }

  function list(i) {
    var ol = $('tut-steps');
    while (ol.firstChild) { ol.removeChild(ol.firstChild); }
    steps.forEach(function (x, k) {
      var li = doc.createElement('li'), state = k < i ? 'done' : k === i ? 'now' : 'next';
      li.dataset.state = state; li.textContent = x.name;
      li.setAttribute('aria-label', x.name + ': ' + (state === 'done' ? 'done' : state === 'now' ? 'now' : 'still to do'));
      ol.appendChild(li);
    });
  }

  function choose() {
    var box = $('nodes');
    box.hidden = later;
    doc.body.dataset.tut = '';
    mark(null);
  }

  function pass(i) {
    var x = steps[i];
    E.tut = E.tut || { passed: [] };
    if (E.tut.passed.indexOf(x.id) >= 0) { return; }
    E.tut.passed.push(x.id);
    if (x.reward) { H.economy.grant(x.reward[0], x.reward[1], x.reward[2]); } else { H.economy.save(); }
  }

  function update() {
    if (!E) { return; }
    var box = $('tut');
    if (E.tut && (E.tut.done || E.tut.skipped)) { box.hidden = true; doc.body.dataset.tut = ''; mark(null); if (start && E.tut.done && !E.tut.node) { choose(); } return; }
    if (!start) { box.hidden = true; $('tut-away').hidden = false; return; }
    for (var k = 0; k < steps.length - 1; k++) { if (isDone(k)) { pass(k); } else { break; } }
    var i = idx();
    box.hidden = false;
    list(i);
    if (i >= steps.length - 1) {
      $('tut-now').textContent = 'Now: ' + steps[steps.length - 1].name + '.';
      if (said !== i) { said = i; H.bubble(steps[i].say); H.say(steps[i].say); }
      E.tut.done = true; H.economy.save(); choose(); return;
    }
    var x = steps[i], sel = target(i), wait = x.id === 'hatch' && !doc.querySelector('#eggs .egg.go');
    $('tut-now').textContent = 'Step ' + (i + 1) + ' of ' + steps.length + ': ' + x.name + (wait ? ' · waiting for the egg' : '') + '.';
    doc.body.dataset.tut = 'on';
    mark(sel);
    if (said !== i) { said = i; H.bubble(x.say); H.say(x.say); }
  }

  function skip() {
    E.tut = Object.assign(E.tut || { passed: [] }, { skipped: true });
    H.economy.save();
    H.bubble('Tutorial skipped. You keep what you have; the tutorial rewards stay unearned. Choose your node.');
    $('tut').hidden = true; doc.body.dataset.tut = ''; mark(null);
    if (start) { choose(); }
  }
  function go(n) { E.tut = Object.assign(E.tut || { passed: [] }, { node: n.id }); H.economy.save().then(function () { root.location.href = n.page; }); }

  nodes.forEach(function (n) { var b = $('node-' + n.id); if (b) { b.addEventListener('click', function () { go(n); }); } });
  $('tut-skip').addEventListener('click', skip);
  var later = false;
  $('node-later').addEventListener('click', function () { later = true; $('nodes').hidden = true; });
  var away = $('tut-away-skip');
  if (away) { away.addEventListener('click', function () { skip(); $('tut-away').hidden = true; }); }
  doc.addEventListener('preceptor:battle', function () { fought = true; update(); });
  doc.addEventListener('preceptor:identity', update);
  new root.MutationObserver(update).observe(doc.body, { attributes: true, attributeFilter: ['data-view', 'data-battle'] });
  new root.MutationObserver(update).observe($('packet'), { childList: true, characterData: true, subtree: true });
  new root.MutationObserver(update).observe($('offer'), { attributes: true, attributeFilter: ['hidden'] });
  new root.MutationObserver(update).observe($('eggs'), { childList: true, subtree: true });
  var menu = $('identity-menu');
  if (menu) { menu.addEventListener('toggle', update); }
  H.army.on(update);
  H.economy.on(function (state) { E = state; update(); });
  H.tutorial = { update: update, skip: skip, step: function () { return E ? idx() : null; } };
})(typeof module === 'object' && module.exports ? this : window);
