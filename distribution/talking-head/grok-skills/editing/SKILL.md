---
name: talking-head-director-editing
description: Cut and finish a presenter-led talking-head video with the versioned engine. Story first, then shots, papers on the presenter's own words, captions, sound, and a check. Never post. Never speed up or mirror the original performance.
---

# Editing

Use the engine the getting-started skill installed. Do not look for it on a
Mac, in a private repository, or in this skill's folder. If `thd doctor` has
not been run in that install, run it. If the release URL is still
`PLACEHOLDER_RELEASE_URL`, stop. That string is not a working download.

The archive SHA256 the install must have matched is:

600a299878fdbdd1385c31ae56786515bb19a922eb23ce4d7244e0deb44dcfe5

## What you are doing

One person talking to a camera. Story and rhythm first. A polished layout that
leaves the recording's original rhythm untouched is the failure to avoid.

Read `docs/WORKFLOW.md` inside the unpacked engine. Use these commands, not a
tour of the rest of the filesystem:

```bash
scripts/thd styles
scripts/thd auto RECORDING --draft
scripts/thd auto RECORDING --brief brief.yaml --style desk
scripts/thd xcheck PLAN
```

`thd styles` lists the looks that ship: desk, journey, timeline, newsdesk,
notebook, receipts, workbench, pinboard, chalkboard, clean. A style chooses
the desk, the papers, the caption look, and the pace. It does not invent facts.

## Rules that do not bend

- Tighten by cutting. Do not speed the performance up. Do not mirror it unless
  the recording itself was mirrored and the brief sets `flip` for that reason.
- Titles and on-screen points are the presenter's words. Keep hedges.
- A headline is verbatim and names its source. A screenshot is a real capture.
  Do not rebuild a post, a chart, or a quote so it looks real. Label an
  illustration that could be mistaken for evidence.
- There is no Blender diorama kit in this package. Do not invent a scene to
  fill that slot.
- Sound library files from Final Cut Pro are not included. Missing cues are
  synthesised. Do not call a paid sound service.
- Captions follow the aligned words. A brief cannot yet correct a misheard word.
- `POST.md` is a draft for a person. `thd xcheck` flags calls to action and
  missing sources. You do not post. You do not upload. You do not send the
  file anywhere unless the person asks, and even then you do not post it
  for them.

## Done

The review MP4, the SRT, and a short note: what changed, and what you did not
watch. If you did not watch the render at normal speed, at phone size, with
sound, say that. Doctor output is not a substitute for watching.
