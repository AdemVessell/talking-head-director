"""Shot templates: one line per shot instead of hand-placed layouts and camera keys, so a
four-minute video is a forty-line beat sheet, not a thousand-line plan.

plan["shots"]: [{at: "B.pin", shot: face|doc|split|desk|film, ...}, ...]   each runs to the next
  face   the presenter print is the hero. size: P (whole print, the default) | W | H | C | X | 0.42
         docs: [name | {doc, slot: br|bl|tr|tl|low}] small papers laid on the print
  doc    one document is the hero (doc: name). A page too tall to read whole: the camera follows
         each line as it is written (one zoom per paper, set by its widest line, so no line is
         ever cut off), then pulls back to the page. A card that fits: framed whole, revealing in
         place. A marker circle inside the shot is framed when nothing is being written.
         presenter: false drops the small print from the desk.
  split  the presenter print and one document together: stacked for wide paper, side by side
         for a receipt or sticky note.
  desk   overview: the presenter print and several documents (docs: [...]); a slow pull-out.
  film   a film print is the hero (film: name, window: [t0, t1] in the film's seconds).
Any shot: move: push | pull | drift | hold (default: alternates), snap: true (a 6-frame snap in on
the cut), punch: "C.w:bones" (snap 14% closer on that word), rot, board, light, surface, name.
Jump cuts: inside a face or split shot, every picture cut between two takes switches the framing
(alternately 13% closer and back), so no jump cut ever lands on a held frame. jumps: false turns
that off for a shot.

Defaults come from the plan: `treatment` (surface, light), `presenter` (face_frac, eye, res,
grade; face_frac is measured from the face track when it is not given). A document with no
appear/slap/drop arrives in the first shot that shows it (receipts and printouts drop in, other
paper slaps down). While the camera follows a line being written, captions of those words are
hidden (the paper already says them). The expansion is written to work/review/shots.yaml.
"""
import json, math
import numpy as np

from . import lives, materials, treatments
from .prep import load_ranges

LADDER = {"W": 0.35, "H": 0.50, "C": 0.67, "X": 0.95, "XX": 1.25}
NARROW = {"receipt", "sticky"}
SLOTS = {"br": (0.50, 0.40, 0.95, 0.66), "bl": (0.05, 0.40, 0.50, 0.66), "tr": (0.52, 0.07, 0.95, 0.30),
         "tl": (0.05, 0.07, 0.48, 0.30), "low": (0.08, 0.42, 0.92, 0.66)}
MOVES = ["push", "drift", "push", "pull"]


def _face_stats(plan):
    """Median face width in the source and the face_frac that uses the source's full width."""
    import sys
    from .plan import SCRIPTS
    sys.path.insert(0, str(SCRIPTS))
    from face_track import Track
    fws, src_w = [], None
    for r in load_ranges(plan):
        tr = Track.load(plan.wp("prep", f"track_{r}.json"))
        fw = tr.a[:, 2]; fws += list(fw[fw > 0]); src_w = tr.W
    med = float(np.median(fws)) if fws else 200.0
    return min(0.5, max(0.16, med / (0.94 * (src_w or 1080)))), med


def _docs_in(s):
    out = []
    if s.get("doc"):
        out.append(s["doc"])
    for d in s.get("docs", []):
        out.append(d if isinstance(d, str) else d["doc"])
    return out


