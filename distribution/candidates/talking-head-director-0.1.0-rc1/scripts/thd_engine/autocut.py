"""Autocut: a first story cut from the word transcript, so a one-to-four-minute recording starts
from a draft instead of a blank plan.

It removes only what needs no judgement: fillers (um, uh, erm, ah, hmm), stutters and exact
repeats ("waxing waxing", "I was, I was") and long pauses. Every in point sits in the quiet
just before the first voiced sound, every out point after the last consonant's release
(energy, not ASR word times). It never reorders and never drops a sentence: choosing the story
(hook first, what to cut, what to keep of his hedges) is the editor's job, done on this draft.

  edit_engine.py autocut RECORDING --out DIR [--pause 0.35]
writes DIR/plan_draft.yaml (source, fps, segments with verbatim text) and DIR/autocut.txt
(the transcript with every removal marked, and the length before and after).
"""
import json, subprocess
from pathlib import Path
import numpy as np
import soundfile as sf

from .prep import SR, sound_mask, transcribe
from .timeline import norm

FILLERS = {"um", "umm", "uh", "uhh", "erm", "er", "ah", "ahh", "hmm", "mm", "mhm"}


def _ids():
    import string
    for c in string.ascii_uppercase:
        yield c
    for a in string.ascii_uppercase:
        for c in string.ascii_uppercase:
            yield a + c


def _repeats(W):
    """Indexes of the first copy of an immediately repeated run of 1-4 words."""
    drop = set(); n_w = len(W)
    for n in (4, 3, 2, 1):
        for i in range(n_w - 2 * n + 1):
            if any(j in drop for j in range(i, i + 2 * n)):
                continue
            a = [norm(W[j]["word"]) for j in range(i, i + n)]; b = [norm(W[j]["word"]) for j in range(i + n, i + 2 * n)]
            if a == b and all(a) and W[i + n]["start"] - W[i + n - 1]["end"] < 0.8:
                drop.update(range(i, i + n))
    return drop


def _quiet_run(mask, i, step, need):
    """From frame i, walk by step until `need` consecutive frames are silent (no voice, no hiss)."""
    run = 0
    while 0 <= i < len(mask):
        run = run + 1 if not mask[i] else 0
        if run >= need:
            return i - step * (need - 1)
        i += step
    return None


def draft(source, out_dir, pause=0.35, model="medium.en"):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    tj = out / "transcript.json"
    segs = json.loads(tj.read_text()) if tj.exists() else transcribe(source, out, model)
    W = [dict(w, k=k) for k, w in enumerate(x for s in segs for x in s["words"])]
    wav = out / "audio48.wav"
    if not wav.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", str(SR),
                        "-c:a", "pcm_f32le", str(wav)], check=True)
    audio, sr = sf.read(wav, dtype="float32"); mask, _, _ = sound_mask(audio, sr)
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                            "-of", "csv=p=0", str(source)], capture_output=True, text=True).stdout.strip()
    num, den = (probe or "30/1").split("/"); src_fps = float(num) / float(den)
    fps = 23.976 if abs(src_fps - 23.976) < 0.05 else (25 if abs(src_fps - 25) < 0.05 else 30)
    why = {}
    for w in W:
        if norm(w["word"]) in FILLERS:
            why[w["k"]] = "filler"
    for k in _repeats(W):
        why.setdefault(k, "repeat")
    keep = [w for w in W if w["k"] not in why]
    phrases, cur = [], []
    for w in keep:  # a removed word or a long pause starts a new phrase (each boundary is a cut)
        gap = w["start"] - cur[-1]["end"] if cur else 0
        sentence = cur and cur[-1]["word"].rstrip()[-1:] in ".?!" and gap >= 0.06  # sentences can be reordered apart
        if cur and (gap > pause or sentence or any(k in why for k in range(cur[-1]["k"] + 1, w["k"]))):
            phrases.append(cur); cur = []
        cur.append(w)
    if cur:
        phrases.append(cur)
    segments, ids, prev_out = [], _ids(), 0.0
    for p, nxt in zip(phrases, phrases[1:] + [None]):
        a = int((p[0]["start"] + 0.06) / 0.01); b = int((p[-1]["end"] - 0.06) / 0.01)
        qi = _quiet_run(mask, a, -1, 3); qo = _quiet_run(mask, b, 1, 4)
        t_in = max(prev_out + 0.01, (qi * 0.01 - 0.02) if qi is not None else p[0]["start"] - 0.06, p[0]["start"] - 0.25)
        t_out = min((qo * 0.01 + 0.04) if qo is not None else p[-1]["end"] + 0.06, p[-1]["end"] + 0.3)
        if nxt is not None:
            t_out = min(t_out, nxt[0]["start"] - 0.03)
        text = " ".join(w["word"] for w in p)
        end_sentence = text.rstrip()[-1:] in ".?!"
        gap = (nxt[0]["start"] - p[-1]["end"]) if nxt else 0
        air = 2 if not end_sentence else (5 if gap < 1.0 else 7)
        segments.append({"id": next(ids),
                         "in": float(round(float(t_in), 3)),
                         "out": float(round(float(max(t_out, t_in + 0.1)), 3)),
                         "air": int(air), "fill": "post", "text": text})
        prev_out = float(t_out)
    total_src = W[-1]["end"] - W[0]["start"] if W else 0
    total_cut = sum(s["out"] - s["in"] + s["air"] / fps for s in segments)
    log = [f"autocut {source}", f"{len(W)} words, {len(why)} removed ({sum(v == 'filler' for v in why.values())} fillers, "
           f"{sum(v == 'repeat' for v in why.values())} repeats), {len(segments)} segments; "
           f"speech {total_src:.1f}s -> {total_cut:.1f}s", ""]
    log.append(" ".join(f"[-{w['word']}-]" if w["k"] in why else w["word"] for w in W))
    (out / "autocut.txt").write_text("\n".join(log) + "\n")
    lines = [f"# autocut draft: {log[1]}", "# Now choose the story: reorder, drop, merge; keep his hedges. See autocut.txt.",
             f"name: {Path(source).stem[:40].strip().replace(' ', '-').lower()}", f"work_dir: {out / 'work'}",
             f"source: {json.dumps(str(source))}", f"fps: {fps}", "treatment: evidence   # evidence studio workshop newsroom lab pinboard classroom",
             "segments:"]
    for s in segments:
        lines.append(f"  - {{id: {s['id']}, in: {s['in']}, out: {s['out']}, air: {s['air']}, fill: post, text: {json.dumps(s['text'])}}}")
    (out / "plan_draft.yaml").write_text("\n".join(lines) + "\n")
    print("\n".join(log[:2])); print("->", out / "plan_draft.yaml")
    return segments
