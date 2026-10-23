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
    status.textContent = file ? (button.disabled ? 'El paquete está vacío o supera 25 MiB.' : 'Paquete elegido. No se ha enviado.')
      : 'No se ha seleccionado ni enviado ninguna creación.';
  });
  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    var file = input.files && input.files[0];
    if (!file || file.size < 1 || file.size > 25 * 1024 * 1024) return;
    button.disabled = true;
    status.textContent = 'Verificando e importando la creación local…';
    try {
      var response = await fetch('/api/creaciones', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: await file.arrayBuffer(), cache: 'no-store'
      });
      var result = await response.json();
      if (!response.ok || result.estado !== 'publicado' || !/^\/creaciones\/[a-f0-9]{64}$/.test(result.url)) {
        throw new Error(result.causa || 'El paquete no se pudo verificar.');
      }
      status.replaceChildren(document.createTextNode('Creación verificada y disponible en '));
      var link = document.createElement('a');
      link.href = result.url; link.textContent = result.url;
      status.appendChild(link);
    } catch (error) {
      status.textContent = 'La creación no está disponible: ' + (error.message || String(error));
      button.disabled = false;
    }
  });
})();
