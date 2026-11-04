// Synthetic API responses: no model or physical-device claim.
const { chromium } = require('playwright-core');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({executablePath: process.env.CHROME_PATH, headless: true, args: ['--no-sandbox']});
  const page = await browser.newPage();
  const origin = process.env.PREVIEW_ORIGIN || 'http://127.0.0.1:18740';
  await page.route('**/api/lab', route => route.fulfill({json: {respuesta: {voz: '  ', texto: 'synthetic', canal: 'fixture', n: 1}}}));
  await page.goto(origin + '/hexelion.html');
  await page.locator('#message').fill('synthetic request');
  await page.locator('#send').click();
  await page.waitForFunction(() => document.querySelector('#connection').textContent.includes('NO_DATA'));
  assert.equal(await page.locator('#read-last').isEnabled(), false);
  assert.equal(await page.locator('#thread [data-role="model"]').count(), 0);
  console.log('PASS: blank speaker is not attributed or read aloud');
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
