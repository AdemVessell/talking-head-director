# Distribution candidates

This directory is review material inside the private development repository.
It is not a public release. Nothing here changes the visibility of this
repository, creates another repository, or uploads a release.

Two candidates:

- `candidates/talking-head-director-0.1.0-rc1/` is the talking-head engine,
  built from the uploaded public port (archive 01), not from the older files
  at the repository root. The root `scripts/` tree is still the private
  development copy at the base commit. Do not treat the two as the same tree.
- `candidates/viz-explainer-starter-v1/` is the original VizExplainer starter,
  file-for-file, plus `CANDIDATE.md`. The starter was not rewritten.

Archives, checksums, and the Grok skill prose live next to those trees after
`distribution/pack-candidates.sh` has been run. `PLACEHOLDER_RELEASE_URL` is
written into the bootstrap files. It is not a working download.

Private audit inputs (PRIVATE_DO_NOT_SHIP, the private skill wrappers, the
real-presenter contact sheet) are not copied into either candidate.

Owner decisions that still block a real publication are in `OWNER_DECISIONS.md`.
The steps that stay manual are in `PUBLISHING_CHECKLIST.md`.
