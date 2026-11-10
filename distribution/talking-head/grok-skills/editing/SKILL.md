---
name: talking-head-director-editing
description: Cut and finish a presenter-led talking-head video with the versioned engine. Story first, then shots, papers on the presenter's own words, captions, sound, and a check. Never post. Never speed up or mirror the original performance.
---

# Editing

Use the engine the getting-started skill installed. Do not look for it on a
Mac, in a private repository, or in this skill's folder. If `thd doctor` has
not been run in that install, run it. The intended release
https://github.com/AdemVessell/bot-video-engines/releases/download/rc1/talking-head-director-0.1.0-rc1.tar.gz
is not live. Do not fetch it until that repository and tag exist.

The archive SHA256 the install must have matched is:

bd7d7149daecdc3a5b7dd974cc2dd4d16f2771bd8f9b7f59bd1a570d420abafa

## What you are doing

One person talking to a camera. Story and rhythm first. A polished layout that
leaves the recording's original rhythm untouched is the failure to avoid.

Read `docs/WORKFLOW.md` inside the unpacked engine. Use these commands, not a
tour of the rest of the filesystem:

`thd auto` drafts a cut from a transcript. A source-aligned edit is a different
path: `docs/SOURCE_ALIGNED.md` and `examples/source-aligned/`. The story is a
segment list, captions are the aligned words, and full render waits until the
preview of that list is approved. The example is synthetic.

```bash
bash scripts/thd styles
bash scripts/thd auto RECORDING --draft
bash scripts/thd auto RECORDING --brief brief.yaml --style desk
bash scripts/thd xcheck PLAN
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
