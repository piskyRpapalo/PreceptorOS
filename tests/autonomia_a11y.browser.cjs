// Autonomy parity · NEXT-A/B · isolated browser walk of Talk, Notebook and Acho, with a synthetic tool.
//
// Run (rack, never against the live service):
//   NODE_PATH=<dir with playwright-core> CHROME_PATH=/usr/bin/google-chrome node tests/autonomia_a11y.browser.cjs
//
// It starts its OWN app server from this checkout on 127.0.0.1:18740 with a throw-away HOME, a fake native MCP
// (same shape as test_hexelion_acciones FAKE) and no model endpoint, so nothing touches the person's data, the live
// service or a model. Levels are kept apart in the receipt it prints:
//   synthetic_tool   the MCP answer is a fixture, never model or rack evidence
//   real_browser     headless Chrome rendered the served assets (measured here)
//   screen_reader    NO_DATA: no assistive technology ran; aria-live text is checked, not heard
//   physical_audio   NO_DATA: no speaker was listened to
const { chromium } = require('playwright-core');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const PORT = Number(process.env.PREVIEW_PORT || 18740);
const ORIGIN = 'http://127.0.0.1:' + PORT;
const FAKE = `import json, os, sys
names = ["exec", "audit_last", "ping", "write_file", "capabilities", "state"]
for line in sys.stdin:
    m = json.loads(line)
    if m["method"] == "initialize": r = {"serverInfo": {"name": "fake"}}
    elif m["method"] == "tools/list": r = {"tools": [{"name": n} for n in names]}
    else:
        name = m["params"]["name"]
        if name == "state":
            out = {"ok": True, "uptime": "up 1 day", "memoria": ["Mem: 8G 2G"], "disco_casa": ["40% 100G"],
                   "servicios": [{"unidad": "a.service", "activo": "active"}], "modelos_cargados": []}
        else:
            out = {"ok": True, "voz": os.environ.get("PRECEPTOROS_MCP_VOZ")}
        r = {"content": [{"type": "text", "text": json.dumps(out)}]}
    print(json.dumps({"jsonrpc": "2.0", "id": m.get("id"), "result": r}), flush=True)
`;
const sha = (buf) => crypto.createHash('sha256').update(buf).digest('hex');

