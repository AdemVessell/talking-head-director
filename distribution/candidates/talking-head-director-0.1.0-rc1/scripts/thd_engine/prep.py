"""Prep: transcribe a new recording, extract the source ranges the plan uses,
track the face, force-align each kept line, and help choose cut points.

  transcribe(src, out)   whole-recording word transcript (to write the plan from)
  extract(plan)          source ranges -> ProRes (flip/fps applied), 48 kHz audio
  track(plan)            face track per range (face_track.py; `face: center` skips detection)
  align(plan)            stable-ts forced alignment of each segment's text
  inspect(plan)          energy + word timing around every cut; room-tone pick
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf

from .plan import SCRIPTS

SR = 48000


def fps_arg(plan):
    f = plan["fps"]
    return str(f) if not isinstance(f, float) or abs(f - 23.976) > 0.01 else "24000/1001"


# ---------------------------------------------------------------- transcribe

def transcribe(src, out_dir, model="medium.en"):
    import warnings
    import stable_whisper
    warnings.filterwarnings("ignore")
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    wav = out / "transcribe16k.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)
    m = stable_whisper.load_model(model, device="cpu")
    r = m.transcribe(str(wav), language="en", word_timestamps=True, vad=False, verbose=None)
    segs = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
             "words": [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)} for w in s.words]}
            for s in r.segments]
    (out / "transcript.json").write_text(json.dumps(segs, indent=1))
    lines = [f"{s['start']:7.2f}-{s['end']:7.2f}  {s['text']}" for s in segs]
    (out / "transcript.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return segs


# ---------------------------------------------------------------- ranges

def ranges_for(plan):
    """Merge segment handles into a few contiguous source ranges r1..rn."""
    pre, post = plan["margins"]
    spans = sorted((max(0.0, s["in"] - pre), s["out"] + post) for s in plan["segments"])
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1] + 1.0:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return {f"r{i + 1}": [round(a, 3), round(b, 3)] for i, (a, b) in enumerate(merged)}


def range_of(ranges, t):
    for k, (a, b) in ranges.items():
        if a <= t <= b:
            return k
    raise ValueError(f"source time {t} is outside every extracted range")


def extract(plan):
    src = str(Path(plan["source"]).expanduser())
    ranges = ranges_for(plan)
    vf = ",".join(x for x in ["hflip" if plan["flip"] else "", f"fps={fps_arg(plan)}"] if x)
    for k, (a, b) in ranges.items():
        out = plan.wp("prep", f"{k}.mov")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-i", src,
                        "-t", f"{b - a:.3f}", "-vf", vf, "-an", "-c:v", "prores_ks", "-profile:v", "3",
                        "-pix_fmt", "yuv422p10le", str(out)], check=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-vn", "-ac", "1",
                    "-ar", str(SR), "-c:a", "pcm_f32le", str(plan.wp("prep", "audio48.wav"))], check=True)
    plan.wp("prep", "ranges.json").write_text(json.dumps({"source": src, "flip": plan["flip"], "ranges": ranges}, indent=1))
    print("ranges:", ranges)
    return ranges


def extract_films(plan):
    """Each film window -> ProRes at the plan's fps (and size, if given)."""
    for fid, f in plan.get("films", {}).items():
        src = str(Path(plan["source"] if f["video"] == "self" else f["video"]).expanduser())
        flip = plan["flip"] and f["video"] == "self"
        vf = [x for x in ["hflip" if flip else "", f"fps={fps_arg(plan)}"] if x]
        if f.get("scale"):
            vf.insert(0, f"scale={f['scale'][0]}:{f['scale'][1]}:flags=lanczos")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{f['from']:.3f}", "-i", src,
                        "-t", f"{f['to'] - f['from']:.3f}", "-vf", ",".join(vf), "-an", "-c:v", "prores_ks",
                        "-profile:v", "3", "-pix_fmt", "yuv422p10le", str(plan.wp("prep", f"film_{fid}.mov"))], check=True)


def load_ranges(plan):
    return json.loads(plan.wp("prep", "ranges.json").read_text())["ranges"]


