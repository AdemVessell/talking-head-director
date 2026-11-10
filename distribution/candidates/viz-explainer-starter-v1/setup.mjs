#!/usr/bin/env node
// Usage: node setup.mjs <new-project-dir> [--no-install]
// Checks node/npm/ffmpeg, copies this starter into a NEW or EMPTY directory (never overwrites), runs npm ci.
import fs from 'node:fs';import path from 'node:path';import {spawnSync} from 'node:child_process';import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));const [dest,flag]=process.argv.slice(2);
if(!dest){console.error('usage: node setup.mjs <new-project-dir> [--no-install]');process.exit(2)}
const need=(c,a,re,label)=>{const r=spawnSync(c,a,{encoding:'utf8'});if(r.status!==0){console.error(`missing: ${label}`);process.exit(1)}const m=(r.stdout+r.stderr).match(re);console.log(`ok ${label}: ${m?m[1]:'present'}`);return m?.[1]};
const nv=+process.versions.node.split('.')[0];if(nv<18){console.error('Node >= 18 required, found '+process.versions.node);process.exit(1)}console.log('ok node '+process.versions.node);
need('npm',['-v'],/(\d+\.\d+\.\d+)/,'npm');need('ffmpeg',['-version'],/ffmpeg version (\S+)/,'ffmpeg');need('ffprobe',['-version'],/ffprobe version (\S+)/,'ffprobe');
const pkg=JSON.parse(fs.readFileSync(path.join(here,'package.json')));const lock=JSON.parse(fs.readFileSync(path.join(here,'package-lock.json')));
for(const [k,v] of Object.entries({...pkg.dependencies,...pkg.devDependencies})){const l=lock.packages['node_modules/'+k]?.version;if(l!==v){console.error(`lock mismatch ${k}: package.json ${v} lock ${l}`);process.exit(1)}}
console.log('ok pins: '+Object.entries(pkg.dependencies).map(([k,v])=>k+'@'+v).join(' '));
const abs=path.resolve(dest);if(fs.existsSync(abs)&&fs.readdirSync(abs).length){console.error('refusing: '+abs+' exists and is not empty (nothing was changed)');process.exit(1)}
const skip=new Set(['node_modules','out','.git']);
const copy=(s,d)=>{fs.mkdirSync(d,{recursive:true});for(const e of fs.readdirSync(s,{withFileTypes:true})){if(skip.has(e.name)||e.isSymbolicLink())continue;const a=path.join(s,e.name),b=path.join(d,e.name);e.isDirectory()?copy(a,b):fs.copyFileSync(a,b,fs.constants.COPYFILE_EXCL)}};
copy(here,abs);console.log('created '+abs);
if(flag!=='--no-install'){const r=spawnSync('npm',['ci','--no-audit','--no-fund'],{cwd:abs,stdio:'inherit'});if(r.status!==0)process.exit(r.status)}
console.log('next: cd '+abs+' && npm run typecheck && npm run render   (first render downloads Remotion\'s own headless browser)');
