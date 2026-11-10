"""Critic pass: `thd critic PLAN`, also the end of `thd all`. Builds the evidence a reviewer scores
from the rendered MP4 alone, measures what a script can, and writes review/CRITIC.md: a rubric to
score 1-10, then the three worst defects to fix, re-render and score again until every line is 8+.

Why (seeco, "Opus 5.5 Motion Design", Oct 2026, from taking the viral code-rendered films apart):
the one habit the clips that blew up shared was the agent judging its own rendered frames, not
what it meant to make. A different agent from the one that cut the video scores it best.

Evidence in review/critic/:
  sheet_NN.jpg   two frames a second, 6 across, 9 s a page
  phone_NN.jpg   the first frame and the middle of every shot at 360 px wide (phone size), 8 a page
  strip_*.jpg    consecutive frames through every plane change (the whole move), around the fastest
                 move, every held frame and every late hit, each sound cue marked on its frame
Measured:
  FAIL  one frame drawn twice by two fresh renderers differs (something is unseeded)
  WARN  a held frame between moving ones (a stutter); the plan or its inputs are newer than the MP4,
        or a patch of a frame differs from what the engine draws now (re-render); a stamp, slap or
        knock more than a frame from the jump in the picture it belongs to
  INFO  stretches of 1.5 s or more where the picture holds still, captions aside; frames held on twos
"""
import json, math, subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import render
from .timeline import Timeline

SHEET_W, PHONE_W = 240, 360
VIA_DUR = {"fall": 0.55, "dive": 0.6, "travel": 0.42, "flip": 0.5}   # journeys.py's plane-change lengths
HITS = {"stamp", "knock", "thud", "paper_slap", "shutter"}   # sounds that must land on a visible jump


def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow without FreeType sizes
        return ImageFont.load_default()


def decode(video, w, h, gray=False, select=None):
    """The review MP4's frames at w x h: all of them, or only the frame indices in `select` (in order)."""
    vf = f"scale={w}:{h}:flags=area"
    if select is not None:
        vf = "select='" + "+".join(f"eq(n\\,{i})" for i in sorted(set(select))) + "'," + vf
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", vf, "-fps_mode", "passthrough",
                          "-f", "rawvideo", "-pix_fmt", "gray" if gray else "rgb24", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8)
    return a.reshape(-1, h, w) if gray else a.reshape(-1, h, w, 3)


def energy(video):
    """Change from the previous frame on a 90 x 160 grey copy (0 for frame 0): the mean over the frame
    (moves, cuts, held frames) and the largest mean over a 10 x 10 patch (lips, ink, a typed letter)."""
    g = decode(video, 90, 160, gray=True).astype(np.int16)
    e = np.zeros(len(g), np.float32); loc = np.zeros(len(g), np.float32)
    for k in range(1, len(g), 600):  # in slices, so a 4-minute video stays small in memory
        j = min(len(g), k + 600)
        dif = np.abs(g[k:j] - g[k - 1:j - 1]).astype(np.float32)
        e[k:j] = dif.mean(axis=(1, 2))
        loc[k:j] = dif.reshape(-1, 16, 10, 9, 10).mean(axis=(2, 4)).max(axis=(1, 2))
    return e, loc


def _runs(mask, min_len):
    out, start = [], None
    for i, m in enumerate(list(mask) + [False]):
        if m and start is None:
            start = i
        elif not m and start is not None:
            if i - start >= min_len:
                out.append((start, i))
            start = None
    return out


def _median5(x):
    return np.array([np.median(x[max(1, i - 2):i + 3]) for i in range(len(x))], np.float32)  # cut spikes removed