class Ctx:
    def __init__(self, plan, meta, lv, k, t0, t1, ff, face_px):
        self.plan, self.meta, self.lv, self.k, self.t0, self.t1 = plan, meta, lv, k, t0, t1
        self.W, self.H, self.fps = plan.W, plan.H, plan.fps
        self.ff, self.face_px = ff, face_px
        self.sign = -1 if k % 2 else 1
        self.hide = []

    # ---- pieces
    def presenter(self, center, inner, rot):
        base = dict(self.plan.get("presenter", {})); k = self.k
        P = dict(center=[float(center[0]), float(center[1])], inner=[float(inner[0]), float(inner[1])], rot=float(rot),
                 face_frac=base.get("face_frac", round(self.ff, 3)), eye=base.get("eye", 0.30), res=base.get("res", 1.6),
                 border=base.get("border", 20), tapes=[[-1, k % 4, -38 + 3 * (k % 3)], [1, (k + 1) % 4, 36 - 4 * (k % 2)]])
        for key in ("grade", "x_offset"):
            if key in base:
                P[key] = base[key]
        return P

    def doc_h(self, name, width):
        m = self.meta["docs"][name]; return m["h"] * width / m["w"]

    def place(self, name, left, top, width, rot):
        kind = self.lv[name]["kind"]; surf = treatments.surface(self.plan)
        R = dict(left=float(left), top=float(top), width=float(width), rot=float(rot))
        if kind == "sticky":
            pass  # its own adhesive
        elif surf == "cork":
            R["pin"] = self.k % 3 if kind != "index" else 0
        else:
            R.update(tape=True, tape_index=(self.k + 1) % 4, tape_angle=3 * self.sign)
        return R

    def face_cam(self, P, size):
        """(cx, cy, z) framing the print's face at a ladder size (as Stage.target does)."""
        iw, ih = P["inner"]
        if size == "P":  # the whole print, above the caption band
            return self.fit_box(*self.rect(P), band=(0.05, 0.69))
        sz = LADDER.get(size, size) if isinstance(size, str) else float(size)
        up = sz * self.W / self.face_px
        if up > 2.3:  # a 720p face can't be blown up much past 2x before it goes soft
            sz *= 2.3 / up
            print(f"  [shots] shot {self.k}: size {size} would enlarge his face {up:.1f}x; holding it at 2.3x")
        z = sz * self.W / (P["face_frac"] * iw)
        th = math.radians(P["rot"]); fx = P.get("x_offset", 0.0) * iw; fy = -ih / 2 + P["eye"] * ih
        px = P["center"][0] + fx * math.cos(th) - fy * math.sin(th)
        py = P["center"][1] + fx * math.sin(th) + fy * math.cos(th)
        return px, py - (P["eye"] - 0.5) * self.H / z, z

    def rect(self, P, border=None):
        b = P.get("border", 20) if border is None else border
        w, h = P["inner"][0] + 2 * b, P["inner"][1] + 2 * b
        return P["center"][0] - w / 2, P["center"][1] - h / 2, P["center"][0] + w / 2, P["center"][1] + h / 2

    def doc_rect(self, R, name):
        return R["left"], R["top"], R["left"] + R["width"], R["top"] + self.doc_h(name, R["width"])

    def fit_box(self, x0, y0, x1, y1, band=(0.05, 0.69), margin=0.05):
        z = min((1 - 2 * margin) * self.W / (x1 - x0), (band[1] - band[0]) * self.H / (y1 - y0))
        return (x0 + x1) / 2, (y0 + y1) / 2 - ((band[0] + band[1]) / 2 - 0.5) * self.H / z, z

    @staticmethod
    def union(*rs):
        return min(r[0] for r in rs), min(r[1] for r in rs), max(r[2] for r in rs), max(r[3] for r in rs)

    def slot(self, cam, name, slot):
        cx, cy, z = cam; fx0, fy0, fx1, fy1 = SLOTS[slot]
        x0 = cx + (fx0 - 0.5) * self.W / z; x1 = cx + (fx1 - 0.5) * self.W / z
        y0 = cy + (fy0 - 0.5) * self.H / z; y1 = cy + (fy1 - 0.5) * self.H / z
        m = self.meta["docs"][name]
        width = min((x1 - x0) * 0.9, (y1 - y0) * m["w"] / m["h"])
        return self.place(name, (x0 + x1) / 2 - width / 2, y0, width, 2.5 * self.sign)

    # ---- camera
    def key(self, t, c, ease=None, **mods):
        tg = {"center": [round(c[0], 1), round(c[1], 1)], "zoom": round(c[2], 4)}
        tg.update(mods)
        return [round(t, 4), tg] + ([ease] if ease else [])

    def moved(self, c, move, end=True):
        cx, cy, z = c
        if not end or move == "hold":
            return c
        if move == "push":
            return cx, cy, z * 1.04
        if move == "pull":
            return cx, cy, z / 1.05
        return cx - 16 * self.sign / z, cy - 6 / z, z * 1.02  # drift

    def hold_keys(self, c, s, default):
        """Keys for a held framing: snap in, punch on a word, then the move to the end of the shot."""
        move = s.get("move", default); t0, t1, f = self.t0, self.t1, 1.0 / self.fps
        start = (c[0], c[1], c[2] * 1.05) if move == "pull" else c
        keys = []
        if s.get("snap"):
            keys += [self.key(t0, (c[0], c[1], start[2] * 0.93)), self.key(t0 + 6 * f, start, "oexp")]
        else:
            keys.append(self.key(t0, start))
        end = self.moved(c, move)
        if s.get("punch"):
            tp = self.plan_t(s["punch"])
            u = (tp - t0) / max(1e-3, t1 - t0)
            mid = tuple(start[i] + (end[i] - start[i]) * u for i in range(3))
            keys.append(self.key(tp - f, mid, "io2"))
            keys.append(self.key(tp + 5 * f, (mid[0], mid[1], mid[2] * 1.14), "oexp"))
            end = (end[0], end[1], end[2] * 1.16)
        keys.append(self.key(t1, end, "io2"))
        return keys

    def plan_t(self, expr):
        return self.tl.t(expr)