def track(plan, every=2):
    for k in load_ranges(plan):
        if plan.get("face"):
            fixed_track(plan, k, plan["face"])
            continue
        subprocess.run([sys.executable, str(SCRIPTS / "face_track.py"), str(plan.wp("prep", f"{k}.mov")),
                        "--out", str(plan.wp("prep", f"track_{k}.json")), "--every", str(every),
                        "--debug", str(plan.wp("review", f"track_{k}.jpg"))], check=True)


def fixed_track(plan, k, face):
    """`face: center`, or {x, eye, width} as fractions of the source frame: a constant track
    and no detector, for screen recordings and sources without a frontal face."""
    import cv2
    f = {"x": 0.5, "eye": 0.42, "width": 0.3, **(face if isinstance(face, dict) else {})}
    src = plan.wp("prep", f"{k}.mov"); cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or plan.fps
    W, H, n = (int(cap.get(p)) for p in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FRAME_COUNT))
    if n <= 0:  # no count in the header: count the frames (Footage clamps to the real length)
        n = 0
        while cap.grab():
            n += 1
    cap.release()
    row = [round(f["x"] * W, 2), round(f["eye"] * H, 2), round(f["width"] * W, 2)]
    plan.wp("prep", f"track_{k}.json").write_text(json.dumps({
        "source": str(src), "detector": "fixed", "fps": fps, "width": W, "height": H, "frames": n, "detections": 0,
        "kept_fraction": 1.0, "columns": ["center_x", "eye_y", "face_width"], "track": [row] * n}))
    print(f"track {k}: fixed face (x {f['x']}, eye {f['eye']}, width {f['width']}), no detector")


# ---------------------------------------------------------------- alignment

def align(plan, model="medium.en"):
    import warnings
    import stable_whisper
    warnings.filterwarnings("ignore")
    audio, sr = sf.read(plan.wp("prep", "audio48.wav"), dtype="float32")
    m = stable_whisper.load_model(model, device="cpu")
    out = {}
    for s in plan["segments"]:
        if not s["text"].strip():  # a sound-only segment (taps, a demo): no words to align
            out[s["id"]] = []; print(s["id"], "(no words)"); continue
        a, b = s["in"] - 0.20, s["out"] + 0.20
        seg = audio[int(max(0, a) * sr):int(b * sr)]
        s16 = np.interp(np.arange(0, len(seg), sr / 16000), np.arange(len(seg)), seg).astype(np.float32)
        r = m.align(s16, s["text"], language="en")
        words = [{"word": w.word.strip(), "start": round(max(0, a) + w.start, 3), "end": round(max(0, a) + w.end, 3)}
                 for x in r.segments for w in x.words]
        db = envelope(audio, sr); thr = speech_threshold(db)
        for w in words:  # a word ASR stretched over trailing taps or breath ends where the voice ends
            if w["end"] - w["start"] > 0.8:
                i0, i1 = int((w["start"] + 0.15) / 0.01), int(w["end"] / 0.01)
                quiet = np.where(db[i0:i1] < thr)[0]
                for q in quiet:  # first stretch of >= 80 ms below the speech threshold
                    if np.all(db[i0 + q:i0 + q + 8] < thr):
                        w["end"] = round((i0 + q) * 0.01 + 0.03, 3); break
        fixes = s.get("word_fixes", {})  # {"word#k": [start, end]} in source time
        for key, (ws, we) in fixes.items():
            word, k = key.rsplit("#", 1) if "#" in key else (key, "1")
            hits = [w for w in words if w["word"].lower().strip(",.?!") == word.lower().strip(",.?!")]
            if len(hits) >= int(k):
                hits[int(k) - 1]["start"], hits[int(k) - 1]["end"] = ws, we
        out[s["id"]] = words
        print(s["id"], " ".join(f"{w['word']}[{w['start']:.2f}]" for w in words))
    plan.wp("prep", "aligned.json").write_text(json.dumps(out, indent=1))
    return out


# ---------------------------------------------------------------- cut-point help

def envelope(audio, sr, hop=0.01, win=0.03):
    h, w = int(hop * sr), int(win * sr)
    n = (len(audio) - w) // h
    idx = np.arange(w)[None, :] + h * np.arange(n)[:, None]
    return 20 * np.log10(np.sqrt((audio[idx] ** 2).mean(1)) + 1e-12)


