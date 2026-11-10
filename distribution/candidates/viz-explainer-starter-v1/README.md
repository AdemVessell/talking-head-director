# VizExplainer starter v1
Turns complex ideas into clear, story-driven animated explainers: a small Remotion + Three.js starter with one
continuous 3D camera, multi-beat timeline, bundled open fonts, offline synthesized sound, and render/QA scripts.

Inspired by Nima Owji's Animator template: https://x.ai/bot/Hp85sZKzJNjabj8hakjee . Enhanced with a reference-led visual-explainer production workflow. No affiliation or endorsement claimed.

## What's inside
- `src/timeline.json` beats + on-screen text (seconds) · `src/tokens.ts` palette/type/safe zones · `src/track.ts` time-keyed Hermite camera
- `src/scene.ts` neutral demo world (stage, three primitives, a field of thin layers) — replace per film
- `src/Main.tsx` frame clock + font gate · `src/index.ts` compositions `Main` (1080x1350) and `Draft` (540x676; H.264 needs even sizes)
- `scripts/make-sound.mjs` offline synth bed · `scripts/render.sh` render + master + compatible copy + audio fit
- `qa/check.mjs` strict decode / fps / size / loudness · `qa/font-test.sh` proves a missing font fails the render
- `examples/rolling-shutter/` optional tiny model (not used by the starter) · `LICENSES/`, `ASSETS.md`

## Setup
Needs Node >= 18, npm, ffmpeg + ffprobe on PATH.
```
node setup.mjs ../my-explainer     # checks versions/pins, copies into a NEW or EMPTY dir (never overwrites), runs npm ci
cd ../my-explainer
npm run typecheck
npm run still                      # out/still.png, frame 45 of Draft
npm run render                     # Draft: out/Draft-master.mp4 ; bash scripts/render.sh Main for 1080x1350 (+720 compat)
npm run qa -- out/Draft-master.mp4 540x676
bash qa/font-test.sh
```
Pinned: remotion/@remotion/cli 4.0.541, react/react-dom 19.1.0, three 0.185.0, typescript 5.8.3 (exact, via package-lock).

## First run & distribution
- First render: Remotion downloads its own headless browser (network once); run `npm run still` first as a startup check.
- This zip is the real kit. A public bot template carries instructions only and cannot carry these files; nothing imports the zip automatically. Get the zip as an attachment (or a local path on the same machine), unzip it, then run `node setup.mjs <new-dir>`.

## Runtime notes
- **Browser:** on first render Remotion downloads its own headless Chrome into node_modules. Nothing assumes a system browser path. That download needs network once.
- **GL backend:** scripts use `--gl=swangle` (software WebGL); it works on headless Linux without a GPU. With a GPU you may try `--gl=angle`.
- **Memory:** software rendering is RAM-heavy. Scripts use `--concurrency=1`; raise it only with spare memory. If Chrome is killed (OOM), lower size (Draft), concurrency, or shadow map size.
- **Determinism:** every visual is a pure function of frame/fps; capture waits for fonts and the scene (`delayRender`), and a font that fails to load cancels the render instead of falling back.
- **Encodes:** master H.264 High 4.0, CRF 17, yuv420p, AAC 48 kHz, faststart. A Constrained Baseline 3.1 compatible copy is always made, scaled down to 720 wide when the master is wider.
- **Audio target:** measured on the final encode: -14 LUFS ±1, true peak ≤ -1 dBTP (render.sh loops gain until met).
- **Local only:** sources, renders and audio stay on the machine you run them on; nothing is uploaded.
- Tested on one Linux machine (Node 24, ffmpeg 7.1). Other OSes/machines are untested; no claim it works everywhere.

## Licensing — read before commercial use
- **Remotion is not MIT.** Per `LICENSES/REMOTION-LICENSE.md`, the free license covers individuals, for-profit organizations with up to 3 employees, and non-profit/not-for-profit organizations; other for-profit companies must obtain a Company License. That file also notes the license will change slightly in Remotion 5.0. Read the file itself; this summary is not legal advice.
- three.js: MIT. Fonts: SIL OFL 1.1 (texts in `LICENSES/`). Starter code and generated assets: yours.

## Make your own explainer
1. Write the idea as 3–6 beats (one claim each) in `timeline.json`; set on-screen text (hold ≥ `readHold`).
2. Build the world in `scene.ts`: real objects that *do* the explanation; keep `update(t)` pure.
3. Key the camera in `track.ts` keys (fewer keys = calmer); mark the last `hold:true`.
4. `npm run still` at each beat, then `bash scripts/render.sh Draft`, review, then `Main`.