# ---------------------------------------------------------------- templates

def t_face(c, s):
    rot = s.get("rot", 1.1 * c.sign)
    P = c.presenter((540, 900), (880, 1320), rot)
    lay = {"presenter": P}
    cam = c.face_cam(P, s.get("size", "P"))
    if s.get("docs"):
        lay["documents"] = {}
        for k, d in enumerate(s["docs"]):
            name, slot = (d, ["br", "bl", "tr"][k % 3]) if isinstance(d, str) else (d["doc"], d.get("slot", "br"))
            lay["documents"][name] = c.slot(cam, name, slot)
    return lay, c.hold_keys(cam, s, MOVES[c.k % len(MOVES)])


def t_doc(c, s):
    name = s["doc"]; kind = c.lv[name]["kind"]; m = c.meta["docs"][name]
    width = {"sticky": 560, "receipt": 640}.get(kind, 900)
    R = c.place(name, 540 - width / 2 + 12 * c.sign, 300, width, s.get("rot", 1.2 * c.sign))
    lay = {"documents": {name: R}}
    if s.get("presenter", True):
        lay["presenter"] = c.presenter((215, 250), (320, 430), -4 * c.sign)
    page = c.fit_box(*c.doc_rect(R, name), band=(0.06, 0.69))
    life = c.lv[name]; sc = width / m["w"]; L = m["lines"]
    cues = sorted((t0, t1, i) for i, (t0, t1, _) in life["cues"].items() if c.t0 - 0.05 <= t0 < c.t1)
    spans = []
    for t0, t1, i in cues:  # the paper says these words: no captions over them
        span = c.tl.phrase(L[i].get("text", ""), t0 - 0.4) if L[i].get("text") else None
        a, b = (min(t0, span[0]), max(t1, span[1])) if span and span[0] < t1 + 0.6 else (t0, t1)
        a, b = a - 0.05, min(b + 0.1, c.t1)
        if spans and a - spans[-1][1] < 1.5:  # a few words between two written lines: hide them too
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    c.hide += [[round(a, 3), round(b, 3)] for a, b in spans]
    texts = [x for x in L if x.get("text") or x["wave"]]
    ux0 = min(x["x0"] for x in texts); ux1 = max(x["x1"] for x in texts)  # the widest line sets one zoom per paper
    z = min(2.3, max(1.0, 0.84 * c.W / ((ux1 - ux0) * sc)))
    th = math.radians(R["rot"]); xc = R["left"] + width / 2
    if c.doc_h(name, width) * z <= 0.6 * c.H or not cues:  # it reads whole: frame the paper
        mk = life.get("marker")
        if not cues and mk and c.t0 <= mk[0] < c.t1:  # the marker circle is the event: frame its lines
            a, b = mk[2]; d = (L[a]["y"] + L[b]["y"] + L[b]["h"]) / 2 * sc
            px, py = xc - d * math.sin(th), R["top"] + d * math.cos(th)
            zm = z
            cam = (px + ((ux0 + ux1) / 2 - m["w"] / 2) * sc, py - (0.42 - 0.5) * c.H / zm, zm)
            return lay, c.hold_keys(cam, s, "push")
        # close on the writing: the text block at reading size, the paper's edges may leave the frame
        d = c.doc_h(name, width) / 2; dx = ((ux0 + ux1) / 2 - m["w"] / 2) * sc
        px = xc - d * math.sin(th) + dx * math.cos(th); py = R["top"] + d * math.cos(th) + dx * math.sin(th)
        zc = max(page[2], z) if c.doc_h(name, width) * z <= 0.6 * c.H else page[2]
        base = (px, py - (0.41 - 0.5) * c.H / zc, zc)
        if len(cues) < 2:
            return lay, c.hold_keys(base, s, "push")
        keys, f = [c.key(c.t0, base)], 1.0 / c.fps  # follow the typewriter: a move onto each line as it starts
        for n, (t0, t1, i) in enumerate(cues):
            zn = min(zc * (1.06 + 0.05 * n), 0.94 * c.W / ((ux1 - ux0) * sc), 2.4)  # every line stays whole
            dl = (L[i]["y"] + L[i]["h"] / 2) * sc; dx = ((ux0 + ux1) / 2 - m["w"] / 2) * sc
            lx = xc - dl * math.sin(th) + dx * math.cos(th); ly = R["top"] + dl * math.cos(th) + dx * math.sin(th)
            tgt = (lx, ly - (0.42 - 0.5) * c.H / zn, zn)
            if n == 0 and t0 - c.t0 < 0.3:
                keys = [c.key(c.t0, tgt)]
                continue
            prev = keys[-1][1]
            keys += [c.key(max(keys[-1][0] + f, t0 - 0.06), (prev["center"][0], prev["center"][1], prev["zoom"] * 1.008), "io2"),
                     c.key(t0 + 0.26, tgt, "io3")]
        end = max(t1 for _, t1, _ in cues)
        last = keys[-1][1]
        if c.t1 - end > 1.0:  # the whole card, once it is typed
            keys += [c.key(end + 0.2, (last["center"][0], last["center"][1], last["zoom"] * 1.01), "io2"),
                     c.key(end + 0.75, base, "io3"), c.key(c.t1, c.moved(base, "push"), "io2")]
        else:
            keys.append(c.key(c.t1, (last["center"][0], last["center"][1], last["zoom"] * 1.02), "io2"))
        keys.sort(key=lambda k: k[0])
        return lay, keys

    def line_cam(i):
        d = (L[i]["y"] + L[i]["h"] / 2) * sc; dx = ((ux0 + ux1) / 2 - m["w"] / 2) * sc
        px = xc - d * math.sin(th) + dx * math.cos(th); py = R["top"] + d * math.cos(th) + dx * math.sin(th)
        return px, py - (0.40 - 0.5) * c.H / z, z

    f = 1.0 / c.fps; keys = []
    first_t = cues[0][0]
    if first_t - c.t0 > 0.9:  # the page first, then into the writing
        keys += [c.key(c.t0, page), c.key(first_t - 0.35, c.moved(page, "push")), c.key(first_t - 0.02, line_cam(cues[0][2]), "io3")]
    else:
        keys.append(c.key(c.t0, line_cam(cues[0][2])))
    prev = line_cam(cues[0][2])
    for (t0, t1, i) in cues[1:]:
        cur = line_cam(i)
        if abs(cur[1] - prev[1]) > 1:
            keys += [c.key(max(keys[-1][0] + f, t0 - 0.14), (prev[0], prev[1] - 4 / z, prev[2] * 1.01), "io2"),
                     c.key(t0 + 0.22, cur, "io3")]
        prev = cur
    last_end = max(t1 for _, t1, _ in cues)
    if c.t1 - last_end > 1.3:  # pull back to the whole page
        keys += [c.key(last_end + 0.25, (prev[0], prev[1] - 4 / z, prev[2] * 1.01), "io2"),
                 c.key(min(c.t1, last_end + 0.95), page, "io3"), c.key(c.t1, c.moved(page, "push"), "io2")]
    else:
        keys.append(c.key(c.t1, (prev[0], prev[1] - 6 / z, prev[2] * 1.02), "io2"))
    keys.sort(key=lambda k: k[0])
    return lay, keys


