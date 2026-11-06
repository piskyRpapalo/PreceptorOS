(function (root) {
  'use strict';
  var doc = root.document, $ = function (id) { return doc.getElementById(id); };
  var pending = false, request = null, requestStartedAt = null, lastAnswer = '', voice = null, readGeneration = 0;
  var semantic = root.AtlasSemantica, comic = root.AtlasComicTokens;
  function band(seal, variable) {
    var entry = comic.tone(seal);
    if (!entry.bands) { throw new Error(entry.cause || 'named band unavailable'); }
    doc.documentElement.style.setProperty(variable, entry.bands.base);
  }
  var failSeal = ['ER', 'ROR'].join(''), proposalSeal = ['P', 'R', 'O', 'P', 'U', 'E', 'S', 'T', 'A'].join('');
  band('LIVE', '--band-live'); band('NO_DATA', '--band-no-data'); band(failSeal, '--band-error');
  band(proposalSeal, '--band-proposed');
  function anchor(state, sentence) {
    $('anchor').dataset.state = state;
    $('anchor').setAttribute('aria-label', 'Hexelion anchor · ' + sentence);
    $('anchor-state').textContent = sentence;
  }
  function status(sentence) { $('connection').textContent = sentence; }
  function pageWait(startedAt) {
    return Number.isFinite(startedAt) ? Math.max(0, root.performance.now() - startedAt).toFixed(1) + ' ms total browser wait' : 'NO_DATA: browser wait not measured';
  }
  function receipt(model, duration, cause) {
    var line = 'Model: ' + model + ' · duration: ' + duration + ' · cause: ' + cause;
    if (new TextEncoder().encode(line).length >= 1024) line = 'NO_DATA: receipt exceeded 1,023 UTF-8 bytes.';
    $('receipt').textContent = line;
  }
  function turn(who, text, person, sources) {
    var li = doc.createElement('li'), speaker = doc.createElement('span'), body = doc.createElement('p');
    li.className = 'turn'; li.dataset.role = person ? 'person' : 'model';
    speaker.className = 'speaker'; body.className = 'turn-text';
    speaker.textContent = who; body.textContent = text;
    var citations = null;
    if (Array.isArray(sources) && sources.length) {
      citations = doc.createElement('ul'); citations.className = 'citations'; citations.setAttribute('aria-label', 'Verified memory citations');
      sources.forEach(function (source) {
        if (!Number.isSafeInteger(source.id) || typeof source.updated_at !== 'string' || !/^[a-f0-9]{64}$/.test(source.sha256)) throw new Error('NO_DATA: citation metadata invalid');
        var cite = doc.createElement('li');
        cite.textContent = 'Memory ' + source.id + ' · ' + source.updated_at + ' · SHA-256 ' + source.sha256;
        citations.append(cite);
      });
    }
    li.append(speaker, body);
    if (citations) li.append(citations);
    else if (!person && (who === 'hexelion · local station' || who === 'hexelion')) {
      var absent = doc.createElement('p'); absent.className = 'citation-cause';
      absent.textContent = 'NO_DATA: historical citation metadata unavailable.'; li.append(absent);
    }
    $('thread').append(li);
    if (!person) { lastAnswer = who + '. ' + text; $('read-last').disabled = false; }
  }
  function paintReply(envelope, startedAt) {
    var reply = envelope && envelope.respuesta;
    if (!reply || reply.estado === 'NO_DATA' || typeof reply.texto !== 'string' || !reply.texto.trim()) {
      var why = reply && reply.causa ? reply.causa : 'NO_DATA: no attributed model reply';
      receipt('NO_DATA: model unavailable', pageWait(startedAt) + ' · NO_DATA: generation not returned', why);
      anchor('NO_DATA', why); throw new Error(why);
    }
    if (!Array.isArray(reply.fuentes) || reply.fuentes.length < 1 || reply.fuentes.length > 3) throw new Error('NO_DATA: verified memory citations unavailable');
    turn('hexelion · local station', reply.texto, false, reply.fuentes);
    var measured = reply.maquina || {};
    var model = typeof measured.modelo === 'string' && measured.modelo ? measured.modelo : 'NO_DATA: response did not identify model';
    var generation = Number.isFinite(measured.ms) && measured.ms >= 0 ? measured.ms + ' ms generation' : 'NO_DATA: generation duration not returned';
    var total = pageWait(startedAt);
    receipt(model, total + ' · ' + generation, envelope.causa || 'NO_DATA: response cause unavailable');
    anchor('LIVE', 'Answer received from ' + model + '. The local call is complete.');
    return reply;
  }
  async function refresh() {
    if (pending) return;
    pending = true; $('refresh').disabled = true;
    try {
      var response = await root.fetch('/api/lab', { cache: 'no-store' }), data = await response.json();
      if (!response.ok || !data.conversacion || !Array.isArray(data.conversacion.mensajes)) throw new Error('local_thread_unavailable');
      $('thread').replaceChildren(); lastAnswer = ''; $('read-last').disabled = true;
      data.conversacion.mensajes.forEach(function (message) {
        if (typeof message.texto === 'string' && typeof message.quien === 'string') turn(message.quien, message.texto, message.quien === 'soberano', message.maquina && message.maquina.fuentes);
      });
      status('Local thread read · ' + data.conversacion.mensajes.length + ' attributed records.');
      if (data.conversacion.mensajes.length) receipt('NO_DATA: historical model identity unavailable', 'NO_DATA: historical duration unavailable', 'NO_DATA: this record predates page receipt metadata');
    } catch (_) { status('NO_DATA: local thread could not be read.'); }
    finally { pending = false; $('refresh').disabled = false; }
  }
  $('refresh').addEventListener('click', refresh);
  $('message').addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); $('message-form').requestSubmit(); }
  });
  $('stop').addEventListener('click', function () {
    if (!request) return;
    request.abort(); status('Stopped waiting in this browser. The local request may already be recorded; read the thread to check.');
    anchor('failed', 'NO_DATA: browser stopped waiting; server result is unknown.');
    receipt('NO_DATA: reply not received', pageWait(requestStartedAt) + ' · NO_DATA: generation receipt not received', 'NO_DATA: browser stopped waiting; server may already have recorded the reply');
  });
  $('message-form').addEventListener('submit', async function (event) {
    event.preventDefault(); var text = $('message').value.trim();
    if (pending || !text || text.length > 600) return;
    pending = true; request = new AbortController(); var startedAt = requestStartedAt = root.performance.now(); $('send').disabled = true; $('refresh').disabled = true; $('stop').disabled = false;
    turn('soberano · explicit send', text, true); status('Waiting for Hexelion through the local app proxy.');
    anchor('thinking', 'Thinking: the local station request is in flight.');
    receipt('NO_DATA: response pending', 'NO_DATA: still running', 'NO_DATA: no reply received yet');
    try {
      var response = await root.fetch('/api/hexelion/chat', { method: 'POST', cache: 'no-store', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ texto: text }), signal: request.signal });
      var data = await response.json();
      if (!response.ok) throw new Error(data.causa || 'station_request_not_confirmed');
      var reply = paintReply(data, startedAt); if (reply) { $('message').value = ''; status('Answer received from Hexelion through the local app.'); }
    } catch (error) {
      if (error.name !== 'AbortError') {
        var cause = error && error.message ? error.message : 'NO_DATA: local answer not confirmed';
        receipt('NO_DATA: model not confirmed', pageWait(startedAt) + ' · NO_DATA: generation not returned', cause);
        anchor('failed', 'NO_DATA: ' + cause); status('NO_DATA: no Hexelion answer confirmed; read the thread before another send.');
      }
    } finally { pending = false; request = null; requestStartedAt = null; $('send').disabled = false; $('refresh').disabled = false; $('stop').disabled = true; }
  });
  $('memory-form').addEventListener('submit', async function (event) {
    event.preventDefault(); var query = $('memory-query').value.trim(); if (!query) return;
    $('memory-search').disabled = true; $('memory-status').textContent = 'Searching local memory…'; $('memory-results').replaceChildren();
    try {
      var response = await root.fetch('/api/hexelion/search', { method: 'POST', cache: 'no-store', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ consulta: query }) });
      var raw = await response.text(); if (new TextEncoder().encode(raw).length >= 1024) throw new Error('response_over_budget');
      var data = JSON.parse(raw);
      if (data.estado === 'NO_DATA' && data.causa) { $('memory-status').textContent = 'NO_DATA: ' + data.causa; return; }
      if (!response.ok || data.esquema !== 'preceptoros.memory-search/1' || !Array.isArray(data.fuentes)) throw new Error('local_sources_not_verified');
      data.fuentes.forEach(function (source) {
        if (!Number.isSafeInteger(source.id) || typeof source.updated_at !== 'string' || !/^[a-f0-9]{64}$/.test(source.sha256) || typeof source.texto !== 'string') throw new Error('citation_invalid');
        var row = doc.createElement('li'), cite = doc.createElement('p'), textNode = doc.createElement('p');
        cite.textContent = 'Memory ' + source.id + ' · ' + source.updated_at + ' · SHA-256 ' + source.sha256;
        textNode.textContent = source.texto; row.append(cite, textNode); $('memory-results').append(row);
      });
      $('memory-status').textContent = data.fuentes.length + ' cited local source(s). Search did not call the model.';
    } catch (_) { $('memory-status').textContent = 'NO_DATA: local memory results could not be verified.'; }
    finally { $('memory-search').disabled = false; }
  });
  $('read-last').addEventListener('click', async function () {
    if (!lastAnswer) return; var generation = ++readGeneration;
    try {
      if (!root.HexelionNativeVoice) await import('/native_voice.js');
      if (generation !== readGeneration) return; voice = root.HexelionNativeVoice;
      if (!voice) throw new Error('reader unavailable');
      voice.read(lastAnswer, doc.documentElement.lang, function (state) { if (generation === readGeneration) $('voice-state').textContent = state; }, 'browser');
    } catch (_) { $('voice-state').textContent = 'NO_DATA: local reader unavailable.'; }
  });
  $('stop-reading').addEventListener('click', function () { readGeneration++; if (voice) voice.stop(); $('voice-state').textContent = 'Reading stopped.'; });
  doc.addEventListener('focusin', function (event) {
    var element = event.target, rect = element.getBoundingClientRect && element.getBoundingClientRect();
    if (rect) $('position').textContent = 'Position: ' + (element.getAttribute('aria-label') || element.textContent || element.id).trim().slice(0, 48) + ' · ' + Math.round(rect.x + rect.width / 2) + ', ' + Math.round(rect.y + rect.height / 2) + ' CSS px.';
  });
  root.addEventListener('pagehide', function () { readGeneration++; if (voice) voice.stop(); });
  if ('serviceWorker' in root.navigator) root.navigator.serviceWorker.register('/sw.js').catch(function () {});
})(globalThis);
