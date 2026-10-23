(function () {
  'use strict';
  var form = document.getElementById('creation-voice-form');
  if (!form) return;
  var status = document.getElementById('creation-voice-status');
  var downloads = document.getElementById('creation-voice-downloads');
  var button = document.getElementById('creation-voice-generate');
  var input = document.getElementById('creation-voice-text');
  var urls = [], running = false;
  function clear() {
    downloads.querySelectorAll('audio').forEach(function (player) { player.pause(); player.removeAttribute('src'); player.load(); });
    urls.forEach(function (url) { URL.revokeObjectURL(url); }); urls = [];
    downloads.replaceChildren();
  }
  function link(name, contents, type, label) {
    var url = URL.createObjectURL(new Blob([contents], {type: type})); urls.push(url);
    var a = document.createElement('a'); a.href = url; a.download = name;
    a.textContent = label; a.style.display = 'inline-block';
    a.style.minHeight = '44px'; a.style.minWidth = '44px'; a.style.marginRight = '1em';
    downloads.appendChild(a); return url;
  }
  input.addEventListener('input', function () {
    clear(); status.textContent = 'Statement changed. Generate the voice downloads again.';
  });
  form.addEventListener('submit', async function (event) {
    event.preventDefault(); if (running) return;
    clear(); var text = input.value;
    if (!text.trim() || new TextEncoder().encode(text).length > 1024) {
      status.textContent = 'Use a statement of 1 to 1024 UTF-8 bytes.'; return;
    }
    running = true; button.disabled = true; input.disabled = true;
    status.textContent = 'Generating the local voice catalog and your statement. This can take several minutes.';
    try {
      var response = await fetch('/api/creaciones/voz', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: text}), cache: 'no-store'
      });
      var result = await response.json();
      if (!response.ok || result.estado !== 'ok') throw new Error(result.causa || 'Voice generation unavailable');
      var c = result.catalog, d = result.declaration;
      if (!c || !d || c.profile_id !== d.profile_id) throw new Error('Voice profile mismatch');
      link('creation-voice.json', JSON.stringify(c), 'application/json', 'Download voice catalog');
      link('creation-declaration.json', JSON.stringify(d), 'application/json', 'Download author statement');
      var bytes = Uint8Array.from(atob(d.data), function (ch) { return ch.charCodeAt(0); });
      var url = link('declaration.wav', bytes, 'audio/wav', 'Download statement WAV');
      var player = document.createElement('audio'); player.controls = true; player.src = url;
      player.setAttribute('aria-label', 'Listen to your author statement'); downloads.appendChild(player);
      status.textContent = 'Voice downloads ready. Listen to your statement, then load both JSON files in the creation page.';
    } catch (error) {
      clear(); status.textContent = error.message;
    } finally {
      running = false; button.disabled = false; input.disabled = false;
    }
  });
  window.addEventListener('pagehide', clear);
})();
