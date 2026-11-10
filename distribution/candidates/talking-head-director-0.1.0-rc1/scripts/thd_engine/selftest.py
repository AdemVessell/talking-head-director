"""End-to-end proof on a synthetic clip: `thd selftest` (about a minute; longer on a busy machine).

A synthetic voice (macOS `say`, or espeak-ng on Linux) speaks four short lines over an ffmpeg test pattern, and the engine
runs the whole pipeline on it as on a real recording: autocut -> plan (studio
treatment, a sticky and a typed index card; face, doc, split and desk shots) ->
prep -> edit -> sound -> render -> assemble -> holds -> audit. The pattern has
no face, so the plan says `face: center`. The desk at the end carries a clearly
labelled synthetic screenshot (a print with its source, a marker box and an
UNCONFIRMED stamp). Checks on the finished MP4: size and frame rate, length
against the EDL, an audio track, picture detail on the paper shot, and sync.
Then the news kit: `news.draft` turns the same recording into a news plan (it
shares the prepared footage), four stills are rendered from it, and the X
pre-posting check runs on both plans, and the critic pass builds its evidence and draws one frame
twice with fresh renderers (they must match). Everything stays in
~/.cache/thd_engine/selftest to look at. Run it before and after changing the engine.
"""
import json, os, re, shutil, subprocess, time

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

from . import audit, autocut, captions, critic, dialogue, news, prep, render, sound, xcheck
from .plan import Plan
from .surfaces import CACHE
from .timeline import Timeline, norm

LINES = ["Here is a quick test of the edit engine.", "First, write the title on the card.",
         "Then ask a question about it.", "That is the whole idea."]


def voice(d):
    """The recording: the lines with real pauses between them, over a test pattern."""
    say, esp = shutil.which("say"), shutil.which("espeak-ng") or shutil.which("espeak")
    if say:
        subprocess.run([say, "-o", str(d / "voice.aiff"), " [[slnc 650]] ".join(LINES)], check=True)
    elif esp:  # Linux: one file per line, joined with the same 0.65 s pauses
        ins, flt = [], []
        for k, line in enumerate(LINES):
            subprocess.run([esp, "-s", "150", "-w", str(d / f"line{k}.wav"), line], check=True)
            ins += ["-i", str(d / f"line{k}.wav")]; flt.append(f"[{k}:a]aresample=48000,apad=pad_dur=0.65[a{k}]")
        flt.append("".join(f"[a{k}]" for k in range(len(LINES))) + f"concat=n={len(LINES)}:v=0:a=1[a]")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ins, "-filter_complex", ";".join(flt),
                        "-map", "[a]", str(d / "voice.aiff")], check=True)
    else:
        raise SystemExit("selftest needs a voice: macOS `say`, or `espeak-ng` on Linux (apt install espeak-ng)")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(d / "voice.aiff")], capture_output=True, text=True, check=True).stdout)
    src, n = d / "source.mp4", f"{dur + 2.5:.2f}"  # he stays on camera after the last word
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    f"testsrc2=size=1280x720:rate=30:duration={n}", "-i", str(d / "voice.aiff"),
                    "-filter_complex", "[1:a]adelay=500,apad[a]", "-map", "0:v", "-map", "[a]", "-t", n,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", str(src)], check=True)
    return src


def test_page(path):
    """A clearly labelled synthetic web page: the stand-in for a real screenshot (never a real outlet)."""
    from . import fonts as _fonts; W, H = 1400, 820
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 96], fill=(30, 30, 34))
    d.text((40, 26), "SELFTEST  -  SYNTHETIC PAGE, NOT A REAL PUBLICATION", font=_fonts.load("sans_bold", 40),
           fill=(255, 255, 255))
    big = _fonts.load("georgia_bold", 78)
    d.text((40, 150), "Engine check: the news kit pins", font=big, fill=(20, 20, 20))
    d.text((40, 250), "a screenshot with its source", font=big, fill=(20, 20, 20))
    for k in range(5):
        d.rectangle([40, 400 + k * 70, 1240 - 140 * (k % 3), 430 + k * 70], fill=(205, 205, 210))
    im.save(path)
    return path


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
    shots.append({"at": f"{c}.pin", "shot": "desk", "docs": ["card", "title", "evidence"]})
    plan = {"name": "selftest", "work_dir": str(d / "work"), "source": str(src), "fps": 30, "tail": 0.9,
            "treatment": "studio", "face": "center", "segments": segs,
            "documents": {"title": {"kind": "sticky", "lines": ["h:c:SELF", "h:c:TEST"], "appear": 0},
                          "card": {"kind": "index", "lines": ["n:1:write the title", "n:2:ask a question"],
                                   "cues": {0: [f"{a}.w:write", f"{a}.we:title"], 1: [f"{b}.w:ask", f"{b}.we:question"]}},
                          "evidence": {"kind": "screenshot", "image": str(test_page(d / "test_page.png")),
                                       "crop": [0, 0, 1, 0.62], "source": "Selftest · synthetic page",
                                       "marker": {"box": [0.02, 0.22, 0.85, 0.62], "at": f"{c}.w:That", "dur": 0.4},
                                       "stamps": [{"at": f"{c}.w:whole", "text": "UNCONFIRMED"}]}},
            "shots": shots,
            "mix": {"voice_chain": "light", "voice_lufs": -16, "lufs": -14, "fade_out": ["END-0.30", "END-0.12"]},
            "end": {"burn": ["END-0.34", "END-0.22"]}, "finish": "medium"}
    p = d / "plan.yaml"
    p.write_text(yaml.safe_dump(plan, sort_keys=False))
    return p, a


