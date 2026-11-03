(function (root) {
  'use strict';
  var serial = 0, player = null, abort = null, objectURL = null;
  var encoder = new TextEncoder();
  function chunks(text) {
    var out = [], part = '', bytes = 0;
    if (typeof text !== 'string' || !text.trim() || encoder.encode(text).length > 32768) throw new Error('Text outside reading budget');
    for (var ch of text) {
      var n = encoder.encode(ch).length;
      if (bytes + n > 700) { out.push(part); part = ''; bytes = 0; }
      part += ch; bytes += n;
    }
    if (part) out.push(part);
    return out;
  }
  function stop() {
    serial++;
    if (root.speechSynthesis) root.speechSynthesis.cancel();
    if (abort) abort.abort(); abort = null;
    if (player) { player.pause(); player.removeAttribute('src'); player.load(); } player = null;
    if (objectURL) root.URL.revokeObjectURL(objectURL); objectURL = null;
  }
  async function sha(data) {
    return Array.from(new Uint8Array(await root.crypto.subtle.digest('SHA-256', data)), x => x.toString(16).padStart(2,'0')).join('');
  }
  function read(text, language, notify, engine) {
    stop(); var run = serial, parts;
    try { parts = chunks(text); } catch (_) { notify('NO_DATA · text is outside the reading budget.'); return; }
    var synth = root.speechSynthesis, selected;
    if (engine !== 'host-espeak-ng') {
      var voices = synth ? synth.getVoices().filter(v => v.localService === true && v.lang.split('-')[0] === language.split('-')[0]) : [];
      if (!voices.length || !root.SpeechSynthesisUtterance) { notify('NO_DATA · no local browser voice for this language.'); return; }
      selected = voices[0];
    }
    async function next(i) {
      if (serial !== run) return;
      if (i === parts.length) { notify('Software playback ended. Physical audibility: NO_DATA.'); return; }
      if (engine !== 'host-espeak-ng') {
        var utterance = new root.SpeechSynthesisUtterance(parts[i]);
        utterance.voice = selected; utterance.lang = selected.lang;
        utterance.onend = function () { if (serial === run) next(i + 1); };
        utterance.onerror = function () { if (serial === run) notify('NO_DATA · local browser reading failed.'); };
        notify('Reading visible text · local browser voice · part ' + (i + 1) + '/' + parts.length + '.');
        synth.speak(utterance); return;
      }
      if (language.split('-')[0] !== 'en') { notify('NO_DATA · host reader currently supports English only.'); return; }
      try {
        abort = new AbortController();
        var response = await root.fetch('/api/voz/lectura', {method:'POST',cache:'no-store',redirect:'error',signal:abort.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({text:parts[i],engine:'host-espeak-ng'})});
        if (serial !== run) return;
        if (!response.ok) throw new Error('host unavailable');
        var receipt = JSON.parse(response.headers.get('X-Voice-Receipt')), bytes = await response.arrayBuffer();
        var textHash = await sha(encoder.encode(parts[i])), audioHash = await sha(bytes);
        if (serial !== run) return;
        if (receipt.text_sha256 !== textHash || receipt.audio_sha256 !== audioHash || receipt.bytes !== bytes.byteLength) throw new Error('voice digest mismatch');
        if (objectURL) root.URL.revokeObjectURL(objectURL);
        objectURL = root.URL.createObjectURL(new Blob([bytes],{type:'audio/wav'}));
        player = new root.Audio(objectURL);
        player.onended = function () { if (serial === run) next(i + 1); };
        player.onerror = function () { if (serial === run) notify('NO_DATA · native audio playback failed.'); };
        notify('Reading visible text · app host espeak-ng · part ' + (i+1) + '/' + parts.length + ' · text SHA-256 ' + textHash + '.');
        await player.play();
      } catch (_) { if (serial === run) notify('NO_DATA · host native reading failed.'); }
    }
    next(0);
  }
  root.HexelionNativeVoice = Object.freeze({read:read,stop:stop,chunks:chunks});
  if (root.addEventListener) root.addEventListener('pagehide', stop);
})(globalThis);