def t_split(c, s):
    name = s["doc"]; kind = c.lv[name]["kind"]
    if kind in NARROW:  # side by side
        P = c.presenter((335, 760), (560, 840), -1.6 * c.sign)
        R = c.place(name, 660, 300, 380, 0.8 * c.sign)
    else:  # stacked: the page laid over the bottom of the print
        P = c.presenter((540, 600), (720, 880), -1.4 * c.sign)
        R = c.place(name, 120 + 10 * c.sign, 960, 840, 1.6 * c.sign)
    lay = {"presenter": P, "documents": {name: R}}
    x0, y0, x1, y1 = c.union(c.rect(P), c.doc_rect(R, name))
    if kind not in NARROW:  # frame the print and the top of the page, not the whole sheet
        m = c.meta["docs"][name]; sc = R["width"] / m["w"]
        cued = [i for i, (t0, _, _) in c.lv[name]["cues"].items() if t0 < c.t1]
        last = max(cued) if cued else min(2, len(m["lines"]) - 1)
        y1 = min(y1, R["top"] + (m["lines"][last]["y"] + m["lines"][last]["h"]) * sc + 60)
    cam = c.fit_box(x0, y0, x1, y1, band=(0.04, 0.69))
    return lay, c.hold_keys(cam, s, "push")