def news_kit(d, src, plan):
    """The same recording through `thd news`: a news plan on the shared prepared footage, four stills
    (thumbnail, evidence print, take, split) and the X check. Returns check rows and the result."""
    nd = d / "news"; (nd / "work").mkdir(parents=True)
    for f in ("transcript.json", "audio48.wav"):  # the cached transcript: no second transcription
        shutil.copy(d / f, nd / f)
    os.symlink(plan.wp("prep"), nd / "work" / "prep")  # same recording, same cut: share the prepared footage
    path = news.draft(src, nd, "newsroom", "SELF TEST", "write the title on the card", "Selftest", "synthetic page",
                      d / "test_page.png", "UNCONFIRMED")
    nplan = Plan.load(path); R = render.Renderer(nplan)
    times = [0.0] + [min(R.tl.total - 0.1, R.tl.t(s["at"]) + 0.7) for s in nplan["shots"][1:4]]
    ims = [R.frame(int(round(t * nplan.fps))) for t in times]
    th = [np.asarray(Image.fromarray(np.asarray(x, np.uint8)).resize((360, 640), Image.LANCZOS)) for x in ims]
    Image.fromarray(np.hstack(th)).save(nplan.wp("review", "news_sheet.jpg"), quality=90)
    detail = [float(np.asarray(Image.fromarray(np.asarray(x, np.uint8)).convert("L"), np.float32).std()) for x in ims]
    shots = " / ".join(s["shot"] + (f" {s['size']}" if "size" in s else "") for s in nplan["shots"][:4])
    xn = xcheck.run(nplan, R)
    ev = nplan["documents"].get("evidence", {})
    rows = [("news", ev.get("kind") == "screenshot" and min(detail) > 8,
             f"{len(nplan['shots'])} shots ({shots} ...), stills detail {min(detail):.0f}+")]
    return rows, xn, nplan.wp("review", "news_sheet.jpg")


def check(plan, tl, out, report, a, secs, extra=()):
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
              ("sync", abs(lag) <= 1000 / plan.fps, f"{lag:+.2f} ms")] + list(extra)
    ok = all(c[1] for c in checks)
    print(f"\nselftest {'PASS' if ok else 'FAIL'}  ({secs:.0f} s)")
    for name, good, detail in checks:
        print(f"  {'PASS' if good else 'FAIL'}  {name:8s} {detail}")
    print(f"  INFO  asr      " + ("no differences from the plan's text" if not diffs
                                  else f"{diffs} differences (synthetic voice; see review/QA.md)"))
    print(f"  INFO  output   {out}")
    return 0 if ok else 1


def run(jobs=3):
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
    xm = xcheck.run(plan)
    rows, xn, sheet = news_kit(d, src, plan)
    rows.append(("xcheck", not xm["fail"] and not xn["fail"],
                 f"main {xm['fail']} fail / {xm['warn']} warn, news {xn['fail']} fail / {xn['warn']} warn"))
    cr = critic.run(plan, out)
    det = next((r for r in cr["rows"] if r[1] == "determinism"), ("FAIL", "", "not run"))
    rows.append(("critic", not cr["fail"] and bool(cr["sheets"] and cr["phones"] and cr["strips"]) and det[0] == "PASS",
                 f"{len(cr['sheets'])} sheets, {len(cr['phones'])} phone pages, {len(cr['strips'])} strips, "
                 f"{det[2].split(': ')[-1]}"))
    code = check(plan, tl, out, report, a, time.time() - t0, rows)
    print(f"  INFO  feed     {xm['preview']}")
    print(f"  INFO  news     {sheet}")
    return code
