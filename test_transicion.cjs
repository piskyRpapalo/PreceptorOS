const test = require('node:test');
const assert = require('node:assert/strict');
const T = require('./interface/transicion.js');

test('desenvuelve fase antes de interpolar el arco corto', () => {
  const a = [{ k: 1, ax: 2, ay: 0, phi: Math.PI - 0.1 }];
  const b = [{ k: 1, ax: 4, ay: 0, phi: -Math.PI + 0.1 }];
  const mid = T.interpolar(a, b, 0.5);
  assert.ok(Math.abs(Math.abs(mid[0].phi) - Math.PI) < 1e-9);
  assert.equal(mid[0].ax, 3);
});

test('el espejo reutiliza interpolador y niega solo ax', () => {
  const a = [{ k: 1, ax: 2, ay: 3, phi: 0.2 }];
  const b = [{ k: 1, ax: 4, ay: 5, phi: 0.8 }];
  const direct = T.interpolar(a, b, 0.25);
  const mirror = T.interpolar(a, b, 0.25, { espejo: true });
  assert.equal(mirror[0].ax, -direct[0].ax);
  assert.equal(mirror[0].ay, direct[0].ay);
  assert.equal(mirror[0].phi, direct[0].phi);
});

test('mismo vector y tau serializan los mismos bytes; tau fuera de rango rechaza', () => {
  const v = [{ k: 1, ax: 0.125, ay: -0.25, phi: 1.25 }];
  assert.equal(T.bytes(T.interpolar(v, v, 0.375)), T.bytes(T.interpolar(v, v, 0.375)));
  assert.throws(() => T.interpolar(v, v, 1.01), RangeError);
});
