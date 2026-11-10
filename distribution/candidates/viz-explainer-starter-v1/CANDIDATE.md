# Public distribution candidate

This directory is the original VizExplainer starter v1, unmodified, plus this
file. The original zip SHA256 is
`bb738653b994f0e3e068a87f919087ac85e4513baede94b007d52e644e581927`
(207533 bytes, 28 files). Those 28 files are byte-for-byte the same as that zip.
This file was added for the candidate. It does not change `src/`, `package.json`,
`package-lock.json`, fonts, licenses, or scripts.

Status: candidate, not a release. The public repository is not live.
Version label for the archive: the starter's own `1.0.0`, packed as
`viz-explainer-starter-v1`.
Intended URL, after `AdemVessell/bot-video-engines` exists:
`https://github.com/AdemVessell/bot-video-engines/releases/download/rc1/viz-explainer-starter-v1.tar.gz`
That URL is not a working download until the repository and the `rc1` release exist.
Owner-written code is MIT, copyright Adem Vessell (`LICENSE`). Remotion and the fonts are not relicensed.

## Install on a new machine

Needs Node >= 18, npm, ffmpeg, and ffprobe. No path on the author's computer
is required.

```bash
node setup.mjs ../my-explainer
cd ../my-explainer
npm run typecheck
npm run still
```

`setup.mjs` copies into a new or empty directory and runs `npm ci` from the
lockfile. Pins: remotion and @remotion/cli 4.0.541, react and react-dom 19.1.0,
three 0.185.0, typescript 5.8.3. The first still downloads Remotion's headless
browser once. Renders use `--gl=swangle` (software WebGL). Nothing points at a
system Chrome.

A full Draft render is `npm run render`, then
`npm run qa -- out/Draft-master.mp4 540x676`.

## Rights

Read `LICENSES/REMOTION-LICENSE.md` before any commercial use. Remotion is not
MIT. The free license covers an individual, a for-profit organisation with up
to 3 employees, and a non-profit, plus evaluation that is not yet commercial.
Other for-profit companies need a Company License. The same file says the
license will change slightly in Remotion 5.0. This summary is not a substitute
for that file, and it is not a statement that all commercial use is free.

three.js is MIT (`LICENSES/THREE-LICENSE.txt`). Do not describe the whole
starter as MIT.

Fonts `public/fonts/BodoniModa.ttf` and `public/fonts/IBMPlexMono.ttf` are
bundled with SIL OFL 1.1 texts in `LICENSES/` and again beside the files.
IBM Plex reserves the font name "Plex". The files are unmodified. See `ASSETS.md`.

Owner-written code is MIT, copyright Adem Vessell. Remotion stays under
`LICENSES/REMOTION-LICENSE.md`. The fonts stay SIL OFL 1.1.

The paper cards stand on the stage in a receding row (`src/stageLayout.ts`).
The camera keys are the original ones. `node --experimental-strip-types qa/camera-clearance.mjs`
fails if the camera or its near plane comes within 0.5 of a card, if a card
pierces the stage, or if the travel no longer shows the field. The near plane
is 0.02.

## What a bot should not do

Do not reconstruct this starter from memory or from `docs/DRAFTSKILLSETUP.md`
when the archive is missing. That draft describes a fallback. This candidate's
bootstrap does not use it. The intended URL is not live. Do not fetch it.

Do not upload sources or renders. Do not post. Do not call a paid voice or
music API. Sound in this starter is the offline synth in `scripts/make-sound.mjs`.
