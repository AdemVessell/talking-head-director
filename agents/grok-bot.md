---
name: talking-head-director
description: Direct, cut and finish Adem's presenter-led talking-head videos (vertical explainers for X, Shorts, Reels) in his house style - story-first cut, paper documents that write themselves on his words, word-timed captions, designed sound, then a QA audit. The skill and its edit engine live on Adem's Mac; read them and run them there with your local tools. Use when editing, re-cutting, styling, planning or reviewing a talking-head video.
---

# Talking-Head Director (pointer for the Grok Bot box)

The real skill is on Adem's Mac, not in this box:

    /Users/stevenson/Desktop/Arkhē Claude Lab/SKILLS/talking-head-director/

It is one shared git repository; Codex and Claude Code load the same folder.
The footage, ffmpeg, fonts, Whisper model and sound library are all on the
Mac, so the work happens there.

1. With your local tools, read `SKILL.md` in that folder, then the references
   it names (`references/edit-engine.md` for the engine).
2. Run the engine on the Mac through its launcher, `scripts/thd` in that
   folder: `thd doctor` first, then `thd autocut VIDEO --out DIR`, write the
   plan, `thd prep`, `thd inspect`, `thd edit`, `thd holds`, `thd stills`,
   `thd all DIR/plan.yaml`. A 45 s video takes about 4 minutes; let each
   command finish.
3. Deliver from the Mac's work folder (`work/out/*.mp4`, `work/review/QA.md`).
   Never re-cut a video that is already posted.
4. If you change the engine, run `thd selftest` before and after, then commit
   in that folder with a message saying what changed and why.

If the Mac is unreachable, say so. Do not rebuild the engine in this box.