def motion(e, loc, fps, moves, skip=()):
    """Held frames inside moves (a stutter, or animation on twos), stretches where nothing visible
    changes anywhere in the frame, and the fastest sustained move outside the plane changes and the
    `skip` spans (seconds)."""
    floor = float(np.percentile(e[1:], 10)) if len(e) > 1 else 0.0
    med = _median5(e)
    # held: only grain changed, between two frames that move
    dips = [i for i in range(2, len(e) - 1)
            if min(e[i - 1], e[i + 1]) > max(4 * floor, 2.0) and e[i] < 1.5 * floor + 0.2]
    stutters, twos, k = [], [], 0
    while k < len(dips):  # three or more dips two frames apart are animation on twos, not a stutter
        j = k
        while j + 1 < len(dips) and dips[j + 1] - dips[j] == 2:
            j += 1
        (twos if j - k >= 2 else stutters).append((dips[k], dips[j]))
        k = j + 1
    lfloor = float(np.percentile(loc[1:], 10)) if len(loc) > 1 else 0.0
    still = _runs(_median5(loc) < 1.5 * lfloor + 0.1, int(round(1.5 * fps)))
    busy = med.copy()
    for t0, dur in list(moves) + list(skip):
        busy[max(0, int(t0 * fps) - 3):int((t0 + dur) * fps) + 3] = 0
    fast = int(np.argmax(busy)) if len(busy) and busy.max() > max(4 * floor, 2.0) else None
    return {"floor": floor, "stutters": stutters, "twos": twos, "still": still, "fast": fast}


def label(img, text, size=16, at=(6, 4), fill=(255, 255, 255)):
    d = ImageDraw.Draw(img); f = _font(size)
    x0, y0, x1, y1 = d.textbbox(at, text, font=f)
    d.rectangle((x0 - 3, y0 - 2, x1 + 3, y1 + 2), fill=(0, 0, 0))
    d.text(at, text, font=f, fill=fill)