def t_desk(c, s):
    P = c.presenter((360, 620), (520, 700), -2.0 * c.sign)
    lay = {"presenter": P, "documents": {}}
    cells = [(620, 120, 1040, 820), (40, 1000, 520, 1640), (560, 900, 1040, 1600), (600, 560, 940, 980)]
    rects = [c.rect(P)]
    for k, name in enumerate(_docs_in(s)):
        x0, y0, x1, y1 = cells[k % len(cells)]; m = c.meta["docs"][name]
        width = min((x1 - x0) * 0.92, (y1 - y0) * m["w"] / m["h"])
        R = c.place(name, (x0 + x1) / 2 - width / 2, y0, width, (2.5 if k % 2 else -2.0) * c.sign)
        lay["documents"][name] = R; rects.append(c.doc_rect(R, name))
    cam = c.fit_box(*c.union(*rects), band=(0.04, 0.69))
    return lay, c.hold_keys(cam, s, "pull")


def t_film(c, s):
    f = c.plan["films"][s["film"]]
    fw, fh = f.get("scale") or (16, 9)
    try:  # the prepared film's real shape (his own clips are often 9:16)
        import cv2
        cap = cv2.VideoCapture(str(c.plan.wp("prep", f"film_{s['film']}.mov")))
        if cap.isOpened() and cap.get(cv2.CAP_PROP_FRAME_WIDTH):
            fw, fh = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        cap.release()
    except Exception:
        pass
    iw = 900.0 if fh / fw <= 1.2 else 900.0 * 1.05 / (fh / fw)  # a tall clip: narrower, so it fits above the captions
    ih = iw * fh / fw
    F = dict(film=s["film"], window=s.get("window", [f["from"], f["to"]]), appear=c.t0 + 0.12, center=[540, 760],
             inner=[iw, round(ih)], rot=1.2 * c.sign, res=1.3, border=18, tapes=[[-1, c.k % 4, -36], [1, (c.k + 2) % 4, 40]])
    lay = {"films": [F]}
    if s.get("presenter", True):
        lay["presenter"] = c.presenter((830, 760 + ih / 2 + 220), (330, 440), 3.0 * c.sign)
    cam = c.fit_box(540 - iw / 2 - 18, 760 - ih / 2 - 18, 540 + iw / 2 + 18, 760 + ih / 2 + 18, band=(0.06, 0.66))
    return lay, c.hold_keys(cam, s, "push")


TEMPLATES = {"face": t_face, "doc": t_doc, "split": t_split, "desk": t_desk, "film": t_film}
JUMP_SHOTS = {"face", "split"}


def _jumps(tl):
    """Edit times where the presenter's picture jumps (consecutive takes not contiguous in the source)."""
    segs = tl.edl["segments"]; f = 1.0 / tl.fps; out = []
    for s, n in zip(segs, segs[1:]):
        before = s["src_in"] + (s["p_out"] - s["edit_in"]); after = n["src_in"] + (n["p_in"] - n["edit_in"])
        if s["range"] != n["range"] or abs(after - before) > 1.5 * f:
            out.append(s["p_out"])
    return out


def _frame_at(keys, t):
    from .stage import EASE, seg
    if t <= keys[0][0]:
        c = keys[0][1]; return c["center"][0], c["center"][1], c["zoom"]
    for (t0, c0, *_), (t1, c1, *e) in zip(keys, keys[1:]):
        if t <= t1:
            u = (EASE[e[0]] if e else EASE["io2"])(seg(t, t0, t1))
            return (c0["center"][0] + (c1["center"][0] - c0["center"][0]) * u,
                    c0["center"][1] + (c1["center"][1] - c0["center"][1]) * u,
                    math.exp(math.log(c0["zoom"]) + (math.log(c1["zoom"]) - math.log(c0["zoom"])) * u))
    c = keys[-1][1]; return c["center"][0], c["center"][1], c["zoom"]


