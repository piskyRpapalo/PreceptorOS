(function (root) {
  'use strict';
  function mount(button, status) {
    var prompt = null, busy = false, installed = !!root.navigator.standalone || !!(root.matchMedia && root.matchMedia('(display-mode: standalone)').matches);
    function show(text, enabled) { status.textContent = text; button.disabled = !enabled; }
    if (installed) show('Running as an installed app.', false);
    else if (!root.isSecureContext) show('NO_DATA · installation requires HTTPS or trusted loopback.', false);
    else show('Install is not offered yet. Use the browser installation menu if available.', false);
    root.addEventListener('beforeinstallprompt', function (event) {
      if (installed || !root.isSecureContext || busy) return;
      event.preventDefault(); prompt = event;
      show('Ready: choose Install, then confirm in the browser.', true);
    });
    root.addEventListener('appinstalled', function () {
      installed = true; prompt = null; busy = false; show('Browser reported app installed.', false);
    });
    button.addEventListener('click', async function (event) {
      if (!event.isTrusted || !prompt || busy || installed) return;
      var current = prompt; prompt = null; busy = true;
      show('Confirm installation in the browser dialog.', false);
      try {
        await current.prompt();
        var choice = await current.userChoice;
        if (installed) return;
        show(choice.outcome === 'accepted' ? 'Browser accepted. Waiting for installation confirmation.' : 'Installation dismissed. Nothing was installed by this button.', false);
      } catch (_) { if (!installed) show('NO_DATA · browser installation could not be confirmed.', false); }
      finally { busy = false; }
    });
  }
  root.HexelionInstall = Object.freeze({mount:mount});
  if (root.document) {
    var button = root.document.getElementById('install-app'), status = root.document.getElementById('install-state');
    if (button && status) mount(button, status);
  }
})(globalThis);
