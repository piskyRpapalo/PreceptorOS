const test = require('node:test');
const assert = require('node:assert/strict');
const Sting = require('./interface/sting.js');

function runtime(reduced = false) {
  const records = { contexts: 0, oscillators: [], gains: [] };
  class AudioContext {
    constructor() {
      records.contexts++;
      this.state = 'running';
      this.currentTime = 10;
      this.destination = {};
    }
    createOscillator() {
      const item = { frequency: { values: [], setValueAtTime(value, time) { this.values.push([value, time]); } }, connections: [], starts: [], stops: [] };
      item.connect = (target) => item.connections.push(target);
      item.start = (time) => item.starts.push(time);
      item.stop = (time) => item.stops.push(time);
      records.oscillators.push(item);
      return item;
    }
    createGain() {
      const item = { gain: { values: [], setValueAtTime(value, time) { this.values.push([value, time]); }, exponentialRampToValueAtTime(value, time) { this.values.push([value, time]); } }, connections: [] };
      item.connect = (target) => item.connections.push(target);
      records.gains.push(item);
      return item;
    }
  }
  return { records, host: { AudioContext, matchMedia: () => ({ matches: reduced }) } };
}

test('missing Web Audio returns a caused no-data result', async () => {
  const result = await Sting.tocar({}, { matchMedia: () => ({ matches: false }) });
  assert.equal(result.estado, 'nodata');
  assert.match(result.causa, /Web Audio/);
});

test('reduced motion suppresses sound before opening audio', async () => {
  const { host, records } = runtime(true);
  const result = await Sting.tocar({}, host);
  assert.equal(result.estado, 'inactivo');
  assert.equal(records.contexts, 0);
  assert.equal(records.oscillators.length, 0);
});

test('local FM sting uses eight pentatonic notes under one second', async () => {
  const { host, records } = runtime();
  const result = await Sting.tocar({}, host);
  const carriers = records.oscillators.filter((oscillator) => oscillator.frequency.values[0][0] < 600 && oscillator.connections.some((target) => target === records.gains[0]));
  assert.equal(result.estado, 'sonado');
  assert.equal(result.base_hz, 220);
  assert.equal(result.duracion_ms, 560);
  assert.ok(result.duracion_ms < 1000);
  assert.equal(result.notas, 8);
  assert.equal(carriers.length, 8);
  assert.deepEqual(carriers.map((oscillator) => oscillator.frequency.values[0][0]),
    [220, 246.94165062806206, 277.1826309768721, 329.6275569128699, 369.99442271163446, 440, 493.8833012561241, 554.3652619537442]);
  assert.equal(result.suboctava_hz, null);
  assert.match(result.causa_suboctava, /tension/);
});

test('110 Hz is only scheduled when tension is explicit', async () => {
  const { host, records } = runtime();
  const result = await Sting.tocar({ tension: true }, host);
  const frequencies = records.oscillators.flatMap((oscillator) => oscillator.frequency.values.map((entry) => entry[0]));
  assert.equal(result.suboctava_hz, 110);
  assert.ok(frequencies.includes(110));
});
