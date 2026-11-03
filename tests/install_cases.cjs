const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
function setup(secure=true,standalone=false){
  const handlers={},button={disabled:false,addEventListener:(n,f)=>handlers.click=f},status={};
  const root={navigator:{standalone},isSecureContext:secure,matchMedia:()=>({matches:false}),addEventListener:(n,f)=>handlers[n]=f};
  vm.runInNewContext(fs.readFileSync('interface/install.js','utf8'),root);root.HexelionInstall.mount(button,status);
  return{handlers,button,status};
}
test('no prompt is invented for insecure or unavailable contexts',()=>{
  const a=setup(false);assert(a.button.disabled);assert.match(a.status.textContent,/HTTPS/);
  a.handlers.beforeinstallprompt({preventDefault(){throw Error('insecure event accepted');}});
  assert(a.button.disabled);assert(setup().button.disabled);
});
test('accepted choice is not installation and duplicate clicks do not prompt twice',async()=>{
  const a=setup();let count=0,resolve;
  const event={preventDefault(){},prompt:()=>{count++;return Promise.resolve();},userChoice:new Promise(r=>resolve=r)};
  a.handlers.beforeinstallprompt(event);assert(!a.button.disabled);
  const first=a.handlers.click({isTrusted:true});await a.handlers.click({isTrusted:true});assert.equal(count,1);
  resolve({outcome:'accepted'});await first;assert.match(a.status.textContent,/Waiting/);
  a.handlers.appinstalled();assert.match(a.status.textContent,/reported app installed/);assert(a.button.disabled);
});
test('untrusted click never opens the browser prompt',async()=>{
  const a=setup();let count=0;
  a.handlers.beforeinstallprompt({preventDefault(){},prompt(){count++;}});
  await a.handlers.click({isTrusted:false});assert.equal(count,0);
});
test('dismissal remains uninstalled and a later native event may retry',async()=>{
  const a=setup();const event={preventDefault(){},prompt:async()=>{},userChoice:Promise.resolve({outcome:'dismissed'})};
  a.handlers.beforeinstallprompt(event);await a.handlers.click({isTrusted:true});assert.match(a.status.textContent,/dismissed/);
  a.handlers.beforeinstallprompt(event);assert(!a.button.disabled);
});
test('installed app ignores later eligibility events',()=>{
  const a=setup(true,true);a.handlers.beforeinstallprompt({preventDefault(){throw Error('installed event accepted');}});assert(a.button.disabled);
});
