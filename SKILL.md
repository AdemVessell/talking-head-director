---
name: talking-head-director
description: Direct, cut and finish presenter-led talking-head videos (vertical explainers, opinion and news-style posts for X, Shorts, Reels) to a professional social standard - cold-open hook, sentence-level tightening, face-anchored shot changes, word-timed captions, explanatory graphics, analog/editorial finish and sound - then audit pacing and loudness before delivery. Use when editing, re-cutting, styling, planning or reviewing a talking-head video. Not for music videos or standalone motion-graphics pieces.
metadata:
  short-description: Pro talking-head direction, cut, look and QA
  author: Claude (Anthropic), written at Adem's request, 2026-11-02
---

# Talking-Head Director

You are the editor and the director. One person talking to a webcam has to feel
like a show: tight, legible, surprising, and unmistakably theirs. Story and
rhythm come first; layout and texture serve them. The failure this skill exists
to prevent is the reverse: a well-made layout that the whole video lives inside,
with the recording's original rhythm left intact.

## Order of work

1. **Cut the story first.** From the word-level transcript find the hook,
   stakes, beats, turn and ending; reorder; remove filler; tighten gaps. No
   graphic exists until the dialogue edit (EDL) is locked for the section.
   Graphics never fix a slow cut. See [pacing-and-hook.md](references/pacing-and-hook.md).
2. **Shoot the edit.** Give every line a shot (size, window, cutaway) so the
   picture changes with the ideas. See [shot-grammar.md](references/shot-grammar.md).
3. **Make it explain.** Devices, graphics and captions keyed to exact words.
   See [graphics-and-type.md](references/graphics-and-type.md).
4. **Bind it.** Camera grade, physical materials, one finish over the frame.
   See [analog-look.md](references/analog-look.md).
5. **Make it sound finished.** Voice chain, room tone, SFX on visual events,
   -14 LUFS. See [sound.md](references/sound.md).
6. **Prove the opening, then the whole.** Render the first 15-20 s, audit it,
   watch it at phone size with sound, fix, and only then render the full piece.

**Art direction lives in [art-direction.md](references/art-direction.md)**: the
principles, the house DNA every video shares, the seven engine treatments
(evidence, studio, workshop, newsroom, lab, pinboard, classroom: a desk
surface and the papers that subject would produce; receipts only for money),
the fuller prose sets, the sequence library, editing craft, and the
director's pass. Read it before planning any new video.
Visual targets are in `assets/style-frames/` (direction, not templates: never
copy a layout verbatim; the point is the material, scale contrast and light).

Upgrading the renderer (camera state, layers, word-keyed cues, captions)? Read
[engine.md](references/engine.md).

Reference cuts Adem has judged (2026-11-03): Codex's director test
(`VIDEO EDITOR PRO/style-studies/2026-11-03/director-test`) and Claude's v2
(`~/Desktop/Arkhē Claude Lab/TALKING_HEAD_20S`). His verdict: Claude's art
direction and story editing lead, combined with Codex's wider resting frames,
shot changes and real-footage cutaways. The v2 folder is a complete working
pipeline (`edl.py` -> `timeline.py` -> `assets.py` -> `render.py` + `sound.py` ->
`assemble.sh`): reuse its patterns, never its facts, layouts or insert timings.

## Standing taste (Adem)

- Wider resting frame, face about half the frame width. Purposeful punch-ins are
  welcome; permanent extreme close-ups are not. No single composition carries
  most of the runtime.
- "More detail, more analogue, spice" means tactile and believable: paper,
  print, ink, grain, light, shadow. Not bronze machinery, generic retro props or
  distress sprayed everywhere. "Plain CGI" and clean AI-stock imagery fail.
- Smart alignment is a hard requirement. Texture never excuses sloppy geometry:
  numbers, arrows, units and labels sit on a deliberate grid and baseline.
- Still images are boring. Move them, replace him with the thing he is talking
  about, put graphics beside him. Each visual explains a relationship, not just
  a topic.
- His real performance stays central. Relighting, cutouts and transformations
  are welcome only when convincing at normal speed; glitchy separation fails.
- Natural voice speed: tighten by cutting, never by speeding up. Not mirrored.
- Original graphics only. Never fabricate screenshots, quotes, charts or
  incidents; label illustrations that could pass as evidence; keep his hedges
  ("about five minutes" stays "~5 MIN").
- One video's requirements (a specific insert, an ending smile) are not house
  rules.

