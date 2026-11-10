Set up a VizExplainer project (Remotion + Three.js) from nothing or from the starter zip.

Two sources, pick the one you actually have:
A) Starter zip attached to this bot/template (viz-explainer-starter-v1.zip): unzip it, run `node setup.mjs <new-empty-dir>`. setup.mjs checks Node>=18, npm, ffmpeg/ffprobe, verifies package.json pins against package-lock, copies into a new or empty dir only (refuses otherwise), and runs `npm ci`.
B) No zip available (a template can carry instructions but not files): bootstrap a minimal project yourself. Never invent a download URL.
   mkdir my-explainer && cd my-explainer && mkdir -p src public/fonts out
   npm init -y
   npm install --save-exact remotion@4.0.541 @remotion/cli@4.0.541 react@19.1.0 react-dom@19.1.0 three@0.185.0
   npm install --save-exact -D typescript@5.8.3 @types/react@19.1.8 @types/three@0.185.0
   tsconfig.json: {"compilerOptions":{"target":"ES2022","module":"ESNext","moduleResolution":"bundler","jsx":"react-jsx","strict":true,"skipLibCheck":true,"resolveJsonModule":true}}
   src/Root.tsx (JSX): export const Root=()=> <><Composition id="Main" component={Main} width={1080} height={1350} fps={30} durationInFrames={120}/><Composition id="Draft" component={Main} width={540} height={676} fps={30} durationInFrames={120}/></>  (even sizes: H.264 needs them)
   src/index.ts (no JSX): import {registerRoot} from 'remotion'; import {Root} from './Root'; registerRoot(Root);
   src/Main.tsx: a canvas; on mount, delayRender(); load each font with new FontFace(name, `url(${staticFile(file)})`).load(), add to document.fonts, check document.fonts.check() or cancelRender(error); create a THREE.WebGLRenderer({canvas, preserveDrawingBuffer:true}); continueRender(). On every frame call update(useCurrentFrame()/fps) which positions everything as a pure function of t and calls renderer.render.
   Fonts: only files whose license allows redistribution (e.g. SIL OFL from Google Fonts); keep the license text next to them.
   Keep package-lock.json from the first install; later installs of the same project use `npm ci`.

Checks before first render:
- `npx tsc --noEmit` passes.
- `npx remotion still src/index.ts Draft out/still.png --frame=30 --gl=swangle` works. First run downloads Remotion's own headless browser (needs network once); do not point at a system browser.
- Headless Linux without GPU: use --gl=swangle. Low memory (~2 GB): --concurrency=1.
- Remotion licensing: read node_modules/remotion/LICENSE.md and tell the user what it says (free for individuals, for-profits with up to 3 employees, non-profits; other companies need a Company License). Do not paraphrase it as MIT.
- Keep sources and renders local; never upload unless the user asks.
