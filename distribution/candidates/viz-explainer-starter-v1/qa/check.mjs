// QA: strict decode, fps/dimensions/pix_fmt, loudness + true peak measured on the final file.
// Usage: node qa/check.mjs out/Draft-master.mp4 [WxH]
import {spawnSync} from 'node:child_process';
const run=(c,a)=>{const r=spawnSync(c,a,{encoding:'utf8',maxBuffer:64e6});return r};
const [f,dim]=process.argv.slice(2);if(!f){console.error('usage: node qa/check.mjs <file> [WxH]');process.exit(2)}
const p=JSON.parse(run('ffprobe',['-v','error','-show_streams','-show_format','-of','json',f]).stdout);
const v=p.streams.find(s=>s.codec_type==='video'),a=p.streams.find(s=>s.codec_type==='audio');const [n,d]=v.r_frame_rate.split('/').map(Number);const fps=n/d;
const dec=run('ffmpeg',['-v','error','-xerror','-err_detect','explode','-i',f,'-f','null','-']);
const lo=run('ffmpeg',['-nostats','-i',f,'-af','ebur128=peak=true','-f','null','-']).stderr;const sum=lo.slice(lo.lastIndexOf('Summary:'));
const I=+sum.match(/I:\s+(-?[\d.]+) LUFS/)[1],TP=+sum.match(/Peak:\s+(-?[\d.]+) dBFS/)[1];
const res={file:f,codec:v.codec_name,profile:v.profile,w:v.width,h:v.height,fps,frames:+v.nb_frames,dur:+p.format.duration,pix:v.pix_fmt,audio:a?.codec_name,LUFS:I,TP,decode:(dec.status===0&&!dec.stderr.trim())?'clean':'errors'};
console.log(JSON.stringify(res));const fail=[];
if(fps!==30)fail.push('fps');if(dim&&`${v.width}x${v.height}`!==dim)fail.push('dims');if(v.pix_fmt!=='yuv420p')fail.push('pix_fmt');if(!a)fail.push('no audio');
if(res.decode!=='clean')fail.push('decode');if(!(I>=-15&&I<=-13))fail.push('LUFS');if(TP>-1)fail.push('true peak');
if(fail.length){console.error('QA FAIL: '+fail.join(', '));process.exit(1)}console.log('QA PASS');
