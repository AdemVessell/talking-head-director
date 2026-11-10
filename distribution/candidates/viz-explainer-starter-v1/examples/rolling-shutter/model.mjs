// Minimal rolling- vs global-shutter model (original math). Background: Basler, "Electronic Shutter Types"
// and "Sensor Readout Time" (docs.baslerweb.com). Row y starts exposing at y*rowOffset and lasts `exposure`;
// a pixel's value = fraction of its exposure window during which a moving vertical bar covers it.
// Output: PGM images rolling.pgm and global.pgm. Run: node model.mjs
import fs from 'node:fs';
const W=160,H=120,exposure=0.002,rowOffset=0.0001,speed=4000, barW=12; // px/s
const x0=t=>20+speed*t; // bar left edge over time
function img(off){const a=new Uint8Array(W*H);for(let y=0;y<H;y++){const t0=y*off;for(let x=0;x<W;x++){let c=0;const S=40;for(let k=0;k<S;k++){const t=t0+exposure*(k+.5)/S,l=x0(t);if(x>=l&&x<l+barW)c++}a[y*W+x]=255-Math.round(255*c/S)}}return a}
for(const [n,off] of [['rolling',rowOffset],['global',0]]){fs.writeFileSync(n+'.pgm',Buffer.concat([Buffer.from(`P5 ${W} ${H} 255\n`),img(off)]));console.log('wrote',n+'.pgm')}
