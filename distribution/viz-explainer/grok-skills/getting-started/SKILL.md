---
name: viz-explainer-getting-started
description: Install the VizExplainer starter from its versioned archive into an empty directory and render the bundled Draft. Remotion is not MIT. PLACEHOLDER_RELEASE_URL is not a working download.
---

# Getting started

This skill does not contain the starter. The starter is one versioned archive.
Do not rebuild it from `docs/DRAFTSKILLSETUP.md` or from memory. Do not look
for it on the author's computer.

## The archive is not published yet

`PLACEHOLDER_RELEASE_URL` is not a working download. Do not invent a URL.
If `RELEASE_URL` still contains `PLACEHOLDER`, stop and say the starter has
not been published. The bootstrap script exits without fetching.

When that placeholder is replaced, the archive must be
`viz-explainer-starter-v1.tar.gz` and its SHA256 must be exactly:

5081b30a04413853f4ebf7893dd71d6b0b394e730b6c9ae9206d9a3b383819ce

A different hash means a different file. Do not install it.

The original 28-file zip this candidate was packed from is
`bb738653b994f0e3e068a87f919087ac85e4513baede94b007d52e644e581927`.
The candidate archive is that starter plus `CANDIDATE.md`, so its hash is the
line above, not the original zip hash.

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
Mono, name "Plex" reserved). The starter's own code has no approved SPDX
license. The line in its README that says the code is "yours" is not a
license grant you can rely on. Say that, and stop if the person needs a grant
the copyright holder has not written.

## Making a film

Follow `docs/DRAFTSKILLPRODUCTION.md` inside the unpacked starter: beats in
`timeline.json`, the world in `scene.ts`, one camera in `track.ts`, offline
synth only. Do not copy someone else's images, characters, logos, or fonts.
Do not call a paid voice or music API. Do not upload. Do not post.
A still that passed on another machine is not this machine's render.
