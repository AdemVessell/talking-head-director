"""End-to-end proof on a synthetic clip: `thd selftest` (about a minute; longer on a busy machine).

macOS `say` speaks four short lines over an ffmpeg test pattern, and the engine
runs the whole pipeline on it as on a real recording: autocut -> plan (studio
treatment, a sticky and a typed index card; face, doc, split and desk shots) ->
prep -> edit -> sound -> render -> assemble -> holds -> audit. The pattern has
no face, so the plan says `face: center`. Checks on the finished MP4: size and
frame rate, length against the EDL, an audio track, picture detail on the paper
shot, and sync. Everything stays in ~/.cache/thd_engine/selftest to look at.
Run it before and after changing the engine.
"""
import json, re, shutil, subprocess, time

import numpy as np
import yaml

from . import audit, autocut, captions, dialogue, prep, render, sound
from .plan import Plan
from .surfaces import CACHE
from .timeline import Timeline, norm

LINES = ["Here is a quick test of the edit engine.", "First, write the title on the card.",
         "Then ask a question about it.", "That is the whole idea."]


def voice(d):
    """The recording: the lines with real pauses between them, over a test pattern."""
    say = shutil.which("say")
    if not say:
        raise SystemExit("selftest needs macOS `say` for its voice")
    subprocess.run([say, "-o", str(d / "voice.aiff"), " [[slnc 650]] ".join(LINES)], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(d / "voice.aiff")], capture_output=True, text=True, check=True).stdout)
    src, n = d / "source.mp4", f"{dur + 2.5:.2f}"  # he stays on camera after the last word
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    f"testsrc2=size=1280x720:rate=30:duration={n}", "-i", str(d / "voice.aiff"),
                    "-filter_complex", "[1:a]adelay=500,apad[a]", "-map", "0:v", "-map", "[a]", "-t", n,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", str(src)], check=True)
    return src


def write_plan(d, src, segs):
    def seg(word):
        for s in segs:
            if norm(word) in {norm(w) for w in s["text"].split()}:
                return s["id"]
        raise SystemExit(f"selftest: the transcript has no {word!r}: {[s['text'] for s in segs]}")
    a, b, c = seg("write"), seg("ask"), seg("whole")
    shots = [{"at": 0, "shot": "face", "size": "P", "docs": [{"doc": "title", "slot": "br"}], "snap": True},
             {"at": f"{a}.pin", "shot": "doc", "doc": "card"}]
    if b != a:
        shots.append({"at": f"{b}.pin", "shot": "split", "doc": "card"})
    shots.append({"at": f"{c}.pin", "shot": "desk", "docs": ["card", "title"]})
    plan = {"name": "selftest", "work_dir": str(d / "work"), "source": str(src), "fps": 30, "tail": 0.9,
            "treatment": "studio", "face": "center", "segments": segs,
            "documents": {"title": {"kind": "sticky", "lines": ["h:c:SELF", "h:c:TEST"], "appear": 0},
                          "card": {"kind": "index", "lines": ["n:1:write the title", "n:2:ask a question"],
                                   "cues": {0: [f"{a}.w:write", f"{a}.we:title"], 1: [f"{b}.w:ask", f"{b}.we:question"]}}},
            "shots": shots,
            "mix": {"voice_chain": "light", "voice_lufs": -16, "lufs": -14, "fade_out": ["END-0.30", "END-0.12"]},
            "end": {"burn": ["END-0.34", "END-0.22"]}, "finish": "medium"}
    p = d / "plan.yaml"
    p.write_text(yaml.safe_dump(plan, sort_keys=False))
    return p, a


def check(plan, tl, out, report, a, secs):
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(out)],
                                     capture_output=True, text=True, check=True).stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    num, den = v["r_frame_rate"].split("/"); fps = float(num) / float(den)
    dur = float(info["format"]["duration"])
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    m = re.search(r"dialogue edit: ([+-]?[\d.]+) ms", report)
    lag = float(m.group(1)) if m else float("nan")
    t = min(tl.t(f"{a}.pin") + 1.0, tl.total - 0.5)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(out), "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    detail = float(np.frombuffer(raw, np.uint8).std())
    diffs = len(re.findall(r"^- \w+: expected", report, re.M))
    checks = [("video", (v["width"], v["height"]) == (plan.W, plan.H) and abs(fps - plan.fps) < 0.01,
               f"{v['width']}x{v['height']} @ {fps:g} fps"),
              ("length", abs(dur - tl.total) < 0.1, f"{dur:.2f} s (EDL {tl.total:.2f} s)"),
              ("audio", has_audio, "AAC track" if has_audio else "no audio stream"),
              ("picture", detail > 8, f"paper shot at {t:.1f} s, detail {detail:.0f}"),
              ("sync", abs(lag) <= 1000 / plan.fps, f"{lag:+.2f} ms")]
    ok = all(c[1] for c in checks)
    print(f"\nselftest {'PASS' if ok else 'FAIL'}  ({secs:.0f} s)")
    for name, good, detail in checks:
        print(f"  {'PASS' if good else 'FAIL'}  {name:8s} {detail}")
    print(f"  INFO  asr      " + ("no differences from the plan's text" if not diffs
                                  else f"{diffs} differences (synthetic voice; see review/QA.md)"))
    print(f"  INFO  output   {out}")
    return 0 if ok else 1


def run(jobs=8):
    t0 = time.time()
    d = CACHE / "selftest"
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    src = voice(d)
    path, a = write_plan(d, src, autocut.draft(src, d))
    plan = Plan.load(path)
    prep.extract(plan); prep.extract_films(plan); prep.track(plan); prep.align(plan)
    dialogue.build(plan); tl = Timeline(plan); captions.srt(plan, tl, plan.wp("out", "captions.srt"))
    sound.build(plan, tl); render.render(plan, jobs); out = render.assemble(plan)
    audit.holds(plan); report = audit.qa(plan, out, True)
    return check(plan, tl, out, report, a, time.time() - t0)
