(function () {
  'use strict';
  var form = document.getElementById('creation-publish-form');
  if (!form) return;
  var input = document.getElementById('creation-publish-file');
  var button = document.getElementById('creation-publish-send');
  var status = document.getElementById('creation-publish-status');
  input.addEventListener('change', function () {
    var file = input.files && input.files[0];
    button.disabled = !file || file.size < 1 || file.size > 25 * 1024 * 1024;
    status.textContent = file ? (button.disabled ? 'The package is empty or larger than 25 MiB.' : 'Package chosen. Not sent yet.')
      : 'No creation chosen or sent.';
  });
  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    var file = input.files && input.files[0];
    if (!file || file.size < 1 || file.size > 25 * 1024 * 1024) return;
    button.disabled = true;
    status.textContent = 'Verifying and importing the local creation…';
    try {
      var response = await fetch('/api/creaciones', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: await file.arrayBuffer(), cache: 'no-store'
      });
      var result = await response.json();
      if (!response.ok || result.estado !== 'publicado' || !/^\/creaciones\/[a-f0-9]{64}$/.test(result.url)) {
        throw new Error(result.causa || 'The package could not be verified.');
      }
      status.replaceChildren(document.createTextNode('Creation verified and available at '));
      var link = document.createElement('a');
      link.href = result.url; link.textContent = result.url;
      status.appendChild(link);
    } catch (error) {
      status.textContent = 'The creation is not available: ' + (error.message || String(error));
      button.disabled = false;
    }
  });
})();
