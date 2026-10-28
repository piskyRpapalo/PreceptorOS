(function (raiz) {
  'use strict';

    function proyecta(col, fila, W) {
    var H = W / 2;
    return { x: (col - fila) * W / 2, y: (col + fila) * H / 2 };
  }
    function aCelda(x, y, W) {
    var H = W / 2, a = x / (W / 2), b = y / (H / 2);
    return { col: (a + b) / 2, fila: (b - a) / 2 };
  }
    function celdaDe(x, y, W) {
    var c = aCelda(x, y, W);
    return { col: Math.round(c.col), fila: Math.round(c.fila) };
  }
    function vertices(col, fila, W) {
    var p = proyecta(col, fila, W), H = W / 2;
    return [[p.x, p.y - H / 2], [p.x + W / 2, p.y], [p.x, p.y + H / 2], [p.x - W / 2, p.y]];
  }
    function ancla(col, fila, huella, W) {
    var n = Math.max(1, huella || 1);
    return proyecta(col + (n - 1) / 2, fila + (n - 1) / 2, W);
  }
    function profundidad(o) { var n = Math.max(1, o.huella || 1); return o.col + o.fila + 2 * (n - 1); }
  function ordena(lista) {
    return lista.map(function (o, i) { return { o: o, i: i }; }).sort(function (a, b) {
      return (profundidad(a.o) - profundidad(b.o)) || (a.o.col - b.o.col) || ((a.o.capa || 0) - (b.o.capa || 0)) || (a.i - b.i);
    }).map(function (x) { return x.o; });
  }

  var IsometricFloor = { proyecta: proyecta, aCelda: aCelda, celdaDe: celdaDe, vertices: vertices, ancla: ancla,
                         profundidad: profundidad, ordena: ordena };
  if (typeof module === 'object' && module.exports) { module.exports = IsometricFloor; } else { raiz.IsometricFloor = IsometricFloor; }
})(this);
