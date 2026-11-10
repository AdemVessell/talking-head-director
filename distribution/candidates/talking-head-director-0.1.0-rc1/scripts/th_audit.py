#!/usr/bin/env python3
"""Pacing / loudness / legibility audit for a finished talking-head render.

Measures what a viewer feels but a receipt hides: how long the picture holds
still, how much dead air is left, how loud it is, and what the first three
seconds look like. Writes a markdown report, a JSON report, a full contact
sheet and a first-3-seconds strip.

usage: th_audit.py VIDEO [--out DIR] [--words WORDS.json] [--scene 0.12]
                         [--sheet-every 2.0] [--target-median 2.5] [--max-hold 6]
WORDS.json (optional): list of {"word"|"text", "start", "end"} in output time.
"""
import argparse, json, math, re, statistics, subprocess, sys
from pathlib import Path
import numpy as np

FILLERS = ["you know", "i mean", "kind of", "sort of", "i guess", "basically",
           "obviously", "whatever", "like", "um", "uh", "yeah so", "so yeah",
           "just in general", "as it seems", "or something", "or whatever"]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(video):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
             "-of", "json", str(video)])
    j = json.loads(r.stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    num, den = v["r_frame_rate"].split("/")
    return float(j["format"]["duration"]), int(v["width"]), int(v["height"]), float(num) / float(den)


def visual_changes(video, thresh):
    r = run(["ffmpeg", "-hide_banner", "-i", str(video), "-an", "-vf",
             f"scale=180:-2,select='gt(scene,{thresh})',showinfo", "-f", "null", "-"])
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def envelope(video, sr=16000, hop=0.02):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", str(sr),
                        "-f", "f32le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.float32)
    n = int(sr * hop)
    if x.size < n:
        return np.zeros(0), hop
    x = x[: x.size // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((x ** 2).mean(1)) + 1e-9), hop


def pauses(db, hop, min_len):
    """Gaps relative to this file's own speech level, not a fixed dB."""
    if db.size == 0:
        return [], None
    speech, floor = np.percentile(db, 90), np.percentile(db, 10)
    th = max(floor + 0.25 * (speech - floor), speech - 30)
    quiet = db < th
    out, start = [], None
    for i, q in enumerate(np.append(quiet, False)):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if (i - start) * hop >= min_len:
                out.append((start * hop, (i - start) * hop))
            start = None
    return out, float(th)


def loudness(video):
    r = run(["ffmpeg", "-hide_banner", "-i", str(video), "-vn", "-af",
             "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        return None
    j = json.loads(m.group(0))
    return {"integrated_lufs": float(j["input_i"]), "true_peak_dbtp": float(j["input_tp"]), "lra": float(j["input_lra"])}


# Pick frames by their own timestamps (select), not with the fps filter: fps=1/N
# outputs the last frame of each window, so labels ran up to N/2 s early.
def _pick(every, until=None):
    sel = f"isnan(prev_selected_t)+gte(t-prev_selected_t\\,{every - 0.001})"
    if until is not None:
        sel = f"lt(t\\,{until})*({sel})"
    return f"select='{sel}'"


def sheet(video, out, every, cols=8, w=216):
    vf = (f"{_pick(every)},scale={w}:-2,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=15:"
          f"fontcolor=yellow:box=1:boxcolor=black@0.6,tile={cols}x4")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", vf, "-fps_mode", "vfr", str(out / "sheet-%02d.jpg")])
    return sorted(str(p) for p in out.glob("sheet-*.jpg"))


def first3(video, out):
    vf = (f"{_pick(0.25, 3)},scale=216:-2,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=15:fontcolor=yellow:"
          "box=1:boxcolor=black@0.6,tile=6x2")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", vf, "-fps_mode", "vfr", "-frames:v", "1",
         str(out / "first-3s.jpg")])
    return str(out / "first-3s.jpg")


def word_stats(path, dur):
    words = json.loads(Path(path).read_text())
    if isinstance(words, dict):
        words = next((v for v in words.values() if isinstance(v, list)), [])
    toks = [str(w.get("word") or w.get("text") or "").strip().lower() for w in words]
    text = " " + " ".join(re.sub(r"[^a-z0-9' ]", " ", t) for t in toks) + " "
    text = re.sub(r"\s+", " ", text)
    hits = {f: len(re.findall(rf"(?<= ){re.escape(f)}(?= )", text)) for f in FILLERS}
    nwords = sum(len(t.split()) for t in toks)
    gaps = [float(b["start"]) - float(a["end"]) for a, b in zip(words, words[1:])]
    long_gaps = [g for g in gaps if g >= 0.25]
    return {"words": nwords, "wpm": round(nwords / dur * 60, 1),
            "word_gaps_ge_0.25s": {"count": len(long_gaps), "total_s": round(sum(long_gaps), 2)},
            "filler_candidates": {k: v for k, v in hits.items() if v},
            "note": "'like' and 'so' are often real words: review each hit, do not auto-delete."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out")
    ap.add_argument("--words")
    ap.add_argument("--scene", type=float, default=0.12, help="scene-change threshold (0.08 catches subtler moves)")
    ap.add_argument("--sheet-every", type=float, default=2.0)
    ap.add_argument("--min-pause", type=float, default=0.25)
    ap.add_argument("--target-median", type=float, default=2.5)
    ap.add_argument("--max-hold", type=float, default=6.0)
    a = ap.parse_args()
    video = Path(a.video).resolve()
    out = Path(a.out or video.parent / f"audit-{video.stem}")
    out.mkdir(parents=True, exist_ok=True)

    dur, w, h, fps = probe(video)
    cuts = visual_changes(video, a.scene)
    edges = [0.0] + cuts + [dur]
    holds = [(s, e - s) for s, e in zip(edges, edges[1:]) if e - s > 0.04]
    lens = sorted(x for _, x in holds)
    long_holds = sorted([(round(s, 2), round(l, 2)) for s, l in holds if l > a.max_hold], key=lambda x: -x[1])
    db, hop = envelope(video)
    gaps, th = pauses(db, hop, a.min_pause)
    loud = loudness(video)
    rep = {
        "video": str(video), "duration_s": round(dur, 2), "size": f"{w}x{h}", "fps": round(fps, 3),
        "visual_changes": len(cuts), "changes_per_10s": round(len(cuts) / dur * 10, 2),
        "hold_median_s": round(statistics.median(lens), 2) if lens else None,
        "hold_p90_s": round(lens[int(0.9 * (len(lens) - 1))], 2) if lens else None,
        "hold_max_s": round(lens[-1], 2) if lens else None,
        "holds_over_max": long_holds[:12],
        "first_change_s": round(cuts[0], 2) if cuts else None,
        "pauses": {"count": len(gaps), "total_s": round(sum(g for _, g in gaps), 2), "threshold_db": th,
                   "longest": [(round(s, 2), round(g, 2)) for s, g in sorted(gaps, key=lambda x: -x[1])[:10]]},
        "loudness": loud,
        "contact_sheets": sheet(video, out, a.sheet_every),
        "first_3s_strip": first3(video, out),
    }
    if a.words:
        rep["speech"] = word_stats(a.words, dur)

    checks = []
    def chk(name, ok, detail):
        checks.append((("PASS" if ok else "WARN"), name, detail))
    med = rep["hold_median_s"] or 99
    chk("median hold", med <= a.target_median, f"{med}s (target <= {a.target_median}s)")
    chk("longest hold", (rep["hold_max_s"] or 99) <= a.max_hold, f"{rep['hold_max_s']}s (target <= {a.max_hold}s unless marked intentional)")
    chk("first visual change", (rep["first_change_s"] or 99) <= 2.0, f"{rep['first_change_s']}s (target <= 2s)")
    pmin = rep["pauses"]["count"] / max(dur / 60, 1e-6)
    chk("dead air", pmin <= 4, f"{rep['pauses']['count']} pauses >= {a.min_pause}s, {rep['pauses']['total_s']}s total ({pmin:.1f}/min, target <= 4/min)")
    if loud:
        chk("loudness", -15.0 <= loud["integrated_lufs"] <= -13.0 and loud["true_peak_dbtp"] <= -1.0,
            f"{loud['integrated_lufs']:.1f} LUFS, {loud['true_peak_dbtp']:.1f} dBTP (target -14 +/-1, TP <= -1)")
    if "speech" in rep:
        s = rep["speech"]
        chk("speech density", s["wpm"] >= 155, f"{s['wpm']} wpm (target 155-190 after tightening)")
        nf = sum(s["filler_candidates"].values())
        chk("filler candidates", nf <= 3, f"{nf} hits {s['filler_candidates']}")
    rep["checks"] = [{"status": c[0], "check": c[1], "detail": c[2]} for c in checks]
    (out / "audit.json").write_text(json.dumps(rep, indent=2))
    md = [f"# Audit: {video.name}", "", f"{rep['duration_s']}s, {rep['size']} @ {rep['fps']} fps", ""]
    md += [f"- **{c[0]}** {c[1]}: {c[2]}" for c in checks]
    md += ["", "Longest holds (start s, length s): " + str(long_holds[:8]),
           "Longest pauses (start s, length s): " + str(rep["pauses"]["longest"][:8]), "",
           "Look at these before judging: " + ", ".join(Path(p).name for p in rep["contact_sheets"]) + ", first-3s.jpg",
           "Holds count cuts and large changes; slow drifts and gentle reframes don't register, so read",
           "long holds against the shot timeline. With --words, trust the word-gap pauses over the audio",
           "ones when music or room tone fills the gaps.",
           "Numbers measure rhythm, not taste. A PASS here is necessary, not sufficient."]
    (out / "audit.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nreport: {out/'audit.md'}")


if __name__ == "__main__":
    main()
