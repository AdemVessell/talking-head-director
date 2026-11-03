"""Dialogue edit: plan segments -> EDL, edit-time words and the dialogue track.

Each segment is one kept line (source in/out at energy minima). Between
segments the plan puts `air` frames; picture fills the air with the silent
post-roll of this take ("post") or the pre-roll of the next ("pre"), so the
face always shows the frames that match its own audio. Audio: 10 ms fades on
every cut over a continuous room-tone bed (never digital silence).
"""
import json, math
import numpy as np
import soundfile as sf

from .prep import SR, envelope, load_ranges, quietest, range_of


def build(plan):
    fps = plan.fps; F = 1 / fps
    audio, sr = sf.read(plan.wp("prep", "audio48.wav"), dtype="float32"); assert sr == SR
    aligned = json.loads(plan.wp("prep", "aligned.json").read_text())
    ranges = load_ranges(plan)
    segs = plan["segments"]
    t, edl = 0.0, []
    for s in segs:
        dur = s["out"] - s["in"]
        air = s.get("air", 4) * F
        edl.append(dict(id=s["id"], src_in=s["in"], src_out=s["out"], edit_in=round(t, 4), edit_out=round(t + dur, 4),
                        air_after=air, fill=s.get("fill", "post"), range=range_of(ranges, s["in"])))
        t += dur + air
    edl[-1]["air_after"] = 0.0
    total = math.ceil((edl[-1]["edit_out"] + plan["tail"]) * fps - 1e-6) / fps
    for k, s in enumerate(edl):
        s["p_in"] = round(s["edit_in"] if k == 0 else edl[k - 1]["p_out"], 4)
        s["p_out"] = round(s["edit_out"] + (s["air_after"] if s["fill"] == "post" else 0.0), 4)
    edl[-1]["p_out"] = edl[-1]["edit_out"]

    # room tone: plan's choice or the quietest 2 s that is not a kept line
    if plan.get("room_tone"):
        ra, rb = plan["room_tone"]
    else:
        db = envelope(audio, sr); avoid = [(s["in"], s["out"]) for s in segs]
        q = next((q for L in (2.0, 1.0, 0.5, 0.3) for q in [quietest(db, L, avoid=avoid)] if q), None)
        if q is None:  # no silence anywhere outside the kept lines: the quietest stretch overall
            q = quietest(db, 0.3)
        ra, rb = q[0], q[1]
    rt = audio[int(ra * SR):int(rb * SR)].copy()
    n = int(total * SR) + SR
    bed = np.zeros(n, np.float32); pos = 0; xf = int(0.08 * SR)
    ramp = np.linspace(0, 1, xf, dtype=np.float32)
    while pos < n:
        piece = rt.copy(); piece[:xf] *= ramp; piece[-xf:] *= ramp[::-1]
        m = min(len(piece), n - pos); bed[pos:pos + m] += piece[:m]; pos += len(rt) - xf
    out = bed * 0.9
    fade = int(0.010 * SR)
    r = np.sin(np.linspace(0, np.pi / 2, fade, dtype=np.float32)) ** 2
    for s in edl:
        clip = audio[int(s["src_in"] * SR):int(s["src_out"] * SR)].copy()
        clip[:fade] *= r; clip[-fade:] *= r[::-1]
        i0 = int(round(s["edit_in"] * SR)); e = i0 + len(clip)
        out[i0:e] = clip  # the take carries its own room sound; the bed only crossfades at its edges
        out[i0:i0 + fade] += bed[i0:i0 + fade] * 0.9 * r[::-1]
        out[e - fade:e] += bed[e - fade:e] * 0.9 * r
    sf.write(plan.wp("prep", "dialogue_edit.wav"), out[:int(total * SR)], SR, subtype="FLOAT")

    # edit-time words in display form (digits for numbers, $, names)
    words = []
    for s, ps in zip(edl, segs):
        # a word belongs to the line when its midpoint falls inside it (zero-length edge words included)
        src = [w for w in aligned[s["id"]] if s["src_in"] - 0.03 <= (w["start"] + w["end"]) / 2 <= s["src_out"] + 0.01]
        disp = (ps.get("display") if ps.get("display") is not None else ps["text"]).split()
        if len(src) != len(disp):
            raise SystemExit(f"segment {s['id']}: {len(src)} aligned words {[w['word'] for w in src]} vs "
                             f"{len(disp)} display words {disp}. Fix the in/out points or the display text.")
        for w, d in zip(src, disp):
            ws = max(w["start"], s["src_in"]); we = min(w["end"], s["src_out"])
            words.append({"word": d, "start": round(s["edit_in"] + ws - s["src_in"], 3),
                          "end": round(s["edit_in"] + we - s["src_in"], 3), "seg": s["id"]})
    edl_doc = {"fps": fps, "total": round(total, 4), "room_tone": [ra, rb], "segments": edl}
    plan.wp("prep", "edl.json").write_text(json.dumps(edl_doc, indent=1))
    plan.wp("prep", "words_edit.json").write_text(json.dumps(words, indent=1))
    print(f"total {total:.3f}s ({int(round(total * fps))} frames), room tone {ra:.2f}-{rb:.2f}")
    for s in edl:
        print(f"  {s['id']:>4} src {s['src_in']:7.2f}-{s['src_out']:7.2f}  edit {s['edit_in']:7.3f}-{s['edit_out']:7.3f}"
              f"  picture {s['p_in']:7.3f}-{s['p_out']:7.3f}")
    return edl_doc, words
