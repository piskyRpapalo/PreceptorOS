// Directed browser checks. API interception below is synthetic, never model evidence.
const { chromium } = require('playwright-core');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({executablePath: process.env.CHROME_PATH, headless:true, args:['--no-sandbox']});
  const page = await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  const origin = process.env.PREVIEW_ORIGIN || 'http://127.0.0.1:18740';
  let posts = 0, release;
  await page.route('**/api/lab', async route => {
    if (route.request().method() === 'GET') return route.fulfill({json:{conversacion:{mensajes:[]}}});
    posts++;
    await new Promise(resolve => {release=resolve;});
    await route.fulfill({json:{respuesta:{voz:'synthetic-test-fixture',texto:'<img src=x onerror="alert(1)"> fixture only',canal:'orquesta',n:7}}});
  });
  const requests=[]; page.on('request',r=>requests.push(r.url()));
  await page.goto(origin+'/hexelion.html');
  assert.equal(await page.title(),'Hexelion · Session');
  await page.screenshot({path:process.env.DESKTOP_SHOT || '/tmp/hexelion-desktop.png',fullPage:true});
  assert(!requests.some(u=>!u.startsWith(origin)),'unexpected cross-origin request');
  await page.locator('#message').fill('Synthetic browser test; not a mission.');
  await page.locator('#send').click();
  await page.waitForFunction(()=>document.querySelector('#send').disabled);
  await page.locator('#message-form').evaluate(f=>f.dispatchEvent(new Event('submit',{cancelable:true})));
  assert.equal(posts,1,'duplicate request'); release();
  await page.waitForFunction(()=>document.querySelector('#connection').textContent.includes('Answer received'));
  assert.equal(await page.locator('#thread img').count(),0,'HTML was interpreted');
  assert.match(await page.locator('#receipt').innerText(),/synthetic-test-fixture.*sequence: 7/);
  await page.locator('#read-last').click();
  await page.waitForFunction(()=>document.querySelector('#voice-state').textContent.includes('NO_DATA'));
  await page.setViewportSize({width:390,height:844});
  await page.goto(origin+'/hexelion.html');
  const targets = await page.locator('button,a').evaluateAll(es=>es.filter(e=>e.getClientRects().length&&!e.closest('[hidden]')).map(e=>({text:e.textContent.trim(),w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height})));
  assert(targets.every(t=>t.w>=44&&t.h>=44),JSON.stringify(targets));
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'mobile horizontal overflow');
  await page.locator('#refresh').focus();
  assert.match(await page.locator('#position').innerText(),/x \d+, y \d+ CSS px/);
  await page.screenshot({path:process.env.MOBILE_SHOT || '/tmp/hexelion-mobile.png',fullPage:true});
  for(const skin of ['basic','atlantis','zombie']) {
    await page.goto(origin+'/face/'+skin+'.html');
    assert.equal(await page.locator('a[href="/hexelion.html"]').count(),1);
  }
  console.log(JSON.stringify({kind:'synthetic_browser_checks',checks:['routes','no_external_startup','duplicate_send','dom_injection','attribution','missing_voice','44px','mobile_overflow','focus_coordinate','three_skin_links'],passed:10,physical_phone:'NO_DATA'}));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
