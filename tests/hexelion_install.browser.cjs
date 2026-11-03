// Real browser metadata/cache checks; never confirm a native OS install here.
const {chromium}=require('playwright-core');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os'),path=require('node:path');
(async()=>{
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'hexelion-install-browser-'));
  const browser=await chromium.launchPersistentContext(profile,{executablePath:process.env.CHROME_PATH,headless:true,args:['--no-sandbox'],viewport:{width:390,height:844}});
  const page=await browser.newPage();
  await page.addInitScript(()=>{window.nativeInstallEventSeen=false;addEventListener('beforeinstallprompt',()=>window.nativeInstallEventSeen=true);});
  const origin=process.env.PREVIEW_ORIGIN||'http://127.0.0.1:18742';
  await page.goto(origin+'/hexelion.html');
  await page.evaluate(()=>navigator.serviceWorker.ready);
  await page.waitForFunction(()=>navigator.serviceWorker.controller);
  const cdp=await page.context().newCDPSession(page);
  const manifest=await cdp.send('Page.getAppManifest');
  assert.equal(manifest.errors.length,0,JSON.stringify(manifest.errors));
  const parsed=JSON.parse(manifest.data);assert.equal(parsed.id,'/');assert.equal(parsed.start_url,'/hexelion.html');
  const cache=await page.evaluate(async()=>({keys:await caches.keys(),install:!!await caches.match('/install.js'),shell:!!await caches.match('/hexelion.html'),api:!!await caches.match('/api/lab')}));
  assert(cache.install&&cache.shell&&!cache.api,JSON.stringify(cache));
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'horizontal mobile overflow');
  const bounds=await page.locator('#install-app').boundingBox();assert(bounds.width>=44&&bounds.height>=44);
  const diagnostics=await cdp.send('Page.getInstallabilityErrors');
  const result={kind:'real_browser_install_metadata',secureContext:await page.evaluate(()=>isSecureContext),manifestErrors:manifest.errors,installabilityErrors:diagnostics.installabilityErrors,nativePromptEvent:await page.evaluate(()=>nativeInstallEventSeen),cache,physicalPhoneInstall:'NO_DATA',osInstallation:'NOT_EXECUTED'};
  fs.writeFileSync('/tmp/hexelion-install-browser-receipt.json',JSON.stringify(result,null,2));
  await page.screenshot({path:'/tmp/hexelion-install-mobile.png',fullPage:true});
  console.log(JSON.stringify(result));await browser.close();fs.rmSync(profile,{recursive:true,force:true});
})().catch(e=>{console.error(e);process.exit(1);});
