import { generateKeyPairSync, sign } from 'node:crypto';
import { writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const P = createRequire(import.meta.url)('../../../public/game/creation_package.js');
const pair = generateKeyPairSync('ed25519');
const wav = Buffer.alloc(48); wav.write('RIFF'); wav.writeUInt32LE(40, 4); wav.write('WAVEfmt ', 8);
wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20); wav.writeUInt16LE(1, 22);
wav.writeUInt32LE(8000, 24); wav.writeUInt32LE(16000, 28); wav.writeUInt16LE(2, 32); wav.writeUInt16LE(16, 34);
wav.write('data', 36); wav.writeUInt32LE(4, 40); wav.writeInt16LE(1000, 44); wav.writeInt16LE(-1000, 46);
const frame = {v:'preceptoros.bubble/1',id:'CREATION',cv:[412,515],style:'clear',
  atoms:[{k:'keepsake',i:[{o:'ribbon',f:'cyan',s:'ink',d:0,lw:2.5,pts:[[206,258],[210,258],[210,262]]}]}]};
const prepared = await P.prepare({author:'Fixture author',description:'A test ribbon.',voice_profile:'a'.repeat(64),frame,audio:wav});
// A leading newline proves that receivers verify original bytes, not reconstructed JSON.
prepared.manifest = '\n' + prepared.manifest;
const pkg = await P.finish(prepared,pair.publicKey.export({format:'der',type:'spki'}).subarray(-32).toString('hex'),
  sign(null,Buffer.from(prepared.manifest),pair.privateKey).toString('hex'));
const save = (n, p) => writeFileSync(new URL(n, import.meta.url), JSON.stringify(p) + '\n');
save('valid.json',pkg);
for (const name of ['frame','audio','manifest','signature']) {
  const p = structuredClone(pkg);
  if(name==='frame' || name==='audio') {
    const key=name==='frame'?'frame.json':'declaration.wav', b=Buffer.from(p.files[key],'base64');
    b[b.length-1]^=1; p.files[key]=b.toString('base64');
  } else if(name==='manifest') p.manifest=p.manifest.replace('Fixture author','Fixture other');
  else p.signature=(p.signature[0]==='0'?'1':'0')+p.signature.slice(1);
  save('altered-'+name+'.json',p);
}
save('limits.json',{frame_bytes:1024,package_bytes:26214401,receipt_bytes:1024,method:'runtime-padding'});
