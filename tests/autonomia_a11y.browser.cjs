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
    physical_audio: 'NO_DATA(no_speaker_listened)', virtual_keyboard: null }, checks: {} };
  let browser;
  try {
    await waitServer(server);
    receipt.head = require('node:child_process').execSync('git rev-parse HEAD', { cwd: ROOT }).toString().trim();

    // 1 · What is served is what was tested: shell, scripts and service worker byte-identical to this checkout.
    const html = fs.readFileSync(path.join(ROOT, 'interface/app.html'), 'utf8');
    const scripts = [...html.matchAll(/<script src="(\/[a-z_]+\.js\?v=\d+)"><\/script>/g)].map((m) => m[1]);
    const styles = [...html.matchAll(/<link rel="stylesheet" href="(\/[a-z_]+\.css\?v=\d+)">/g)].map((m) => m[1]);
    const served = {};
    for (const url of ['/sw.js', ...scripts, ...styles]) {
      const r = await fetch(ORIGIN + url); assert.equal(r.status, 200, url);
      const local = fs.readFileSync(path.join(ROOT, 'interface', url.split('?')[0].slice(1)));
      assert.equal(sha(Buffer.from(await r.arrayBuffer())), sha(local), 'served differs from checkout: ' + url);
      served[url] = sha(local).slice(0, 12);
    }
    const sw = fs.readFileSync(path.join(ROOT, 'interface/sw.js'), 'utf8');
    for (const url of [...styles, ...scripts.filter((u) => /app\.js|notebook\.js|acho_sonido\.js/.test(u))]) assert(sw.includes('"' + url + '"'), 'sw lacks ' + url);
    receipt.checks.assets_match_checkout = Object.keys(served).length;

    browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' });
    await page.addInitScript(() => {
      window.__audioMade = 0;
      const Real = window.AudioContext;
      window.AudioContext = function () { window.__audioMade++; return new Real(); };
      window.__live = {};
      // What a screen reader would be handed: words added to a visible, effective live region (aria-live="off" on
      // a nearer element silences it). Text replaced by the same text is not new words.
      window.__said = [];
      const effective = (el) => { const r = el && el.closest('[aria-live]'); return r && r.getAttribute('aria-live') !== 'off' ? r : null; };
      new MutationObserver((ms) => { for (const m of ms) {
        const el = m.target.nodeType === 1 ? m.target : m.target.parentElement;
        const nodes = m.type === 'characterData' ? [m.target] : [...m.addedNodes];
        for (const n of nodes) {
          const host = n.nodeType === 1 ? n : n.parentElement || el;
          const region = effective(host);
          if (!region || region.closest('[hidden]') || getComputedStyle(region).display === 'none') continue;
          const words = (n.textContent || '').trim();
          if (words) window.__said.push([region.id || region.className, words]);
        } } }).observe(document, { subtree: true, childList: true, characterData: true });
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

    // 7 · Nine panels by keyboard: Home, End and arrows reach every tab in order; only its panel is shown; wraps both ways.
    await page.locator('#tab-mando').click();
    await page.locator('#tab-mando').focus();
    const tabs = await page.$$eval('.pestanas [role=tab]', (ts) => ts.map((t) => [t.id, t.getAttribute('aria-controls')]));
    assert.equal(tabs.length, 9, 'nine panels');
    const at = () => page.evaluate(() => { const a = document.activeElement;
      const shown = [...document.querySelectorAll('[role=tabpanel]')].filter((p) => !p.hidden && p.offsetParent !== null).map((p) => p.id);
      return [a.id, a.getAttribute('aria-selected'), a.tabIndex, shown]; });
    const walk = [];
    for (let i = 1; i <= tabs.length; i++) {
      await page.keyboard.press('ArrowRight');
      const [id, sel, tabindex, shown] = await at(); const want = tabs[i % tabs.length];
      assert.deepEqual([id, sel, tabindex, shown], [want[0], 'true', 0, [want[1]]], 'ArrowRight step ' + i);
      walk.push(id);
    }
    await page.keyboard.press('ArrowLeft');
    assert.equal((await at())[0], tabs[tabs.length - 1][0], 'ArrowLeft wraps to the last tab');
    await page.keyboard.press('Home'); assert.equal((await at())[0], tabs[0][0]);
    await page.keyboard.press('End'); assert.equal((await at())[0], tabs[tabs.length - 1][0]);
    const others = await page.$$eval('.pestanas [role=tab]', (ts) => ts.filter((t) => t.getAttribute('aria-selected') !== 'true').map((t) => t.tabIndex));
    assert(others.every((x) => x === -1), 'unselected tabs leave the Tab order (roving tabindex)');
    const unnamed = await page.$$eval('[role=tabpanel]', (ps) => ps.filter((p) => !(p.getAttribute('aria-label') || p.getAttribute('aria-labelledby'))).map((p) => p.id));
    assert.deepEqual(unnamed, [], 'every panel has a name');
    receipt.checks.nine_panels_keyboard = walk.length;

    // 8 · Contrast, light and dark: visible text against its painted background (WCAG 2.x formula, 4.5:1 normal text).
    const contrast = async () => page.evaluate(() => {
      const rgb = (c) => { const m = c.match(/[\d.]+/g); return m ? m.map(Number) : null; };
      const lum = ([r, g, b]) => [r, g, b].map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; })
        .reduce((a, v, i) => a + v * [0.2126, 0.7152, 0.0722][i], 0);
      const bg = (el) => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor);
        if (c && (c.length < 4 || c[3] > 0.95)) return c.slice(0, 3); if (getComputedStyle(e).backgroundImage !== 'none') return null; }
        return [255, 255, 255]; };
      const out = [];
      for (const el of document.querySelectorAll('[role=tab], #estado, #talk-tasks, #conv-destinos, .notebook-status, .notebook-fact, button, label, h2, h3, h4, p')) {
        if (!el.offsetParent || !el.textContent.trim() || el.closest('[hidden]')) continue;
        const own = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
        if (!own) continue;
        const b = bg(el); const f = rgb(getComputedStyle(el).color);
        if (!b || !f) continue;
        const [L1, L2] = [lum(f.slice(0, 3)), lum(b)].sort((a, c) => c - a);
        out.push([el.id || el.className || el.tagName, +((L1 + 0.05) / (L2 + 0.05)).toFixed(2), el.textContent.trim().slice(0, 30)]);
      }
      return out;
    });
    // The app declares `color-scheme: light` only, so a dark pass would measure the same page: NO_DATA, not a second pass.
    const rows = [];
    for (const tab of ['#tab-conversacion', '#tab-cuaderno', '#tab-ajustes']) {
      await page.locator(tab).click(); await page.waitForTimeout(300); rows.push(...await contrast());
    }
    const low = rows.filter((r) => r[1] < 4.5);
    receipt.checks.contrast_light = { elements: rows.length, min: Math.min(...rows.map((r) => r[1])), below_4_5: low.slice(0, 8) };
    receipt.checks.contrast_dark = 'NO_DATA(app_declares_light_only)';
    assert.deepEqual(low, [], 'text below 4.5:1');

    // 9 · Sound by keyboard: Settings switch turns turn sounds on, says so, and off again; off means silent.
    await page.locator('#tab-ajustes').click();
    await page.locator('#ajustes-voz > summary').focus();
    await page.keyboard.press('Enter');
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'acho-sonido', 'Tab from the group opens onto the switch');
    const soundNow = async () => page.evaluate(async () => [document.querySelector('#acho-sonido').checked,
      document.querySelector('#acho-sonido-estado').textContent, (await window.PreceptorAchoSonido.play({ class: 'ok',
        motif: { portadora: 220, moduladora: 440, indice: 20, dur: 0.05, vibrato: false } })).state]);
    await page.keyboard.press('Space'); const on = await soundNow();
    await page.keyboard.press('Space'); const off = await soundNow();
    assert.equal(on[0], true); assert(/are on/.test(on[1]), on[1]); assert(['played', 'NO_DATA'].includes(on[2]), on[2]);
    assert.deepEqual([off[0], /are off/.test(off[1]), off[2]], [false, true, 'off']);
    receipt.checks.sound_switch_by_keyboard = { on: on[2], off: off[2] };

    // 10 · Phone size 420 x 680: Talk fits without sideways scroll; the box and Send stay on screen and big enough.
    const phone = await browser.newPage({ viewport: { width: 420, height: 680 }, reducedMotion: 'reduce', hasTouch: true, isMobile: true });
    await phone.goto(ORIGIN + '/app');
    await phone.locator('#tab-conversacion').click();
    await phone.locator('#dicho').focus();
    const fit = await phone.evaluate(() => { const r = (s) => document.querySelector(s).getBoundingClientRect();
      const d = r('#dicho'), e = r('#enviar');
      return { scroll: document.documentElement.scrollWidth, width: innerWidth, dicho: [d.top, d.bottom, d.height],
        enviar: [e.top, e.bottom, e.width, e.height], viewport: document.querySelector('meta[name=viewport]').content }; });
    assert(fit.scroll <= fit.width, 'sideways scroll at 420 px: ' + fit.scroll);
    assert(fit.dicho[0] >= 0 && fit.dicho[1] <= 680 && fit.enviar[1] <= 680, 'box or Send off screen');
    assert(fit.enviar[2] >= 24 && fit.enviar[3] >= 24, 'Send smaller than 24 px');
    assert(/interactive-widget=resizes-content/.test(fit.viewport));
    receipt.checks.phone_420x680 = { scroll_width: fit.scroll, send_px: fit.enviar.slice(2).map(Math.round), box_bottom: Math.round(fit.dicho[1]) };
    receipt.levels.virtual_keyboard = 'NO_DATA(headless_has_no_on_screen_keyboard)';
    await phone.close();

    // 11 · An uncertain task, in a real DOM. The server's route stays NO_DATA(p2_mirror_not_built); the browser is handed
    // the projection test_uncertainty_presentation builds (python3 tareas_hexelion on its fixture). Synthetic data.
    const fixture = JSON.parse(require('node:child_process').execFileSync('python3', ['-c',
      'import json,test_uncertainty_presentation as U; print(json.dumps(U.told(U.event(U.projection()))))'], { cwd: ROOT }));
    const real = await page.evaluate(async () => (await (await fetch('/api/hexelion/tareas')).json()).cause);
    assert.equal(real, 'p2_mirror_not_built', 'the live route must stay unconnected');
    await page.route('**/api/hexelion/tareas', (r) => r.fulfill({ contentType: 'application/json', body: JSON.stringify(fixture) }));
    await page.locator('#tab-conversacion').click();
    await page.waitForFunction(() => !document.querySelector('#talk-tasks').hidden, null, { timeout: 10000 });
    await page.locator('#tab-cuaderno').click();
    await page.waitForSelector('#notebook-tasks [data-state="OUTCOME_UNKNOWN"]', { timeout: 10000 });
    const u = await page.evaluate(() => ({ talk: document.querySelector('#talk-tasks').textContent,
      talkLive: document.querySelector('#talk-tasks').getAttribute('aria-live'),
      status: document.querySelector('#notebook-tasks-status').textContent,
      card: document.querySelector('#notebook-tasks [data-state="OUTCOME_UNKNOWN"]').innerText,
      acho: document.querySelector('#notebook-tasks [data-state="OUTCOME_UNKNOWN"]').dataset.acho,
      buttons: [...document.querySelectorAll('#notebook-tasks button, #talk-tasks button')].length }));
    const t = fixture.tasks[0];
    assert.equal(u.talk, u.status, 'Talk and Notebook say the same line');
    assert(u.talk.includes(t.sentence + ' ' + t.next));
    // Compact card first; the full references sit in a closed disclosure that the keyboard can open.
    assert(!u.card.includes(t.uncertainty.projection_ref), 'full refs belong to the disclosure, not the first view');
    await page.locator('#notebook-tasks [data-state="OUTCOME_UNKNOWN"] details > summary').focus();
    await page.keyboard.press('Enter');
    const opened = await page.locator('#notebook-tasks [data-state="OUTCOME_UNKNOWN"]').innerText();
    for (const ref of [t.uncertainty.task_ref, t.uncertainty.projection_ref]) assert(opened.includes(ref), 'ref missing after opening');
    assert.deepEqual([u.talkLive, u.acho, u.buttons], ['polite', 'uncertain', 0]);
    assert(!/\b(signed|refunded|released|returned|approved)\b/i.test(u.talk + opened), 'claims something unseen');
    receipt.checks.uncertain_task_same_in_talk_and_notebook = 'SIMULATED_DATA_REAL_DOM';
    const border = await page.$eval('#notebook-tasks [data-state="OUTCOME_UNKNOWN"]', (c) => getComputedStyle(c).borderInlineStartStyle);
    assert.equal(border, 'dashed', 'uncertainty is drawn as a dashed line, not by colour alone');
    await page.unroute('**/api/hexelion/tareas');

    // 12 · One announcement per event. A Talk turn hands each message's words to a reader once: the person's draft,
    // the reply, the turn line; the thread's copies of drafts arrive quietly; unchanged lines stay silent.
    await page.locator('#tab-conversacion').click(); await page.waitForTimeout(500);
    await page.evaluate(() => { window.__said = []; });
    await page.locator('#dicho').fill('/estado'); await page.locator('#enviar').click();
    await page.waitForFunction(() => document.querySelector('#estado').dataset.state === 'ACTED', null, { timeout: 15000 });
    await page.waitForTimeout(2500);
    const said = await page.evaluate(() => window.__said);
    // A repeat is an announcement that carries words already announced in this turn (a copy wrapped in metadata counts).
    const core = (w) => w.replace(/^Hexelion · [a-z ]+?: /, '').replace(/^Hexelion: /, '');
    const repeats = said.filter((x, j) => said.slice(0, j).some((y) => core(y[1]).length >= 4 && x[1].includes(core(y[1]))));
    const replyWords = (await page.evaluate(async () => (await (await fetch('/api/hexelion/turnos')).json()).turns[0].sentence));
    assert(said.some((x) => x[0] === 'estado' && x[1].startsWith(replyWords)), 'the turn line was not announced');
    assert.deepEqual(repeats, [], 'the same words were announced twice in one turn');
    assert(!said.some((x) => x[0] === 'conv-destinos'), 'unchanged destinations re-announced');
    receipt.checks.turn_announcements = said.map((x) => x[0]);

    // 14 · Acho expression: the mark beside the status says what just happened; it never moves without evidence.
    assert.equal(await page.$eval('#acho-estado', (m) => m.dataset.expression), 'verified', 'an ACTED turn is drawn as verified');
    assert.equal(await page.evaluate(() => document.getAnimations().filter((a) => a.playState === 'running').length), 0,
      'reduced motion: nothing moves');
    const lively = await browser.newPage({ viewport: { width: 1280, height: 900 }, reducedMotion: 'no-preference' });
    await lively.goto(ORIGIN + '/app');
    const moves = await lively.evaluate(() => { const m = document.getElementById('acho-estado'), A = window.AchoMotion;
      const count = () => m.getAnimations().length, out = {};
      for (const [cls, state] of [[null, 'waiting'], ['uncertain', 'OUTCOME_UNKNOWN'], ['ok', 'ACTED'], ['ok', 'ACTED']]) {
        const before = count(); const name = A.express(m, cls, state); out[name + (out[name] !== undefined ? '_again' : '')] = count() - before; }
      return out; });
    await lively.close();
    assert.deepEqual(moves, { waiting: 0, uncertain: 0, verified: 1, verified_again: 0 }, 'moves once, only for a confirmed result');
    receipt.checks.acho_expression = moves;

    // 15 · Panel flow: opening a panel speaks once. Its sections keep painting their own lines (visible, readable),
    // but only the panel's own line is spoken when the reading settles. A refresh keeps focus on its button.
    const openSaid = {};
    for (const tab of ['#tab-mando', '#tab-gobierno', '#tab-cuaderno', '#tab-lab', '#tab-harness', '#tab-puerta', '#tab-modelos', '#tab-ajustes', '#tab-conversacion']) {
      await page.evaluate(() => { window.__said = []; });
      await page.locator(tab).click(); await page.waitForTimeout(1500);
      openSaid[tab.slice(5)] = await page.evaluate(() => window.__said.map((x) => x[0]));
    }
    receipt.checks.panel_open_announcements = openSaid;
    const focusAfterRefresh = {};
    for (const [tab, panel] of [['#tab-cuaderno', 'cuaderno'], ['#tab-lab', 'lab'], ['#tab-harness', 'harness'], ['#tab-ajustes', 'ajustes']]) {
      await page.locator(tab).click(); await page.waitForTimeout(800);
      const button = page.locator(`#panel-${panel} button[data-refrescar]`).first();
      if (!(await button.count())) { focusAfterRefresh[panel] = 'NO_DATA(no_refresh_button)'; continue; }
      await button.focus(); await page.keyboard.press('Enter'); await page.waitForTimeout(1500);
      focusAfterRefresh[panel] = await page.evaluate(() => { const a = document.activeElement; return a && a.dataset && a.dataset.refrescar ? 'kept' : (a ? a.tagName + '#' + a.id : 'none'); });
    }
    receipt.checks.focus_after_refresh = focusAfterRefresh;
    for (const [panel, said] of Object.entries(openSaid)) assert(said.length <= 1, `opening ${panel} spoke ${said.length} lines: ${said}`);
    for (const [panel, where] of Object.entries(focusAfterRefresh)) assert(where === 'kept' || where.startsWith('NO_DATA'), `refresh in ${panel} lost focus to ${where}`);

    // 13 · English only, first paint included: no Spanish words visible in any of the nine panels.
    // `canal:<thread>` is lab.py's source identifier (data, pinned by test_lab), not prose; it is not matched.
    const spanish = /\b(Bucles|Consultando|aún|comprobando|Zona activa|Hablar|mensajes|Publicar|creación|Identidad|edificio|Redacción|Modelos locales|Canales recientes|Elige|ninguna)\b/;
    const leaks = [];
    for (const tab of ['#tab-mando', '#tab-conversacion', '#tab-gobierno', '#tab-cuaderno', '#tab-lab', '#tab-harness', '#tab-puerta', '#tab-modelos', '#tab-ajustes']) {
      await page.locator(tab).click(); await page.waitForTimeout(700);
      const text = await page.evaluate(() => document.querySelector('[role=tabpanel]:not([hidden])').innerText + ' ' + document.querySelector('#estado').textContent);
      for (const line of text.split('\n')) if (spanish.test(line)) leaks.push(tab + ': ' + line.trim().slice(0, 60));
    }
    assert.deepEqual(leaks, [], 'Spanish prose visible in the English app');
    receipt.checks.spanish_visible = 0;

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