def pages(frames, tags, cols, rows, w, path_fmt, marks=None):
    """Grids of frames with a tag on each; returns the written paths."""
    out, per = [], cols * rows
    for p in range(0, len(frames), per):
        chunk = frames[p:p + per]; h = chunk[0].shape[0]
        sheet = Image.new("RGB", (cols * w, math.ceil(len(chunk) / cols) * h), (24, 24, 24))
        for k, fr in enumerate(chunk):
            im = Image.fromarray(fr); label(im, tags[p + k])
            for n, m in enumerate((marks or {}).get(p + k, [])):
                label(im, m, 15, (6, h - 26 - 24 * n), (255, 214, 102))
            sheet.paste(im, ((k % cols) * w, (k // cols) * h))
        path = path_fmt.format(len(out) + 1); sheet.save(path, quality=88); out.append(path)
    return out


def run(plan, out=None):
    tl = Timeline(plan); fps = plan.fps
    video = out or plan.wp("out", plan.get("name", "edit") + ".mp4")
    if not video.exists():
        raise SystemExit(f"no render at {video}: run thd all first")
    d = plan.wp("review", "critic"); d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.jpg"):
        old.unlink()
    rows = []; add = lambda level, what, detail="": rows.append((level, what, detail))
    e, loc = energy(video); nf = len(e)
    shots = [dict(s, t0=tl.t(s["at"])) for s in plan.get("shots") or []] or \
        sorted(({"shot": b.get("name", b["layout"]), "t0": tl.t(b["from"])} for b in plan.get("beats") or []),
               key=lambda s: s["t0"])   # hand-placed plans: their beats
    moves = [(s["t0"], s.get("via_dur", VIA_DUR.get(s["via"], 0.5))) for s in shots if s.get("via")]
    burn = (plan.get("end") or {}).get("burn")
    m = motion(e, loc, fps, moves, [(tl.t(burn[0]), tl.total - tl.t(burn[0]))] if burn else [])  # the burn is no move

    # contact sheets: two frames a second
    idx = list(range(0, nf, max(1, int(round(fps / 2)))))
    hs = round(SHEET_W * plan.H / plan.W)
    sheets = pages(list(decode(video, SHEET_W, hs, select=idx)), [f"{i / fps:.1f}s" for i in idx], 6, 3, SHEET_W,
                   str(d / "sheet_{:02d}.jpg"))

    # phone pages: the first frame, then the middle of every shot
    ends = [s["t0"] for s in shots[1:]] + [tl.total]
    picks = [(0, "0.0s first frame")] + [(min(nf - 1, int((s["t0"] + t1) / 2 * fps)),
              f"{(s['t0'] + t1) / 2:.1f}s {s['shot']}" + (f" {s['size']}" if "size" in s else "") +
              (f" {s['doc']}" if "doc" in s else "")) for s, t1 in zip(shots, ends) if t1 > s["t0"]]
    hp = round(PHONE_W * plan.H / plan.W)
    pf = decode(video, PHONE_W, hp, select=[i for i, _ in picks])
    order = sorted(set(i for i, _ in picks)); by = {i: pf[k] for k, i in enumerate(order)}
    phones = pages([by[i] for i, _ in picks], [t for _, t in picks], 4, 2, PHONE_W, str(d / "phone_{:02d}.jpg"))

    # sound cues, and the hits that miss the frame where the picture jumps
    cues = []
    auto = plan.wp("review", "sfx_auto.json")
    for c in (json.loads(auto.read_text()) if auto.exists() else []) + list(plan.get("sfx") or []):
        try:
            cues.append((tl.t(c["at"]), c["kit"]))
        except (KeyError, ValueError):
            continue
    late, checked = [], 0
    for tt, kit in [(tt, kit) for tt, kit in cues if kit in HITS]:
        i = int(round(tt * fps)); lo = max(1, i - 3); w = e[lo:i + 4]
        around = np.median(e[max(1, i - 12):i + 13]) if i > 1 else 0.0
        if len(w) and w.max() > max(3 * around, 4 * m["floor"], 2.0):  # only where there is a jump to land on
            checked += 1; j = int(np.argmax(w)) + lo - i
            if abs(j) > 1:
                late.append((i, kit, tt, j))

    # strips: every plane change from its first frame to its last, the fastest move, every held frame
    # and every late hit
    spans = [(int(round(t0 * fps)) - 2, min(18, int(round(dur * fps)) + 5), f"plane change ({s['via']})")
             for s, (t0, dur) in zip([s for s in shots if s.get("via")], moves)]   # a frame or two either side
    if m["fast"] is not None:
        spans.append((m["fast"] - 6, 12, "fastest move"))
    spans += [(a - 5, 12, "held frame") for a, _ in m["stutters"]]
    spans += [(i - 5, 12, f"hit ({kit})") for i, kit, _, _ in late]
    strips = []
    for a, n, why in spans:
        a = int(np.clip(a, 0, max(0, nf - n))); ids = list(range(a, min(nf, a + n)))
        fr = decode(video, SHEET_W, hs, select=ids)
        marks = {k: [f"SFX {kit}" for t, kit in cues if abs(t - i / fps) < 0.5 / fps] for k, i in enumerate(ids)}
        strips += pages(list(fr), [f"{i / fps:.2f}s" + (f" {why}" if k == 0 else "") for k, i in enumerate(ids)], 6, 3,
                        SHEET_W, str(d / f"strip_{a / fps:06.2f}s_{{:02d}}.jpg"), marks)
    add("INFO", "evidence", f"{len(sheets)} sheets, {len(phones)} phone pages, {len(strips)} strips -> review/critic/")

    # determinism: one frame drawn by two fresh renderers, then against the MP4
    k = int(round((moves[0][0] + moves[0][1] / 2) * fps)) if moves else nf // 2
    k = int(np.clip(k, 0, nf - 1))
    a = render.Renderer(plan).frame(k); b = render.Renderer(plan).frame(k)
    diff = int(np.abs(a.astype(np.int16) - b).max())
    add("PASS" if diff == 0 else "FAIL", "determinism",
        f"frame {k} ({k / fps:.2f} s) drawn twice: " + ("identical" if diff == 0 else
                                                       f"differs by up to {diff} levels: something is unseeded"))
    # at quarter size, where grain and the encoder's smoothing average out and a moved caption does not
    q = lambda x: cv2.resize(x, (plan.W // 4, plan.H // 4), interpolation=cv2.INTER_AREA).astype(np.float32)
    dq = np.abs(q(decode(video, plan.W, plan.H, select=[k])[0]) - q(a)).mean(axis=2)
    h4, w4 = (dq.shape[0] // 16) * 16, (dq.shape[1] // 16) * 16
    worst = float(dq[:h4, :w4].reshape(h4 // 16, 16, w4 // 16, 16).mean(axis=(1, 3)).max())
    newer = [p.name for p in [plan.path, *plan.wp("prep").glob("*.json")] if p.stat().st_mtime > video.stat().st_mtime]
    stale = worst > 20 or newer
    add("WARN" if stale else "PASS", "the MP4 is current",
        (f"{', '.join(newer)} changed after the render; " if newer else "") +
        f"frame {k} differs from the engine by at most {worst:.0f} levels in any patch" +
        (" (over 20: the plan changed since; re-render)" if worst > 20 else ""))

    # motion the eye trips on
    t = lambda i: f"{i / fps:.2f} s"
    add("WARN" if m["stutters"] else "PASS", "no stutter inside a move",
        "; ".join(f"a held frame at {t(a)}" + ("" if a == b else f"-{t(b)}") for a, b in m["stutters"]) or
        "no held frame between moving ones")
    if m["twos"]:
        add("INFO", "held on twos", "; ".join(f"{t(a)}-{t(b)}" for a, b in m["twos"]) +
            " (stop-motion arrivals are deliberate; a camera move on twos is not)")
    shot_at = lambda tt: next((s for s in reversed(shots) if s["t0"] <= tt), {"shot": "?"})
    add("INFO" if m["still"] else "PASS", "the picture moves",
        "; ".join(f"holds still {t(a)}-{t(b)} ({shot_at(a / fps)['shot']})" for a, b in m["still"]) +
        ", captions aside (fine if it is a beat on purpose)" if m["still"] else "no still stretch of 1.5 s")
    if checked:
        add("WARN" if late else "PASS", "hits on their frames",
            "; ".join(f"{kit} at {tt:.2f} s: the picture jumps {j:+d} frames from it" for _, kit, tt, j in late)
            if late else f"{checked} hits checked")

    md = [f"# Critic pass: {plan.get('name', 'edit')}", "",
          f"{tl.total:.1f} s, {nf} frames. Score only what these frames show, never what the plan meant. A "
          "different agent from the one that cut the video scores it best (one agent cuts, another scores).",
          "", "1. Score each line from 1 to 10.",
          "2. List the three worst defects: the time, the image that shows it, and the local fix (the plan line to change).",
          "3. Fix them, run `thd all` (it ends with this pass), and score the new evidence. Done when every line is 8 or more.",
          "", "| score | criterion | look at |", "|---|---|---|",
          "|  | **Hook in 2 s:** the hook line is spoken, readable and already moving | `critic/phone_01.jpg` (first frame), `audit/first-3s.jpg` |",
          "|  | **Phone readability:** every caption and paper line reads at 360 px | `critic/phone_*.jpg` |",
          "|  | **Motion:** moves ease and settle, plane changes blur instead of stepping, no stutter | `critic/strip_*.jpg`, Measured |",
          "|  | **Variety:** something new every 2-4 s; no layout carries most of the runtime | `critic/sheet_*.jpg` |",
          "|  | **Sound:** whooshes start with their moves, hits land on their frames, dialogue in sync | strips (SFX marks), Measured, `QA.md` |",
          "|  | **Accuracy:** numbers, names, sources and hedges match the facts; nothing invented | `X_CHECK.md` claims |",
          "|  | **Craft:** grid and baselines hold, nothing overlaps or clips, his performance carries it, no plain CGI | `critic/sheet_*.jpg`, `critic/phone_*.jpg` |",
          "", "## Measured", "", "| result | check | detail |", "|---|---|---|"]
    md += [f"| {lv} | {what} | {detail} |" for lv, what, detail in rows]
    md += ["", "## Evidence", ""] + [f"- `critic/{p.split('/')[-1]}`" for p in sheets + phones + strips]
    md += ["", "## The three worst defects", "", "1. ", "2. ", "3. "]
    plan.wp("review", "CRITIC.md").write_text("\n".join(md) + "\n")
    n = {k: sum(r[0] == k for r in rows) for k in ("PASS", "WARN", "FAIL")}
    print(f"critic {plan.get('name', 'edit')}")
    for lv, what, detail in rows:
        print(f"  {lv:4s}  {what:28s} {detail}")
    print(f"{n['PASS']} pass, {n['WARN']} warn, {n['FAIL']} fail -> {plan.wp('review', 'CRITIC.md')}: "
          "score it, fix the worst three, re-render")
    return {"fail": n["FAIL"], "warn": n["WARN"], "rows": rows, "sheets": sheets, "phones": phones, "strips": strips}
