const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
function setup(voices) {
  const spoken=[];
  const scope={TextEncoder,AbortController,Blob,crypto:require('node:crypto').webcrypto,URL,
    speechSynthesis:{getVoices:()=>voices,cancel(){},speak:u=>spoken.push(u)},
    SpeechSynthesisUtterance:function(text){this.text=text;},addEventListener(){}};
  vm.runInNewContext(fs.readFileSync('interface/native_voice.js','utf8'),scope);
  return {scope,spoken,reader:scope.HexelionNativeVoice};
}
test('remote-only voices never cause speech or an implicit default',()=>{
  const {reader,spoken}=setup([{localService:false,lang:'en-US'}]);let status;
  reader.read('Synthetic test text','en',s=>status=s,'browser');
  assert.match(status,/NO_DATA/);assert.equal(spoken.length,0);
});
test('chunks preserve every Unicode character and obey the byte budget',()=>{
  const {reader}=setup([]);const text='Synthetic 🌊 text. '.repeat(400);
  const parts=reader.chunks(text);assert.equal(parts.join(''),text);
  assert(parts.every(p=>Buffer.byteLength(p)<=700));
});
test('STOP invalidates late native callbacks and remaining chunks',()=>{
  const {reader,spoken}=setup([{localService:true,lang:'en-US'}]);
  reader.read('Synthetic '.repeat(200),'en',()=>{},'browser');
  assert.equal(spoken.length,1);reader.stop();spoken[0].onend();assert.equal(spoken.length,1);
});
test('STOP ignores a late host response without creating audio',async()=>{
  const {reader,scope}=setup([]);let finish,created=0;
  scope.fetch=()=>new Promise(r=>finish=r);scope.Audio=function(){created++;};
  reader.read('Synthetic test text','en',()=>{},'host-espeak-ng');
  reader.stop();finish({ok:true});await new Promise(r=>setImmediate(r));assert.equal(created,0);
});
