// Offline synthesized bed: soft pad + one tick per beat from src/timeline.json. Deterministic, no network.
import fs from 'node:fs';
const TL=JSON.parse(fs.readFileSync(new URL('../src/timeline.json',import.meta.url)));
const SR=48000,N=Math.round(TL.duration*SR),L=new Float32Array(N);let s=12345;const rnd=()=>((s=(s*1664525+1013904223)>>>0)/4294967296)*2-1;
for(let i=0;i<N;i++){const t=i/SR,env=Math.min(1,t/.6,(TL.duration-t)/.6);L[i]=env*.08*(Math.sin(2*Math.PI*110*t)+.6*Math.sin(2*Math.PI*164.8*t)+.4*Math.sin(2*Math.PI*220.5*t))}
for(const b of TL.beats){const i0=Math.round(b.t[0]*SR);for(let j=0;j<SR*.25&&i0+j<N;j++){const e=Math.exp(-j/SR*30);L[i0+j]+=e*(.25*Math.sin(2*Math.PI*880*j/SR)+.05*rnd())}}
const out='out/sound.wav';fs.mkdirSync('out',{recursive:true});const b=Buffer.alloc(44+N*2);
b.write('RIFF',0);b.writeUInt32LE(36+N*2,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(1,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*2,28);b.writeUInt16LE(2,32);b.writeUInt16LE(16,34);b.write('data',36);b.writeUInt32LE(N*2,40);
for(let i=0;i<N;i++)b.writeInt16LE(Math.round(Math.max(-1,Math.min(1,L[i]))*32000),44+i*2);fs.writeFileSync(out,b);console.log('wrote',out);
