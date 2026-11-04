(function (root) {
  'use strict';
  var doc = root.document, $ = function (id) { return doc.getElementById(id); };
  var pending = false, lastAnswer = '', voice = null, readGeneration = 0;
  function status(text) { $('connection').textContent = text; }
  function turn(who, text, person) {
    var li = doc.createElement('li'), speaker = doc.createElement('span'), body = doc.createElement('p');
    li.dataset.role = person ? 'person' : 'model'; speaker.className = 'speaker'; body.className = 'turn-text';
    speaker.textContent = who; body.textContent = text; li.append(speaker, body); $('thread').append(li);
    if (!person) { lastAnswer = who + '. ' + text; $('read-last').disabled = false; }
  }
  function responseTurn(reply) {
    if (!reply || reply.estado === 'NO_DATA' || typeof reply.texto !== 'string' || !reply.texto.trim() || typeof reply.voz !== 'string' || !reply.voz.trim()) {
      throw new Error('No attributed model answer was returned');
    }
    turn(reply.voz + ' · local app', reply.texto, false);
    return reply;
  }
  async function refresh() {
    if (pending) return;
    pending = true; $('refresh').disabled = true;
    try {
      var r = await root.fetch('/api/lab', { cache: 'no-store' }), d = await r.json();
      if (!r.ok || !d.conversacion || !Array.isArray(d.conversacion.mensajes)) throw new Error('Local thread unavailable');
      $('thread').replaceChildren(); lastAnswer = ''; $('read-last').disabled = true;
      d.conversacion.mensajes.forEach(function (m) {
        if (typeof m.texto === 'string' && typeof m.quien === 'string') turn(m.quien, m.texto, m.quien === 'soberano');
      });
      status('Local thread read. ' + d.conversacion.mensajes.length + ' attributed records.');
    } catch (_) { status('NO_DATA · local thread could not be read.'); }
    finally { pending = false; $('refresh').disabled = false; }
  }
  $('refresh').addEventListener('click', refresh);
  $('message-form').addEventListener('submit', async function (e) {
    e.preventDefault(); var text = $('message').value.trim();
    if (pending || !text || text.length > 4000) return;
    pending = true; $('send').disabled = true; $('refresh').disabled = true;
    turn('You · explicit send', text, true); status('Waiting for the local orchestrator.');
    $('receipt').textContent = 'Request dispatched. Result pending; do not resend blindly.';
    try {
      var r = await root.fetch('/api/lab', { method: 'POST', cache: 'no-store', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ texto: text }) });
      var d = await r.json();
      if (!r.ok) throw new Error('Local request denied');
      var reply = responseTurn(d.respuesta);
      $('message').value = ''; status('Answer received from the local orchestrator.');
      $('receipt').textContent = 'Speaker: ' + reply.voz + '; channel: ' + (reply.canal || 'NO_DATA') + '; sequence: ' + (Number.isSafeInteger(reply.n) ? reply.n : 'NO_DATA') + '. Local app result; no tower attribution.';
    } catch (_) {
      status('NO_DATA · no attributed answer confirmed.');
      $('receipt').textContent = 'UNKNOWN · request was dispatched, result not confirmed. Check the local thread before sending again.';
    } finally { pending = false; $('send').disabled = false; $('refresh').disabled = false; }
  });
  var memoryPending = false;
  function validSource(source) {
    return source && Number.isSafeInteger(source.id) && source.id > 0 &&
      typeof source.updated_at === 'string' && source.updated_at.trim() &&
      typeof source.sha256 === 'string' && /^[a-f0-9]{64}$/.test(source.sha256) &&
      typeof source.texto === 'string' && source.texto.trim();
  }
  function showSources(sources) {
    $('memory-results').replaceChildren();
    sources.forEach(function (source) {
      var row = doc.createElement('li'), citation = doc.createElement('p'), text = doc.createElement('p');
      citation.textContent = 'Memory #' + source.id + ' · ' + source.updated_at + ' · SHA-256 ' + source.sha256;
      text.textContent = source.texto; text.className = 'turn-text';
      row.append(citation, text); $('memory-results').append(row);
    });
  }
  async function memoryRequest(path) {
    var query = $('memory-query').value.trim();
    if (memoryPending || !query || query.length > 600) return null;
    memoryPending = true; $('memory-search').disabled = true; $('memory-decision').disabled = true;
    try {
      var response = await root.fetch(path, { method: 'POST', cache: 'no-store', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ consulta: query }) });
      var raw = await response.text();
      if (new TextEncoder().encode(raw).length >= 1024) throw new Error('Response exceeds the byte limit');
      var data = JSON.parse(raw);
      if (!response.ok || !data || typeof data !== 'object') throw new Error('Local request denied');
      return data;
    } finally { memoryPending = false; $('memory-search').disabled = false; $('memory-decision').disabled = false; }
  }
  $('memory-form').addEventListener('submit', async function (event) {
    event.preventDefault();
    if (memoryPending || !$('memory-query').value.trim()) return;
    $('memory-status').textContent = 'Searching local memory…'; showSources([]);
    try {
      var data = await memoryRequest('/api/hexelion/search');
      if (!data || data.esquema !== 'preceptoros.memory-search/1') throw new Error('Invalid search response');
      if (data.estado === 'NO_DATA' && typeof data.causa === 'string' && data.causa.trim()) {
        $('memory-status').textContent = 'NO_DATA · ' + data.causa; return;
      }
      if (data.estado !== 'MEASURED' || !Array.isArray(data.fuentes) || !data.fuentes.length ||
          !data.fuentes.every(validSource) || !Number.isSafeInteger(data.fuera) || data.fuera < 0 || typeof data.completo !== 'boolean') throw new Error('Invalid source metadata');
      showSources(data.fuentes);
      $('memory-status').textContent = data.fuentes.length + ' local source(s). ' + (data.completo ? 'Complete within this search.' : 'Partial results: ' + data.fuera + ' outside the budget.') + ' No model called.';
    } catch (_) { $('memory-status').textContent = 'NO_DATA · local memory search could not be verified.'; showSources([]); }
  });
  $('read-last').addEventListener('click', async function () {
    if (!lastAnswer) return;
    var generation = ++readGeneration, text = lastAnswer, source = $('voice-source').value;
    try {
      if (!root.HexelionNativeVoice) await import('/native_voice.js');
      if (generation !== readGeneration) return;
      voice = root.HexelionNativeVoice;
      if (!voice) throw new Error('reader unavailable');
      voice.read(text, doc.documentElement.lang, function (s) { if (generation === readGeneration) $('voice-state').textContent = s; }, source);
    } catch (_) { if (generation === readGeneration) $('voice-state').textContent = 'NO_DATA · local native reader is unavailable.'; }
  });
  $('stop-reading').addEventListener('click', function () {
    readGeneration++; if (voice) voice.stop(); $('voice-state').textContent = 'Reading stopped.';
  });
  function describePosition(target) {
    if (!target || !target.getBoundingClientRect || target === doc.body) return;
    var r = target.getBoundingClientRect();
    $('position').textContent = 'Position: ' + (target.getAttribute('aria-label') || target.textContent || target.id).trim().slice(0, 64) + '; x ' + Math.round(r.x + r.width / 2) + ', y ' + Math.round(r.y + r.height / 2) + ' CSS px.';
  }
  doc.addEventListener('focusin', function (e) { describePosition(e.target); });
  root.addEventListener('resize', function () { describePosition(doc.activeElement); });
  if (['localhost', '127.0.0.1', '[::1]'].includes(root.location.hostname)) {
    $('aula-link').hidden = false; $('aula-state').textContent = 'Separate authenticated aula. Availability is not inferred.';
  }
  root.addEventListener('pagehide', function () { readGeneration++; if (voice) voice.stop(); });
  if ('serviceWorker' in root.navigator) root.navigator.serviceWorker.register('/sw.js').catch(function () {});
})(globalThis);