async function waitServer(child) {
  for (let i = 0; i < 100; i++) {
    if (child.exitCode !== null) throw new Error('preview server exited: ' + child.exitCode);
    try { const r = await fetch(ORIGIN + '/app'); if (r.ok) return; } catch { /* not yet */ }
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error('preview server did not answer');
}

(async () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'preceptoros-a11y-'));
  const fake = path.join(home, 'fake_s3.py');
  fs.writeFileSync(fake, FAKE);
  const env = { ...process.env, HOME: home, PRECEPTOROS_PWA_BIND: '127.0.0.1', PRECEPTOROS_PWA_PUERTO: String(PORT),
    PRECEPTOROS_MCP_NATIVO: fake };
  delete env.PRECEPTOROS_HEXELION_ENDPOINT;
  const server = spawn('python3', [path.join(ROOT, 'bin/preceptoros-pwa')], { cwd: ROOT, env, stdio: 'ignore' });
  const receipt = { schema: 'preceptoros.a11y-walk/1', head: null, levels: {
    synthetic_tool: 'SIMULATED', real_browser: null, screen_reader: 'NO_DATA(no_assistive_technology_ran)',
    physical_audio: 'NO_DATA(no_speaker_listened)' }, checks: {} };
  let browser;
  try {
    await waitServer(server);
    receipt.head = require('node:child_process').execSync('git rev-parse HEAD', { cwd: ROOT }).toString().trim();

    // 1 · What is served is what was tested: shell, scripts and service worker byte-identical to this checkout.
    const html = fs.readFileSync(path.join(ROOT, 'interface/app.html'), 'utf8');
    const scripts = [...html.matchAll(/<script src="(\/[a-z_]+\.js\?v=\d+)"><\/script>/g)].map((m) => m[1]);
    const served = {};
    for (const url of ['/sw.js', ...scripts]) {
      const r = await fetch(ORIGIN + url); assert.equal(r.status, 200, url);
      const local = fs.readFileSync(path.join(ROOT, 'interface', url.split('?')[0].slice(1)));
      assert.equal(sha(Buffer.from(await r.arrayBuffer())), sha(local), 'served differs from checkout: ' + url);
      served[url] = sha(local).slice(0, 12);
    }
    const sw = fs.readFileSync(path.join(ROOT, 'interface/sw.js'), 'utf8');
    for (const url of scripts.filter((u) => /app\.js|notebook\.js|acho_sonido\.js/.test(u))) assert(sw.includes('"' + url + '"'), 'sw lacks ' + url);
    receipt.checks.assets_match_checkout = Object.keys(served).length;

    browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' });
    await page.addInitScript(() => {
      window.__audioMade = 0;
      const Real = window.AudioContext;
      window.AudioContext = function () { window.__audioMade++; return new Real(); };
      window.__live = {};
      new MutationObserver((ms) => { for (const m of ms) {
        const el = m.target.nodeType === 1 ? m.target : m.target.parentElement;
        const live = el && el.closest('[aria-live]');
        if (live && live.id) (window.__live[live.id] = window.__live[live.id] || []).push(live.textContent);
      } }).observe(document, { subtree: true, childList: true, characterData: true });
    });
    const outside = []; page.on('request', (r) => { if (!r.url().startsWith(ORIGIN)) outside.push(r.url()); });
    await page.goto(ORIGIN + '/app');

    // 2 · Keyboard only: reach Talk with the tab list's arrow keys, send, and keep the place afterwards.
    await page.locator('#tab-mando').focus();
    let presses = 0;
    while (presses < 9 && await page.evaluate(() => document.activeElement.id) !== 'tab-conversacion') {
      await page.keyboard.press('ArrowRight'); presses++;
    }
    assert.equal(await page.evaluate(() => document.activeElement.id), 'tab-conversacion', 'Talk not reachable by arrows');
    assert.equal(presses, 1, 'arrows must move from the focused tab (Command -> Talk is one press)');
    receipt.checks.arrow_presses_to_talk = presses;
    assert.equal(await page.locator('#tab-conversacion').getAttribute('aria-selected'), 'true');
    await page.locator('#dicho').focus();
    await page.keyboard.type('/estado');
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'enviar');
    const liveBefore = await page.evaluate(() => (window.__live['estado'] || []).length);
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.querySelector('#estado').dataset.state === 'ACTED', null, { timeout: 15000 });
    const focusAfter = await page.evaluate(() => document.activeElement && document.activeElement.id);
    assert(['dicho', 'enviar'].includes(focusAfter), 'focus lost after the turn: ' + focusAfter);
    receipt.checks.keyboard_reaches_talk_and_focus_kept = focusAfter;

    // 3 · Parity: Talk's aria-live line is the turn the machine serves; the Notebook card says the same words.
    const machine = await page.evaluate(async () => (await (await fetch('/api/hexelion/turnos')).json()).turns[0]);
    const talk = await page.evaluate(() => ({ line: document.querySelector('#estado').textContent,
      acho: document.querySelector('#estado').dataset.acho }));
    assert.equal(talk.line, machine.sentence + ' ' + machine.next);
    assert.equal(talk.acho, machine.acho.class);
    const turnLive = await page.evaluate((n) => (window.__live['estado'] || []).slice(n), liveBefore);
    assert.deepEqual(turnLive, [talk.line], 'one turn must change Talk status exactly once, to the turn line');
    receipt.checks.talk_status_changes_per_turn = turnLive.length;
    await page.locator('#tab-cuaderno').click();
    const cardSel = '#notebook-turns [data-n="' + machine.n + '"]';
    await page.waitForSelector(cardSel, { timeout: 10000 });
    const card = await page.locator(cardSel).evaluate((c) => ({ text: c.innerText, state: c.dataset.state, acho: c.dataset.acho }));
    assert.equal(card.state, machine.state); assert.equal(card.acho, machine.acho.class);
    assert(card.text.includes(machine.sentence), 'Notebook card lacks the sentence');
    receipt.checks.talk_notebook_machine_same_sentence = machine.state;

    // 4 · Not by colour alone: the card names its state in words.
    assert(card.text.includes(machine.state), 'state word missing from the card');
    receipt.checks.state_named_in_words = true;

    // 5 · One announcement per change: refreshing the Notebook does not repeat its status lines.
    const before = await page.evaluate(() => (window.__live['notebook-turns-status'] || []).length);
    await page.locator('#notebook-refresh').click();
    await page.waitForTimeout(800);
    const after = await page.evaluate(() => (window.__live['notebook-turns-status'] || []).length);
    assert.equal(after, before, 'status line re-announced without a change');
    receipt.checks.no_repeat_on_refresh = true;
    receipt.checks.talk_status_mutations = await page.evaluate(() => (window.__live['estado'] || []).length);
    receipt.checks.talk_status_sequence = await page.evaluate(() => (window.__live['estado'] || []).map((t) => t.slice(0, 60)));

    // 6 · Sound stays off by default; reduced motion keeps the panel sting silent.
    const sound = await page.evaluate(async () => [await window.PreceptorAchoSonido.play({ class: 'ok',
      motif: { portadora: 220, moduladora: 440, indice: 20, dur: 0.28, vibrato: false } }), window.__audioMade,
      await window.PreceptorSting.tocar()]);
    assert.equal(sound[0].state, 'off'); assert.equal(sound[1], 0); assert.equal(sound[2].estado, 'inactivo');
    receipt.checks.sound_off_and_reduced_motion = true;

    // The arrow walk passes through World, whose panel loads the public OpenWorld page by design; anything else fails.
    const declared = ['https://preceptoros.org/openworld/'];
    assert.deepEqual(outside.filter((u) => !declared.includes(u)), [], 'request left the preview origin');
    receipt.checks.outside_requests_declared = outside.length;
    receipt.levels.real_browser = 'MEASURED(headless_chrome)';
    receipt.result = 'PASS';
  } catch (e) {
    receipt.result = 'FAIL'; receipt.error = String(e && e.message || e).slice(0, 300);
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    server.kill('SIGTERM');
    fs.rmSync(home, { recursive: true, force: true });
    console.log(JSON.stringify(receipt));
  }
})();
