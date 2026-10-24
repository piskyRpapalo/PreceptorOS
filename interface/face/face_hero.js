(function (root) {
  'use strict';
  var V = 'preceptoros.bubble/1';
  function heroFrame(skin, clase, dir) {
    var h = skin.hero, d = dir === 1 ? 1 : -1, x = function (v) { return 60 + (v - 60) * d; }, visor = clase === 'coral' ? 'vermilion.base' : 'cyan';
    return { v: V, id: 'hero', t: 0, cv: [120, 120], atoms: [{ k: 'soldier', r: 'you: a space soldier in uniform and a full helmet, visor ' + (clase === 'coral' ? 'coral' : 'sea blue'), i: [
      { o: 'ribbon', pts: [[x(52), 112], [x(53), 88]], s: h.uniform, lw: 10 },
      { o: 'ribbon', pts: [[x(68), 112], [x(67), 88]], s: h.uniform, lw: 10 },
      { o: 'blob', x: x(46), y: 66, rx: 11, ry: 17, rough: 0, f: h.pack },
      { o: 'blob', x: 60, y: 72, rx: 18, ry: 22, rough: 0, f: h.uniform },
      { o: 'ribbon', pts: [[x(72), 62], [x(82), 74], [x(80), 86]], s: h.uniform, lw: 9 },
      { o: 'blob', x: 60, y: 38, rx: 21, ry: 20, rough: 0, f: h.helmet },
      { o: 'blob', x: x(66), y: 39, rx: 13, ry: 8, rough: 0, f: visor },
      { o: 'arcs', x: x(68), y: 37, r: [5, 5], n: 1, arc: 70, ph: 200, s: 'paper', lw: 3 }] }],
      bands: [h.uniform, h.pack, h.helmet, visor, 'paper', 'ink'], change: ['rest'], sound: 'NO_DATA', soundCause: 'silent', motion: 'steps when you move' };
  }
  var Hero = { heroFrame: heroFrame };
  if (typeof module === 'object' && module.exports) { module.exports = Hero; } else { root.PreceptorHero = Hero; }
})(typeof module === 'object' && module.exports ? this : window);
