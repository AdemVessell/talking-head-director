"""Document lives: when each paper arrives (appear, slap, drop, tape), when each line's ink
reveals (cues; `follow: true` writes each line while he says it) and when each accent lands
(marks). Shared by the stage (pictures), shots (the camera follows the writing) and sound
(each reveal gets its pen, keys or print head).

Cue forms, per line index:  "expr"  |  [expr, seconds]  |  [expr, "end-expr"]  |  {at, dur | to, mode}
(a number is a length, a string is a time). `values`/`waves` are the receipt-era names for cues.
`marker: {at, lines: [a, b]}` circles lines; on a screenshot, `marker: {at, box: [x0, y0, x1, y1]}`
circles part of the image (fractions). Stamps land on `line` (default 4; on a screenshot, the image).
"""
from . import materials

# seconds per character (clamped): how fast each pen or print head moves when a cue gives no length
REVEAL_PACE = {"type": (0.045, 0.25, 1.4), "write": (0.055, 0.3, 1.7), "draw": (0.04, 0.3, 1.2),
               "print": (0.016, 0.12, 0.6), "wipe": (0.0, 0.5, 0.5), "ink": (0.0, 0.1, 0.1)}


def reveal_dur(mode, L):
    per, lo, hi = REVEAL_PACE[mode]
    return min(hi, max(lo, per * max(4, len(L.get("text", "")))))


def line_mode(doc_mode, L):
    """A waveform prints as a sweep; bars, boxes and rules sweep under type and print heads."""
    if L["wave"]:
        return "wipe"
    if L["spec"].startswith(("bar:", "box:")) or L["spec"] in ("rule", "rule2"):
        return "wipe" if doc_mode in ("ink", "type", "print") else doc_mode
    return doc_mode


def cue(tl, fps, v, mode, L, dur=None):
    if isinstance(v, dict):
        mode = v.get("mode", mode); t0 = tl.t(v["at"])
        t1 = tl.t(v["to"]) if "to" in v else t0 + float(v.get("dur", dur or reveal_dur(mode, L)))
    elif isinstance(v, (list, tuple)):
        t0 = tl.t(v[0]); t1 = tl.t(v[1]) if isinstance(v[1], str) else t0 + float(v[1])
    else:
        t0 = tl.t(v); t1 = t0 + (dur or reveal_dur(mode, L))
    return (t0, max(t1, t0 + 1.0 / fps), mode)


def follow(tl, name, m, life, given):
    """Each text line writes itself while he says it, first word to last."""
    out, after = {}, life.get("appear", 0.0)
    for L in m["lines"]:
        if L["i"] in given or L["wave"] or not L.get("text") or L.get("caption"):  # a print's source is not said
            continue
        span = tl.phrase(L["text"], after)
        if span is None:
            print(f"  [lives] {name}: line {L['i']} '{L['text']}' is not in his words after {after:.2f}s; "
                  f"it is on the paper when the paper arrives")
            continue
        mode = life["modes"][L["i"]]
        out[L["i"]] = (span[0], max(span[1], span[0] + reveal_dur(mode, L) * 0.5), mode)
        after = span[0] + 0.01
    return out


def resolve(plan, tl, meta):
    fps = plan.fps; lives = {}
    for name, r in materials.docs_of(plan).items():
        m = meta["docs"][name]; life = {"kind": r["kind"]}
        if "appear" in r:
            life["appear"] = tl.t(r["appear"])
        if "drop" in r:
            a, b, dist = r["drop"]; life["drop"] = (tl.t(a), tl.t(b), float(dist))
            life.setdefault("appear", tl.t(a))
        if "slap" in r:  # lands on its cue with a two-frame scale pop
            life["slap"] = tl.t(r["slap"]); life.setdefault("appear", life["slap"])
        if "tape_at" in r:
            life["tape_at"] = tl.t(r["tape_at"])
        mode = r.get("reveal", m.get("reveal", "ink"))
        life["modes"] = {L["i"]: line_mode(mode, L) for L in m["lines"]}
        raw = {}
        for src in ("waves", "values", "cues"):
            for k, v in (r.get(src) or {}).items():
                raw[int(k)] = v
        cues = follow(tl, name, m, life, raw) if r.get("follow") else {}
        for i, v in raw.items():
            cues[i] = cue(tl, fps, v, life["modes"][i], m["lines"][i])
        life["cues"] = cues
        marks = {int(k): cue(tl, fps, v, "write", m["lines"][int(k)], dur=0.3) for k, v in (r.get("marks") or {}).items()}
        for L in m["lines"]:  # an accent with no cue of its own lands as its line finishes
            if L.get("acc") and L["i"] not in marks and L["i"] in cues:
                t1 = cues[L["i"]][1]; marks[L["i"]] = (t1 + 0.08, t1 + 0.38, "write")
        life["marks"] = marks
        if "marker" in r:
            mk = r["marker"]; t0 = tl.t(mk["at"])
            if "box" in mk:
                if r["kind"] != "screenshot":
                    raise SystemExit(f"document {name!r}: marker box is for screenshots; circle paper lines with lines: [a, b]")
                target = ("box",) + tuple(float(v) for v in mk["box"])
            else:
                target = tuple(mk["lines"])
            life["marker"] = (t0, t0 + float(mk.get("dur", 0.34)), target)
        last = len(m["lines"]) - 1; home = 0 if r["kind"] == "screenshot" else 4
        life["stamps"] = [dict(at=tl.t(s["at"]), text=s.get("text", "TESTED"), line=min(int(s.get("line", home)), last),
                               angle=float(s.get("angle", -7)), width=float(s.get("width", 330)))
                          for s in r.get("stamps", [])]
        lives[name] = life
    return lives
