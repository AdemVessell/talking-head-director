# Public distribution candidate

This directory is the original VizExplainer starter v1, unmodified, plus this
file. The original zip SHA256 is
`bb738653b994f0e3e068a87f919087ac85e4513baede94b007d52e644e581927`
(207533 bytes, 28 files). Those 28 files are byte-for-byte the same as that zip.
This file was added for the candidate. It does not change `src/`, `package.json`,
`package-lock.json`, fonts, licenses, or scripts.

Status: candidate, not a release.
Version label for the archive: the starter's own `1.0.0`, packed as
`viz-explainer-starter-v1`.
Release URL: `PLACEHOLDER_RELEASE_URL`. That string is not a working download.
No file is fetched from it.

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

The starter README says the starter code and generated assets are "yours."
No SPDX license for that code was approved for this candidate. "Yours" is not
treated as an open-source grant. The copyright holder still has to choose.

## What a bot should not do

Do not reconstruct this starter from memory or from `docs/DRAFTSKILLSETUP.md`
when the archive is missing. That draft describes a fallback. This candidate's
bootstrap does not use it. If the release URL is still the placeholder, stop.

Do not upload sources or renders. Do not post. Do not call a paid voice or
music API. Sound in this starter is the offline synth in `scripts/make-sound.mjs`.
