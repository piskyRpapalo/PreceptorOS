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
// Bugfix 3 (2026-11-03): the Doogee read «no local browser voice» with 0 voices and no cause. Chrome hands an empty
// list until `voiceschanged`; a device may have no TTS engine at all. Each case now says WHICH NO_DATA it is.
function setupLate(initial, later, opts={}) {
  const spoken=[],timers=[];let listener=null,voices=initial;
  const synth=opts.noSynth?undefined:{getVoices:()=>voices,cancel(){},speak:u=>spoken.push(u),
    addEventListener:(t,h)=>{if(t==='voiceschanged')listener=h;},removeEventListener:()=>{listener=null;}};
  const scope={TextEncoder,AbortController,Blob,crypto:require('node:crypto').webcrypto,URL,speechSynthesis:synth,
    SpeechSynthesisUtterance:function(text){this.text=text;},addEventListener(){},
    setTimeout:(f,ms)=>{timers.push(f);return timers.length;},clearTimeout:()=>{}};
  vm.runInNewContext(fs.readFileSync('interface/native_voice.js','utf8'),scope);
  return {reader:scope.HexelionNativeVoice,spoken,arrive:()=>{voices=later;listener&&listener();},expire:()=>timers.splice(0).forEach(f=>f())};
}
test('voices that arrive late (voiceschanged) are waited for and used',()=>{
  const t=setupLate([],[{localService:true,lang:'en-US'}]);let status;
  t.reader.read('Synthetic test text','en',s=>status=s,'browser');
  assert.equal(t.spoken.length,0);t.arrive();assert.equal(t.spoken.length,1);assert.match(status,/part 1\/1/);
});
test('a device with zero voices says so, with the count and what to do',()=>{
  const t=setupLate([],[]);let status;
  t.reader.read('Synthetic test text','en',s=>status=s,'browser');t.expire();
  assert.match(status,/^NO_DATA · this device has no installed voices \(0\)/);assert.equal(t.spoken.length,0);
});
test('no speech synthesis at all is its own cause',()=>{
  const t=setupLate([],[],{noSynth:true});let status;
  t.reader.read('Synthetic test text','en',s=>status=s,'browser');
  assert.match(status,/^NO_DATA · this browser has no speech synthesis/);
});
test('only network voices: said as such, text never leaves',()=>{
  const t=setupLate([{localService:false,lang:'en-US'}],[]);let status;
  t.reader.read('Synthetic test text','en',s=>status=s,'browser');
  assert.match(status,/only network voices/);assert.equal(t.spoken.length,0);
});
test('local voices in other languages: the count is given',()=>{
  const t=setupLate([{localService:true,lang:'es-ES'},{localService:true,lang:'fr-FR'}],[]);let status;
  t.reader.read('Synthetic test text','en',s=>status=s,'browser');
  assert.match(status,/no local voice for en \(2 local voices in other languages\)/);
});
test('STOP while waiting for voices: nothing is spoken when they arrive',()=>{
  const t=setupLate([],[{localService:true,lang:'en-US'}]);
  t.reader.read('Synthetic test text','en',()=>{},'browser');t.reader.stop();t.arrive();t.expire();
  assert.equal(t.spoken.length,0);
});