## Definition of done

- `scripts/th_audit.py` passes, or every WARN is a deliberate, stated choice:
  median hold <= 2.5 s, no hold > 6 s unless marked intentional, first visual
  change <= 2 s, <= 4 pauses/min, -14 +/-1 LUFS, true peak <= -1 dBTP,
  >= 155 wpm after tightening.
- No single window/layout state covers more than ~35% of the runtime, and at
  least five distinct shot types appear.
- The first-3s strip shows the hook line being spoken, readable hook text, the
  face or the hero visual, and motion already under way.
- You watched and listened to the whole render at normal speed and phone size.
  If you could not, say so plainly. Numbers are necessary, not sufficient.
- Deliver the 1080x1920 H.264/AAC review MP4 (faststart), beat sheet, SRT,
  audit report, and a short note: what changed, what was not checked.

## One shared copy, every agent

This folder is the only copy: `~/Desktop/Arkhē Claude Lab/SKILLS/talking-head-director`,
a git repository. Claude Code, Codex and Cursor load it through links in
`~/.claude/skills`, `~/.codex/skills` and `~/.cursor/skills`. The Grok Bot app
runs in a cloud box: it installs `agents/grok-bot.md` there as a pointer and
runs the engine on the Mac with its local tools. A fix made here reaches every
agent, so:

- Run the engine through `scripts/thd`, which picks the Python that has its
  packages (`requirements.txt` pins them). `thd doctor` checks the machine:
  packages, ffmpeg, fonts, Whisper model, sound library, agent links.
  `thd selftest` runs the whole pipeline on a synthetic clip in about a
  minute.
- Before changing the engine, run `thd selftest`. Run it again after, then
  commit and push to the private backup, `AdemVessell/talking-head-director`
  (`git -C <this folder> commit -am "what changed and why"`, then
  `git -C <this folder> push`). Never edit a copy of this folder.

## Edit engine (one plan file per video)

`scripts/thd` (the launcher for `scripts/edit_engine.py`) runs the whole style from a single plan (YAML/JSON):
story segments, a treatment, documents that write, type or print themselves on
his words, one line per shot (the engine builds layouts, camera moves and
jump-cut reframes), captions, automatic sound, render and QA. Built for 1-4
minute videos: a 45 s edit renders, assembles and audits in under 4 minutes.
Read [edit-engine.md](references/edit-engine.md), then copy a worked example:
`examples/songwriting-studio/plan.yaml` (the current reference: studio
treatment, shots, a lyric page written as he says it),
`examples/rode-holder-test/plan.yaml` (product test, hand-placed layouts) or
`examples/grok-topup-v2/plan.yaml` (money receipts, 3D film wall).
News shorts for X: `thd news` drafts the plan, screenshot prints carry the real
source, and `thd xcheck` checks it before posting; read [news-kit.md](references/news-kit.md).
`autocut` -> choose the story -> treatment, documents, shots -> `prep` ->
`inspect` (fix every `!`) -> `edit` -> `holds` (look at every silent hold) ->
`stills` -> `all`.

## Scripts

Run any with `--help`. They are building blocks: the edit engine uses them, and
they also slot into another Python/PIL/FFmpeg renderer.

- `scripts/th_audit.py VIDEO [--words WORDS.json] [--out DIR]`: holds, pauses
  (relative to the file's own speech level), loudness, wpm, filler hits,
  contact sheets, first-3s strip.
- `scripts/face_track.py SOURCE --out track.json [--debug sheet.jpg]`: smoothed
  face and eye-line track. `Track.crop(t, face_frac=0.67, aspect=4/5)` returns
  a face-anchored crop for any rung of the shot ladder (eye line and x offset
  adjustable). Haar by default; pass
  `--model face_landmarker.task` for landmarks.
- `scripts/look.py`: `grade_webcam()`, `Finish(W, H, preset).apply(frame, i)`,
  `halftone()`, `xerox()`, `misregister()`, `paper()`; `still`, `video` and
  `print` CLIs.
- `scripts/caption_cards.py`: word timings to caption cards with the grouping
  rules, plus a PIL renderer with stable layout and active-word highlight.
- `scripts/voice_chain.sh IN OUT.wav [LUFS] [--mix]`: voice cleanup and two-pass
  loudness; `--mix` only normalises a finished mix.
- `scripts/style_frames.py`: renders `assets/style-frames/` and is a worked
  example of composing every building block in one frame.
