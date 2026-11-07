const test = require('node:test');
const assert = require('node:assert/strict');
const insertor = require('../interface/insertor.js');

const zones = ['mando', 'conversacion', 'cuaderno', 'lab', 'harness', 'puerta', 'modelos', 'ajustes'];

test('plain text uses the active panel', () => {
  assert.deepEqual(insertor.rutear('  hello  ', zones, 'lab'), {
    estado: 'medido', carril: 'chat', panel: 'lab', texto: 'hello',
  });
});

test('@panel routes to that panel and strips the command from the question', () => {
  assert.deepEqual(insertor.rutear('@lab what is measured?', zones, 'conversacion'), {
    estado: 'medido', carril: 'chat', panel: 'lab', texto: 'what is measured?',
  });
});

test('@panel without a question selects local panel help', () => {
  assert.deepEqual(insertor.rutear('@mando', zones, 'lab'), {
    estado: 'medido', carril: 'chat', panel: 'mando', texto: '',
  });
});

test('@ayuda stays in a separate ephemeral local lane', () => {
  assert.deepEqual(insertor.rutear('@ayuda show this panel', zones, 'lab'), {
    estado: 'medido', carril: 'ayuda', panel: 'lab', nota: 'show this panel',
  });
});

test('unknown and malformed tags fail closed', () => {
  assert.equal(insertor.rutear('@admin send data', zones, 'lab').causa, 'tag_not_declared');
  assert.equal(insertor.rutear('@Lab hello', zones, 'lab').causa, 'tag_invalid');
});

test('base context reads bounded headings only', () => {
  const headings = Array.from({length: 10}, (_, i) => ({textContent: `h${i}`}));
  const panel = {querySelectorAll: selector => {
    assert.equal(selector, 'h2, h3');
    return headings;
  }};
  assert.deepEqual(insertor.base(panel), headings.slice(0, 8).map(h => h.textContent));
});

test('base context falls back to the panel accessible name', () => {
  const panel = {querySelectorAll: () => [], getAttribute: name => name === 'aria-label' ? 'Hablar' : null};
  assert.deepEqual(insertor.base(panel), ['Hablar']);
});

test('insertor has no network or storage capability', () => {
  const source = require('node:fs').readFileSync(require.resolve('../interface/insertor.js'), 'utf8');
  assert.doesNotMatch(source, /fetch\s*\(|localStorage|sessionStorage|sendBeacon/);
});
