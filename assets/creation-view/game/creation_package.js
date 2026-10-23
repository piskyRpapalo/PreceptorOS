(function (root) {
  'use strict';
  const SCHEMA = 'preceptoros.creation/1', MAX = 25 * 1024 * 1024;
  const names = ['frame.json', 'declaration.wav'], enc = new TextEncoder();
  const dec = new TextDecoder('utf-8', { fatal: true });
  function fail(cause) { throw new Error('NO_DATA · ' + cause); }
  function exact(value, keys, label) {
    if (!value || typeof value !== 'object' || Array.isArray(value) ||
        Object.keys(value).sort().join('|') !== keys.slice().sort().join('|')) fail(label + ' fields');
  }
  function text(value, max, label) {
    if (typeof value !== 'string' || !value.trim() || enc.encode(value).length > max ||
        dec.decode(enc.encode(value)) !== value) fail(label + ' text');
    return value;
  }
  function bytes(value) { return typeof value === 'string' ? enc.encode(value) : new Uint8Array(value); }
  function hex(value, length, label) {
    if (typeof value !== 'string' || value.length !== length || !/^[0-9a-f]+$/.test(value)) fail(label + ' hex');
    return Uint8Array.from(value.match(/../g), h => parseInt(h, 16));
  }
  function encode(value) {
    let s = ''; const b = bytes(value);
    for (let i = 0; i < b.length; i += 8192) s += String.fromCharCode.apply(null, b.subarray(i, i + 8192));
    return btoa(s);
  }
  function decode(value) {
    if (typeof value !== 'string' || value.length > MAX || value.length % 4 ||
        !/^[A-Za-z0-9+/]*={0,2}$/.test(value)) fail('base64 encoding');
    const b = Uint8Array.from(atob(value), c => c.charCodeAt(0));
    if (encode(b) !== value) fail('base64 padding');
    return b;
  }
  async function sha256(value) {
    const b = await crypto.subtle.digest('SHA-256', bytes(value));
    return Array.from(new Uint8Array(b), x => x.toString(16).padStart(2, '0')).join('');
  }
  function wav(value) {
    const b = bytes(value); if (b.length < 46) fail('WAV length');
    const d = new DataView(b.buffer, b.byteOffset, b.byteLength);
    const tag = n => String.fromCharCode.apply(null, b.subarray(n, n + 4));
    const rate = d.getUint32(24, true), size = d.getUint32(40, true);
    if (tag(0) !== 'RIFF' || tag(8) !== 'WAVE' || tag(12) !== 'fmt ' || tag(36) !== 'data' ||
        d.getUint32(4, true) !== b.length - 8 || d.getUint32(16, true) !== 16 ||
        d.getUint16(20, true) !== 1 || d.getUint16(22, true) !== 1 ||
        rate < 8000 || rate > 96000 || d.getUint32(28, true) !== rate * 2 ||
        d.getUint16(32, true) !== 2 || d.getUint16(34, true) !== 16 ||
        size !== b.length - 44 || size < 2 || size % 2) fail('WAV PCM16 mono format');
    return b;
  }
  function frame(value) {
    const b = bytes(value); if (!b.length || b.length >= 1024) fail('frame byte limit');
    const f = JSON.parse(dec.decode(b)); exact(f, ['v', 'id', 'cv', 'style', 'atoms'], 'frame');
    if (f.v !== 'preceptoros.bubble/1' || typeof f.id !== 'string' || !/^[A-Z0-9_-]{1,32}$/.test(f.id) ||
        JSON.stringify(f.cv) !== '[412,515]' || !['volume', 'etch', 'clear'].includes(f.style) ||
        !Array.isArray(f.atoms) || f.atoms.length !== 1) fail('frame schema');
    const a = f.atoms[0]; exact(a, ['k', 'i'], 'atom');
    if (a.k !== 'keepsake' || !Array.isArray(a.i) || a.i.length !== 1) fail('frame atom');
    const r = a.i[0]; exact(r, ['o', 'f', 's', 'd', 'lw', 'pts'], 'ribbon');
    if (r.o !== 'ribbon' || r.f !== 'cyan' || r.s !== 'ink' || r.d !== 0 || r.lw !== 2.5 ||
        !Array.isArray(r.pts) || r.pts.length < 2 || !r.pts.every(p => Array.isArray(p) && p.length === 2 &&
          p.every((n, i) => Number.isInteger(n) && n >= 0 && n <= f.cv[i]))) fail('frame ribbon');
    return f;
  }
  function manifest(value) {
    text(value, 16384, 'manifest'); const m = JSON.parse(value);
    exact(m, ['schema', 'author', 'description', 'voice_profile', 'files'], 'manifest');
    if (m.schema !== SCHEMA) fail('manifest schema');
    text(m.author, 256, 'author'); text(m.description, 4096, 'description'); hex(m.voice_profile, 64, 'voice profile');
    if (!Array.isArray(m.files) || m.files.length !== 2) fail('file inventory');
    m.files.forEach((f, i) => {
      exact(f, ['name', 'size', 'sha256'], 'file');
      if (f.name !== names[i] || !Number.isSafeInteger(f.size) || f.size < 1 || f.size > MAX) fail('file descriptor');
      hex(f.sha256, 64, 'file digest');
    });
    return m;
  }
  async function verify(raw) {
    if (typeof raw !== 'string') raw = dec.decode(bytes(raw));
    if (enc.encode(raw).length > MAX) fail('package byte limit');
    const p = JSON.parse(raw); exact(p, ['schema', 'manifest', 'public_key', 'signature', 'files'], 'package');
    if (p.schema !== SCHEMA) fail('package schema');
    const m = manifest(p.manifest); exact(p.files, names, 'files');
    const pub = hex(p.public_key, 64, 'public key'), sig = hex(p.signature, 128, 'signature');
    const payloads = names.map(n => decode(p.files[n]));
    for (let i = 0; i < 2; i++) if (payloads[i].length !== m.files[i].size ||
        await sha256(payloads[i]) !== m.files[i].sha256) fail('file hash or size');
    const f = frame(payloads[0]); wav(payloads[1]);
    const key = await crypto.subtle.importKey('raw', pub, 'Ed25519', false, ['verify']);
    if (!await crypto.subtle.verify('Ed25519', key, sig, enc.encode(p.manifest))) fail('author signature');
    return { id: await sha256(p.manifest), manifest: m, frame: f, audio: payloads[1], package: p };
  }
  async function prepare(input) {
    const rawFrame = typeof input.frame === 'string' ? input.frame : JSON.stringify(input.frame);
    frame(rawFrame); const audio = wav(input.audio), payloads = [bytes(rawFrame), audio], files = {}, entries = [];
    for (let i = 0; i < 2; i++) {
      files[names[i]] = encode(payloads[i]);
      entries.push({ name: names[i], size: payloads[i].length, sha256: await sha256(payloads[i]) });
    }
    const raw = JSON.stringify({ schema: SCHEMA, author: input.author, description: input.description,
      voice_profile: input.voice_profile, files: entries });
    manifest(raw);
    if (bytes(JSON.stringify({ schema: SCHEMA, manifest: raw, files, public_key: '0'.repeat(64), signature: '0'.repeat(128) })).length > MAX) fail('package byte limit');
    return { manifest: raw, files };
  }
  async function finish(prepared, publicKey, signature) {
    const p = { schema: SCHEMA, manifest: prepared.manifest, public_key: publicKey, signature, files: prepared.files };
    await verify(JSON.stringify(p)); return p;
  }
  const api = Object.freeze({ SCHEMA, MAX, verify, prepare, finish, sha256, encode, decode, wav, frame, manifest, bytes });
  if (typeof module === 'object' && module.exports) module.exports = api; else root.CreationPackage = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
