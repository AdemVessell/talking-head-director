#!/usr/bin/env python3
"""Talking-head edit engine. One plan file per video; see references/edit-engine.md.
Run it through scripts/thd, which picks the Python that has the engine's packages.

  edit_engine.py doctor           check this machine: packages, ffmpeg, fonts, model, sounds, agent links
  edit_engine.py selftest         about a minute: the whole pipeline on a synthetic clip (run before/after changes)
  edit_engine.py transcribe RECORDING --out DIR    word transcript to write the plan from
  edit_engine.py autocut RECORDING --out DIR [--pause 0.35]   draft segments: fillers, repeats, pauses out
  edit_engine.py news RECORDING --out DIR [--look newsroom|lab] [--title T] [--headline H --source S --date D]
                 [--image SHOT.png] [--stamp UNCONFIRMED] [--flat]   autocut + a news-shaped plan in the house
                 colour journey (--flat: the rostrum camera; references/news-kit.md)
  edit_engine.py prep PLAN        extract ranges + films, face-track, force-align the kept lines
  edit_engine.py align PLAN       force-align the kept lines again (after moving in/out points)
  edit_engine.py inspect PLAN     energy and word timing around every cut, room-tone pick
  edit_engine.py edit PLAN        EDL, edit-time words, dialogue track, captions.srt
  edit_engine.py holds PLAN       frame strips of every silent hold on his face (burp check)
  edit_engine.py stills PLAN --at 0.5,3.2,7    proof frames + sheet
  edit_engine.py sound PLAN       voice chain + SFX + mix at -14 LUFS
  edit_engine.py render PLAN [--jobs 8] [--proof]
  edit_engine.py assemble PLAN    review MP4 in work/out
  edit_engine.py audit PLAN [--no-asr]   pacing/loudness audit, sync, ASR of the final audio
  edit_engine.py xcheck PLAN      X pre-posting check: calls to action, captions, title, sources, claims
  edit_engine.py all PLAN         edit -> sound -> render -> assemble -> audit -> xcheck
"""
import argparse, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["doctor", "selftest", "transcribe", "autocut", "news", "prep", "align", "inspect", "edit",
                                    "holds", "stills", "sound", "render", "assemble", "audit", "xcheck", "all"])
    ap.add_argument("target", nargs="?", help="plan file (or a recording, for transcribe and autocut)")
    ap.add_argument("--out"); ap.add_argument("--at"); ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--proof", action="store_true"); ap.add_argument("--no-asr", action="store_true")
    ap.add_argument("--frames", help="a:b frame range for render")
    ap.add_argument("--pause", type=float, default=0.35, help="autocut: pauses longer than this become cuts")
    for opt in ("--look", "--title", "--headline", "--source", "--date", "--image", "--stamp"):
        ap.add_argument(opt, help="news: see references/news-kit.md")
    ap.add_argument("--flat", action="store_true", help="news: the plain rostrum camera instead of the house colour journey")
    a = ap.parse_args()
    if a.cmd == "doctor":  # standard library only, so it can report missing packages
        from thd_engine import doctor
        sys.exit(doctor.run())
    from thd_engine import audit, autocut, captions, dialogue, news, prep, render, selftest, sound, xcheck
    from thd_engine.plan import Plan
    from thd_engine.timeline import Timeline
    t0 = time.time()
    if a.cmd == "selftest":
        sys.exit(selftest.run(a.jobs))
    if not a.target:
        ap.error(f"{a.cmd} needs " + ("a recording" if a.cmd in ("transcribe", "autocut", "news") else "a plan file"))
    if a.cmd == "transcribe":
        prep.transcribe(a.target, a.out or (Path(a.target).with_suffix("") .name + "_transcript"))
        return
    if a.cmd == "autocut":
        autocut.draft(Path(a.target).expanduser(), a.out or (Path(a.target).with_suffix("").name + "_cut"), a.pause)
        return
    if a.cmd == "news":
        news.draft(a.target, a.out or (Path(a.target).with_suffix("").name + "_news"), a.look or "newsroom", a.title,
                   a.headline, a.source, a.date, a.image, a.stamp, a.pause, a.flat)
        return
    plan = Plan.load(a.target)
    if a.cmd == "prep":
        prep.extract(plan); prep.extract_films(plan); prep.track(plan); prep.align(plan)
    elif a.cmd == "align":
        prep.align(plan)
    elif a.cmd == "inspect":
        prep.inspect(plan)
    elif a.cmd == "edit":
        dialogue.build(plan); captions.srt(plan, Timeline(plan), plan.wp("out", "captions.srt"))
    elif a.cmd == "holds":
        audit.holds(plan)
    elif a.cmd == "stills":
        render.stills(plan, a.at.split(","), a.proof)
    elif a.cmd == "sound":
        sound.build(plan, Timeline(plan))
    elif a.cmd == "render":
        render.render(plan, a.jobs, a.proof, tuple(map(int, a.frames.split(":"))) if a.frames else None)
    elif a.cmd == "assemble":
        render.assemble(plan)
    elif a.cmd == "audit":
        audit.qa(plan, plan.wp("out", plan.get("name", "edit") + ".mp4"), not a.no_asr)
    elif a.cmd == "xcheck":
        sys.exit(1 if xcheck.run(plan)["fail"] else 0)
    elif a.cmd == "all":
        dialogue.build(plan); tl = Timeline(plan); captions.srt(plan, tl, plan.wp("out", "captions.srt"))
        sound.build(plan, tl); render.render(plan, a.jobs, a.proof); out = render.assemble(plan)
        audit.holds(plan); audit.qa(plan, out, not a.no_asr); xcheck.run(plan)
    print(f"[{a.cmd}] done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
