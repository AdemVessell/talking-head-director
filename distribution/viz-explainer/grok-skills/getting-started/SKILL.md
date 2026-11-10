---
name: viz-explainer-getting-started
description: Install the VizExplainer starter from its versioned archive into an empty directory and render the bundled Draft. Remotion is not MIT. The intended GitHub release is not live yet. Do not fetch it.
---

# Getting started

This skill does not contain the starter. The starter is one versioned archive.
Do not rebuild it from `docs/DRAFTSKILLSETUP.md` or from memory. Do not look
for it on the author's computer.

## The archive is not live yet

The intended file, after `AdemVessell/bot-video-engines` exists and tag `rc1`
is published, is:

https://github.com/AdemVessell/bot-video-engines/releases/download/rc1/viz-explainer-starter-v1.tar.gz

That URL is not a working download today. Do not fetch it. The bootstrap
refuses while `PUBLISHED` is `no`. Do not rebuild the starter from
`docs/DRAFTSKILLSETUP.md`.

When the release exists, the archive name is `viz-explainer-starter-v1.tar.gz`
and its SHA256 must be exactly:

22e948b5cf7cd6255a261d9356198d878ae0f04a95c353ac7854cd6d1f119fc5

A different hash means a different file. Do not install it. Owner-written
code is MIT, copyright Adem Vessell. Remotion is not MIT.

## Isolated install

```bash
sh viz-bootstrap.sh
node <unpacked>/setup.mjs ../my-explainer
cd ../my-explainer
npm run typecheck
npm run still
```

`setup.mjs` only copies into a new or empty directory, checks the lockfile
pins, and runs `npm ci`. Pins: remotion and @remotion/cli 4.0.541, react and
react-dom 19.1.0, three 0.185.0, typescript 5.8.3. The first still downloads
Remotion's own headless browser. Use `--gl=swangle` on a machine without a GPU.
Nothing in the scripts points at a system Chrome path.

A full sample is `npm run render`, then
`npm run qa -- out/Draft-master.mp4 540x676`.

## Rights, before you use it for a client

Read `LICENSES/REMOTION-LICENSE.md` in the unpacked tree. Remotion is not MIT.
The free license covers an individual, a for-profit organisation with up to
3 employees, and a non-profit, plus evaluation that is not yet commercial.
Other for-profit companies need a Company License. The file says the terms
change slightly in Remotion 5.0. Do not tell anyone that all commercial use
is free.

three.js is MIT. The bundled fonts are SIL OFL 1.1 (Bodoni Moda and IBM Plex
Mono, name "Plex" reserved). Owner-written starter code is MIT, copyright
Adem Vessell. That grant does not cover Remotion or the fonts.

## Making a film

Follow `docs/DRAFTSKILLPRODUCTION.md` inside the unpacked starter: beats in
`timeline.json`, the world in `scene.ts`, one camera in `track.ts`, offline
synth only. Do not copy someone else's images, characters, logos, or fonts.
Do not call a paid voice or music API. Do not upload. Do not post.
A still that passed on another machine is not this machine's render.