def _clip(c, keys, a, b, factor):
    """The shot's camera between a and b, every key's zoom times factor."""
    out = [c.key(a, _frame_at(keys, a))] + [k for k in keys if a < k[0] < b] + [c.key(b, _frame_at(keys, b), "io2")]
    out = json.loads(json.dumps(out))
    for k in out:
        k[1]["zoom"] = round(k[1]["zoom"] * factor, 4)
    return out


# ---------------------------------------------------------------- expansion

def expand(plan, tl, meta):
    """Fill plan layouts/beats/caption hides from plan["shots"]; returns the document lives."""
    shots = plan.get("shots") or []
    if not shots:
        return lives.resolve(plan, tl, meta)
    times = [tl.t(s["at"]) for s in shots] + [tl.total]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise SystemExit(f"shots must run forward in time: {[round(t, 2) for t in times]}")
    # papers arrive in the first shot that shows them, unless the plan says when
    first = {}
    for k, s in enumerate(shots):
        for name in _docs_in(s):
            first.setdefault(name, times[k])
    pool = {**(plan.get("receipts") or {}), **(plan.get("documents") or {})}
    for name, t0 in first.items():
        if name not in pool:
            raise SystemExit(f"shot uses unknown document {name!r}")
        r = pool[name]; kind = r.get("kind") or ("receipt" if name in (plan.get("receipts") or {}) else treatments.default_kind(plan))
        if not any(x in r for x in ("appear", "slap", "drop")):
            if kind in ("receipt", "printout"):
                r["drop"] = [round(t0 + 0.05, 4), round(t0 + 0.37, 4), 900]; r.setdefault("tape_at", round(t0 + 0.37, 4))
            else:
                r["slap"] = round(t0 + 0.2, 4)
    lv = lives.resolve(plan, tl, meta)
    ff, face_px = _face_stats(plan)
    layouts = plan.setdefault("layouts", {}); beats = plan.setdefault("beats", [])
    hide = plan["captions"].setdefault("hide", [])
    base_light = treatments.light(plan)
    jumps = _jumps(tl)
    for k, s in enumerate(shots):
        c = Ctx(plan, meta, lv, k, times[k], times[k + 1], ff, face_px); c.tl = tl
        if s["shot"] not in TEMPLATES:
            raise SystemExit(f"shot {k}: unknown template {s['shot']!r}; one of {sorted(TEMPLATES)}")
        lay, cam = TEMPLATES[s["shot"]](c, s)
        lay["board"] = s.get("board", [400 + (k * 370) % 1300, 500 + (k * 530) % 1600])
        lx, ly, sig, lo, hi = s.get("light", base_light)
        lay["light"] = [lx + 60 * ((k % 3) - 1), ly, sig, lo, hi]
        if s.get("surface"):
            lay["surface"] = s["surface"]
        name = f"s{k:02d}_{s['shot']}"
        layouts[name] = lay
        t0, t1 = times[k], times[k + 1]
        cuts = [x for x in jumps if t0 + 0.25 < x < t1 - 0.25] if s["shot"] in JUMP_SHOTS and s.get("jumps", True) else []
        edges = [t0] + cuts + [t1]
        for j, (a, b) in enumerate(zip(edges, edges[1:])):  # a jump cut is a new framing, never a held one
            beats.append({"name": s.get("name", name) + (f"~{j}" if j else ""), "layout": name, "from": round(a, 4),
                          "to": round(b, 4), "camera": cam if len(edges) == 2 else _clip(c, cam, a, b, 1.13 if j % 2 else 1.0)})
        hide += c.hide
    try:
        import yaml
        dump = {"layouts": {k: v for k, v in layouts.items() if k.startswith("s") and "_" in k}, "beats": beats,
                "caption_hide": hide}
        plan.wp("review", "shots.yaml").write_text(yaml.safe_dump(json.loads(json.dumps(dump)), sort_keys=False, width=140))
    except Exception as e:  # inspection only
        print("  [shots] could not write shots.yaml:", e)
    return lv


def prepare(plan, tl=None):
    """Materials, shot expansion and document lives, once per process: (timeline, meta, lives)."""
    if getattr(plan, "_prepared", None):
        return plan._prepared
    from .timeline import Timeline
    tl = tl or Timeline(plan)
    meta = materials.build(plan)
    lv = expand(plan, tl, meta)
    plan._prepared = (tl, meta, lv)
    return plan._prepared
