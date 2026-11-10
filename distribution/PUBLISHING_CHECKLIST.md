# Publishing checklist

Do these by hand, after the decisions in `OWNER_DECISIONS.md`. This repository
stays private until you change that yourself. These candidates do not.

## Before any public URL exists

- [ ] Read `NOTICES.md` in the talking-head candidate and `CANDIDATE.md` plus
      `LICENSES/REMOTION-LICENSE.md` in the Viz candidate.
- [ ] Choose the owner-code license, or keep the source unlicensed and do not
      publish it.
- [ ] Listen to a Linux selftest render. The synthesised sound kit has not
      been approved by ear.
- [ ] Replace `PLACEHOLDER_RELEASE_URL` in both bootstrap `RELEASE_URL` files.
      Until you do, both bootstraps exit and do not download.
- [ ] Re-run `distribution/pack-candidates.sh` if the trees changed, and
      replace the SHA256 recorded in the skill files and `ENGINE.sha256`.
      A changed archive is a different file. The old hash must not stay.
- [ ] Confirm each archive has no `.git`, no `__pycache__`, no
      `PRIVATE_DO_NOT_SHIP`, no `/Users/` path, and no real-presenter stills.
      The pack script greps for those and refuses to write the archive if it
      finds them.

## Creating the public place

- [ ] Create the public repository or repositories yourself, under the names
      you chose. Do not push this private repository's history to them.
- [ ] Put the candidate archive in a release, or push a fresh tree that
      contains only the candidate files. Do not push this private repo's
      `.git` history.
- [ ] Record the real URL and the SHA256 where recipients can see both.
- [ ] Only then put that URL into the Grok skill files that the parent bot
      installs (`distribution/talking-head/grok-skills/` and
      `distribution/viz-explainer/grok-skills/`).
- [ ] Install those skills into the bot templates yourself. The skills do not
      contain the engine or the starter filesystem. They tell the bot to
      fetch one versioned archive and check the hash.

## After a URL exists

- [ ] On a machine that is not the author's, run the bootstrap, then
      `scripts/thd doctor` and `scripts/thd selftest` for talking-head, and
      `node setup.mjs` plus `npm run still` for Viz.
- [ ] Do not describe a unit test or this agent's run as that recipient's
      install.
- [ ] The tools do not post. A person posts, after `thd xcheck` or Viz QA,
      and only if they meant to.

## Explicitly not part of this checklist

- Changing this repository's visibility.
- Creating the public repository from this agent.
- Uploading the archives to a public host.
- Sending the skills to a live bot, Slack, X, or email.