def hf_envelope(audio, sr, hop=0.01, win=0.03, lo=4000, hi=10000):
    """Energy above 4 kHz per frame: a sibilant ("veins", "this") is quiet in broadband loudness
    but loud here, so cut points must respect both."""
    h, w = int(hop * sr), int(win * sr)
    n = (len(audio) - w) // h; wf = np.hanning(w).astype(np.float32)
    f = np.fft.rfftfreq(w, 1 / sr); band = (f >= lo) & (f <= hi)
    out = np.empty(n, np.float32)
    for i in range(0, n, 2048):  # chunked: bounded memory on long recordings
        idx = np.arange(w)[None, :] + h * np.arange(i, min(n, i + 2048))[:, None]
        X = np.abs(np.fft.rfft(audio[idx] * wf, axis=1)) ** 2
        out[i:i + len(idx)] = 10 * np.log10(X[:, band].sum(1) + 1e-12)
    return out


def sound_mask(audio, sr):
    """Frames where he makes any sound: voicing or a fricative's hiss. Returns (mask, db, thr)."""
    db = envelope(audio, sr); hf = hf_envelope(audio, sr); n = min(len(db), len(hf))
    thr = speech_threshold(db); hthr = speech_threshold(hf)
    return (db[:n] > thr) | (hf[:n] > hthr), db, thr


def speech_threshold(db):
    floor, speech = np.percentile(db, 8), np.percentile(db, 75)
    return max(floor + 0.25 * (speech - floor), speech - 30)


def regions(db, thr, t0, t1, hop=0.01, mask=None):
    i0, i1 = int(t0 / hop), int(t1 / hop)
    out, s = [], None
    for k, v in enumerate((mask if mask is not None else db > thr)[i0:i1]):
        t = (i0 + k) * hop + 0.015
        if v and s is None:
            s = t
        if not v and s is not None:
            out.append((round(s, 2), round(t, 2))); s = None
    if s is not None:
        out.append((round(s, 2), round(t1, 2)))
    return out


def quietest(db, length=2.0, hop=0.01, avoid=()):
    L = int(length / hop)
    cs = np.convolve(db, np.ones(L) / L, mode="valid")
    for i in np.argsort(cs):
        t = i * hop
        if all(not (a - length < t < b) for a, b in avoid):
            return round(t, 2), round(t + length, 2), round(float(cs[i]), 1)
    return None


def inspect(plan):
    audio, sr = sf.read(plan.wp("prep", "audio48.wav"), dtype="float32")
    mask, db, thr = sound_mask(audio, sr)  # voiced or hissing: a cut inside either clips a word
    aligned = json.loads(plan.wp("prep", "aligned.json").read_text()) if plan.wp("prep", "aligned.json").exists() else {}
    lines = [f"speech threshold {thr:.1f} dB (regions include sibilant hiss above 4 kHz)"]
    for s in plan["segments"]:
        regs_in = regions(db, thr, max(0, s["in"] - 0.8), s["in"] + 0.6, mask=mask)
        regs_out = regions(db, thr, s["out"] - 0.6, s["out"] + 0.8, mask=mask)
        for edge, t in (("in", s["in"]), ("out", s["out"])):
            i = int(t / 0.01)
            if 0 < i < len(mask) and mask[i - 1] and mask[min(i, len(mask) - 1)]:
                lines.append(f"   ! {edge} point {t:.2f} sits inside sound (voiced or a sibilant): move it to a gap")
        ws = aligned.get(s["id"], [])
        first = ws[0] if ws else None; last = ws[-1] if ws else None
        lines.append(f"{s['id']}: in {s['in']:.2f}  out {s['out']:.2f}  '{s['text'][:48]}'")
        lines.append(f"   voiced near in : {regs_in}   first word {first}")
        lines.append(f"   voiced near out: {regs_out}   last word {last}")
        flag = [w["word"] for w in ws if w["end"] - w["start"] < 0.04 or w["end"] - w["start"] > 1.0]
        if flag:
            lines.append(f"   check timing of: {flag} (zero-length or stretched)")
    q = quietest(db, avoid=[(s["in"], s["out"]) for s in plan["segments"]])
    lines.append(f"quietest 2 s for room tone: {q}")
    text = "\n".join(lines)
    plan.wp("review", "inspect.txt").write_text(text + "\n")
    print(text)
    return text
