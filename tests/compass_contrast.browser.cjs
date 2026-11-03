// Directed browser check of the Command dial (measured 2026-11-03 on the Beelink and the Doogee: black labels on black
// sectors, unreadable). The dial's sheet went to legacy/ and nothing active styled the SVG, so every sector and every
// label fell back to the default fill: black. J1 demands every label read on every sector it can sit on.
// Law held here: no sector paints the default black; every label and symbol carries a halo (stroke painted under the
// fill) whose contrast with its fill is at least 4.5:1, so it reads on gold, green, violet or slate alike.
const { chromium } = require('playwright-core');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({executablePath: process.env.CHROME_PATH, headless:true, args:['--no-sandbox']});
  const page = await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const origin = process.env.PREVIEW_ORIGIN || 'http://127.0.0.1:18740';
  await page.goto(origin+'/app.html');
  await page.waitForFunction(()=>document.querySelectorAll('#compass-svg-hueco .etiqueta').length>0,null,{timeout:15000});
  const d = await page.evaluate(()=>{
    const rgb = s => (s.match(/[\d.]+/g)||[]).slice(0,3).map(Number);
    const lum = c => { const v=c.map(x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4;}); return .2126*v[0]+.7152*v[1]+.0722*v[2]; };
    const ratio = (a,b) => { const A=lum(rgb(a)),B=lum(rgb(b)); return (Math.max(A,B)+.05)/(Math.min(A,B)+.05); };
    const hueco = document.getElementById('compass-svg-hueco');
    const sectores = [...hueco.querySelectorAll('.sector')].map(e=>getComputedStyle(e).fill);
    const textos = [...hueco.querySelectorAll('.etiqueta,.simbolo')].map(e=>{ const s=getComputedStyle(e);
      return {t:e.textContent, fill:s.fill, stroke:s.stroke, sw:parseFloat(s.strokeWidth)||0, order:s.paintOrder,
        ratio: s.stroke && s.stroke!=='none' ? ratio(s.fill,s.stroke) : 0}; });
    return {sectores, textos};
  });
  assert(d.sectores.length>0,'no sectors drawn');
  assert(d.sectores.every(f=>f!=='rgb(0, 0, 0)'),'a sector paints the default black: '+JSON.stringify(d.sectores.slice(0,4)));
  const malos = d.textos.filter(t=>!(t.ratio>=4.5 && t.sw>=1 && /^stroke/.test(t.order)));
  assert.equal(malos.length,0,'labels without a readable halo: '+JSON.stringify(malos.slice(0,3)));
  await page.locator('#compass-container').screenshot({path:process.env.DIAL_SHOT || '/tmp/compass-dial.png'});
  console.log(JSON.stringify({piece:'compass-contrast', receipt:'VERDE', sectors:d.sectores.length, labels:d.textos.length, min_ratio:Math.min(...d.textos.map(t=>t.ratio)).toFixed(1)}));
  await browser.close();
})().catch(e=>{ console.log(JSON.stringify({piece:'compass-contrast', receipt:'ROJO', error:String(e.message||e).slice(0,300)})); process.exit(1); });
