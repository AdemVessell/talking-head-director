"""Paper documents, one kind per subject family. The receipt is one kind among many:
choose the document the video's subject would really produce (treatments.py).

  receipt    thermal till roll        money, costs, usage, prices
  card       spec / lab card, holed   products, gear, tests, measurements
  note       lined notebook page      ideas, lyrics, plans, personal thoughts (handwritten)
  sticky     sticky note              tips, asides, reminders (marker)
  clipping   newsprint, torn          opinions, claims, industry talk (his words as headlines; a real headline
                                      only verbatim with a "via OUTLET" line; never a masthead or logo)
  blueprint  drafting blue            how it works, builds, systems, architecture
  printout   tractor-feed printout    tech, AI, code, logs, prompts
  index      index card               definitions, steps, section titles
  staff      music manuscript         melody, music theory (staves, notes, lyric under each)
  screenshot photo print of a REAL     news: the headline, post or page he is reacting to
             screenshot               (`image:`, `crop:`, `source:`; see screenshot())

Line specs (one string per line):
  "l:TEXT" "c:TEXT" "r:TEXT"   body text, aligned        "h:TEXT" "h:c:TEXT"   headline
  "D:r:TEXT" "D:c:TEXT"        big value                 "x:TEXT"   struck through (red, its own cue)
  "q:TEXT"   quote             "check:TEXT" "done:TEXT"  box, or box with a red tick (own cue)
  "n:3:TEXT" numbered step     "bar:LABEL:VALUE:FRACTION"  measurement bar (red fill, own cue)
  "box:A|B|C" boxes + arrows   "rule" "rule2" "gap"      "WAVE:t0:t1" real waveform of source seconds
Every line is two layers: ink (the kind's pen or print head) and accent (vermilion marks:
strike, tick, bar fill), so each can be revealed on its own word. Meta per line carries the
ink extent and each character's right edge, for typewriter and handwriting reveals.
"""
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .texture import fbm, paper_tex

from . import fonts as _fonts
FONTS = _fonts.TABLE   # name -> (path, index), resolved per machine (fonts.py)
VERMILION = (226, 69, 43)

KINDS = {
    "receipt": dict(w=860, mx=46, paper=(244, 242, 236), grain=0.012, fibres=0.03, body="courier", size=64, lh=82,
                    head="courier", head_size=96, dsize=128, dlh=156, ink=(50, 48, 45), edge="teeth", deco=None,
                    reveal="ink", top=78, bottom=66, creases=3, mono_rules=True, gap=82),
    "card": dict(w=900, mx=64, paper=(241, 234, 215), grain=0.016, fibres=0.05, body="typewriter", size=50, lh=74,
                 head="rockwell", head_size=88, dsize=110, dlh=140, ink=(36, 33, 30), edge="round_hole", deco="card",
                 reveal="type", top=150, bottom=80, creases=1),
    "note": dict(w=900, mx=120, paper=(248, 246, 239), grain=0.01, fibres=0.02, body="hand", size=62, lh=92,
                 head="hand", head_size=96, dsize=104, dlh=132, ink=(30, 52, 118), edge="spiral", deco="ruled",
                 reveal="write", top=150, bottom=90, baseline=0.74, creases=2, tilt=0.5),
    "sticky": dict(w=600, mx=48, paper=(249, 226, 98), grain=0.02, fibres=0.02, body="marker", size=58, lh=80,
                   head="marker", head_size=80, dsize=96, dlh=120, ink=(30, 28, 26), edge="straight", deco="sticky",
                   reveal="write", top=78, bottom=60, min_h=600, creases=0, tilt=0.7),
    "clipping": dict(w=920, mx=56, paper=(234, 228, 208), grain=0.022, fibres=0.04, body="georgia", size=44, lh=62,
                     head="didot", head_size=104, dsize=110, dlh=132, ink=(26, 24, 22), edge="torn", deco="newsprint",
                     reveal="ink", top=70, bottom=70, creases=2),
    "blueprint": dict(w=920, mx=60, paper=(32, 66, 120), grain=0.02, fibres=0.0, body="menlo", size=44, lh=68,
                      head="futura", head_size=92, dsize=100, dlh=128, ink=(236, 242, 250), edge="straight", deco="grid",
                      reveal="draw", top=80, bottom=80, creases=1),
    "printout": dict(w=940, mx=92, paper=(243, 245, 237), grain=0.012, fibres=0.02, body="menlo", size=40, lh=62,
                     head="menlo_bold", head_size=64, dsize=84, dlh=104, ink=(54, 54, 60), edge="tractor", deco="greenbar",
                     reveal="print", top=62, bottom=62, creases=1, mono_rules=True),
    "index": dict(w=900, mx=56, paper=(247, 244, 236), grain=0.012, fibres=0.03, body="typewriter", size=50, lh=76,
                  head="didot", head_size=88, dsize=110, dlh=136, ink=(34, 31, 28), edge="straight", deco="index",
                  reveal="type", top=60, bottom=60, baseline=0.76, creases=1),
    "staff": dict(w=920, mx=64, paper=(242, 236, 221), grain=0.014, fibres=0.03, body="hand", size=54, lh=150,
                  head="hand", head_size=92, dsize=100, dlh=130, ink=(30, 30, 36), edge="straight", deco="staff",
                  reveal="write", top=90, bottom=70, dy=30, creases=1, tilt=0.4),
    "screenshot": dict(w=1000, mx=40, paper=(246, 244, 240), grain=0.008, fibres=0.01, body="typewriter", size=40, lh=64,
                       head="typewriter_bold", head_size=48, dsize=48, dlh=64, ink=(46, 44, 40), edge="straight",
                       deco=None, reveal="ink", top=40, bottom=40, creases=0),
}
HANDWRITTEN = {"note", "sticky", "staff"}
_F = {}


def font(name, size):
    k = (name, int(size))
    if k not in _F:
        path, idx = FONTS[name]
        _F[k] = ImageFont.truetype(path, int(size), index=idx)
    return _F[k]


def line_height(K, spec):
    if spec.startswith("WAVE:"):
        h = 170
    elif spec.startswith("D:"):
        h = K["dlh"]
    elif spec.startswith("h:"):
        h = int(K["head_size"] * 1.3)
    elif spec.startswith("box:"):
        h = int(max(K["lh"], 70) * 1.9)
    elif spec == "gap":
        h = K.get("gap", K["lh"] // 2)
    else:
        h = K["lh"]
    if K.get("baseline"):  # ruled paper: every line box is a whole number of rules
        h = int(math.ceil(h / K["lh"]) * K["lh"])
    return h


class _Off:
    """ImageDraw with every y shifted down by `oy`: a line is drawn in the middle of a taller canvas
    so descenders, tails and accents may leave their line box, as handwriting does."""
    def __init__(self, d, oy):
        self.d, self.oy = d, oy

    def textlength(self, *a, **k):
        return self.d.textlength(*a, **k)

    def text(self, xy, *a, **k):
        return self.d.text((xy[0], xy[1] + self.oy), *a, **k)

    def _pts(self, pts):
        return [(x, y + self.oy) for x, y in pts]

    def line(self, pts, *a, **k):
        return self.d.line(self._pts(pts), *a, **k)

    def polygon(self, pts, *a, **k):
        return self.d.polygon(self._pts(pts), *a, **k)

    def rectangle(self, box, *a, **k):
        x0, y0, x1, y1 = box
        return self.d.rectangle([x0, y0 + self.oy, x1, y1 + self.oy], *a, **k)

    def ellipse(self, box, *a, **k):
        x0, y0, x1, y1 = box
        return self.d.ellipse([x0, y0 + self.oy, x1, y1 + self.oy], *a, **k)


def _text_layer(K, kind, spec, lh, rng):
    """Ink and accent alpha (float 0..1) for one line on a canvas `pad` taller above and below, plus
    {text, xs, pad}."""
    W, mx = K["w"], K["mx"]
    pad = int(max(K["size"], K["head_size"], K["dsize"]) * 0.6)
    im = Image.new("L", (W, lh + 2 * pad), 0); d = _Off(ImageDraw.Draw(im), pad)
    acc = Image.new("L", (W, lh + 2 * pad), 0); da = _Off(ImageDraw.Draw(acc), pad)
    info = {"text": "", "xs": [], "pad": pad}

    def ytop(f, dy=0):
        if K.get("baseline"):  # sit on the rule (a hand touches it; type clears it)
            return lh - (1 - K["baseline"]) * K["lh"] - f.getmetrics()[0] + (4 if kind in HANDWRITTEN else -4)
        return (lh - f.size) / 2 - 6 + dy

    def put(txt, fname, size, al="l", x0=None, main=True, room=None, dy=0):
        f = font(fname, size); tw = d.textlength(txt, font=f)
        room = room or (W - 2 * mx - (x0 - mx if x0 is not None else 0))
        if tw > room:  # too long for the paper: shrink this line rather than run off the edge
            print(f"  [documents] {kind}: '{txt}' is {tw / room:.0%} of the line; shrinking it")
            f = font(fname, size * room / tw * 0.98); tw = d.textlength(txt, font=f)
        tx = x0 if x0 is not None else (mx if al == "l" else (W - mx - tw if al == "r" else (W - tw) / 2))
        ty = ytop(f, dy)
        d.text((tx, ty), txt, font=f, fill=255)
        if main:
            info["text"] = txt
            info["xs"] = [round(tx + d.textlength(txt[:k + 1], font=f), 1) for k in range(len(txt))]
        return tx, tw, ty, f

    body, size = K["body"], K["size"]
    if spec in ("rule", "rule2"):
        if K.get("mono_rules"):
            f = font(body, size); n = int((W - 2 * mx) / d.textlength("-", font=f))
            d.text((mx, ytop(f) + 2), ("-" if spec == "rule" else "=") * n, font=f, fill=255)
        else:
            y = lh // 2
            d.line([(mx, y), (W - mx, y)], fill=210, width=3)
            if spec == "rule2":
                d.line([(mx, y + 8), (W - mx, y + 8)], fill=210, width=3)
    elif spec == "gap":
        pass
    elif spec.startswith("h:"):
        rest = spec[2:]; al = "l"
        if rest[:2] in ("c:", "r:", "l:"):
            al, rest = rest[0], rest[2:]
        put(rest, K["head"], K["head_size"], al)
    elif spec.startswith("D:"):
        _, al, txt = spec.split(":", 2)
        put(txt, body if kind == "receipt" else K["head"], K["dsize"], al)
    elif spec.startswith("x:"):
        tx, tw, ty, f = put(spec[2:], body, size)
        y = ty + f.size * 0.62
        pts = [(tx - 10 + k * (tw + 20) / 12, y + rng.normal(0, 2.4)) for k in range(13)]
        da.line(pts, fill=255, width=max(5, int(size * 0.12)), joint="curve")
    elif spec.startswith("q:"):
        fq = "georgia_italic" if body in ("georgia", "typewriter") else body
        put("“" + spec[2:] + "”", fq, size * 1.06)
    elif spec.startswith(("check:", "done:")):
        done = spec.startswith("done:"); txt = spec.split(":", 1)[1]
        f = font(body, size); ty = ytop(f); s = int(size * 0.7); y0 = int(ty + size * 0.2)
        d.rectangle([mx, y0, mx + s, y0 + s], outline=255, width=max(3, size // 14))
        if done:
            da.line([(mx + 5, y0 + s * 0.5), (mx + s * 0.42, y0 + s - 4), (mx + s + 12, y0 - 14)], fill=255,
                    width=max(6, size // 7), joint="curve")
        put(txt, body, size, x0=mx + s + 28)
    elif spec.startswith("n:"):
        _, num, txt = spec.split(":", 2)
        f = font(body, size); ty = ytop(f); r = int(size * 0.5); cx, cy = mx + r, int(ty + size * 0.56)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=255, width=max(3, size // 14))
        nf = font(K["head"], r * 1.25); nw = d.textlength(num, font=nf)
        d.text((cx - nw / 2, cy - nf.getmetrics()[0] * 0.62), num, font=nf, fill=255)
        put(txt, body, size, x0=mx + 2 * r + 26)
    elif spec.startswith("bar:"):
        _, label, value, frac = spec.split(":", 3)
        frac = max(0.0, min(1.0, float(frac))); ls = size * 0.82
        put(label, body, ls, "l", room=(W - 2 * mx) * 0.34)
        f = font(body, ls); vw = d.textlength(value, font=f); put(value, body, ls, "r", main=False)
        ty = ytop(f); cy = ty + ls * 0.56
        x0 = mx + int((W - 2 * mx) * 0.37); x1 = int(W - mx - vw - 24); y0, y1 = int(cy - 14), int(cy + 14)
        d.rectangle([x0, y0, x1, y1], outline=255, width=3)
        da.rectangle([x0 + 6, y0 + 6, x0 + 6 + int((x1 - x0 - 12) * frac), y1 - 6], fill=255)
    elif spec.startswith("box:"):
        items = spec[4:].split("|"); n = len(items)
        gap = 70; bw = (W - 2 * mx - gap * (n - 1)) / n; y0, y1 = int(lh * 0.16), int(lh * 0.84)
        for k, it in enumerate(items):
            x0 = mx + k * (bw + gap)
            d.rectangle([x0, y0, x0 + bw, y1], outline=255, width=4)
            bf = font(body, size * 0.8); tw = d.textlength(it, font=bf)
            if tw > bw - 20:
                bf = font(body, size * 0.8 * (bw - 20) / tw); tw = d.textlength(it, font=bf)
            d.text((x0 + (bw - tw) / 2, (lh - bf.size) / 2 - 6), it, font=bf, fill=255)
            if k < n - 1:
                ax = x0 + bw + 10; ay = lh / 2
                d.line([(ax, ay), (ax + gap - 22, ay)], fill=255, width=4)
                d.polygon([(ax + gap - 24, ay - 11), (ax + gap - 6, ay), (ax + gap - 24, ay + 11)], fill=255)
        info["text"] = " ".join(items)
    else:
        al, txt = (spec[0], spec[2:]) if spec[:2] in ("l:", "c:", "r:") else ("l", spec)
        tx, tw, ty, f = put(txt, body, size, al, dy=K.get("dy", 0))  # staff: the lyric sits under its staff
        if kind == "staff" and txt.strip():  # the melody, sketched on the staff above its lyric
            for k in range(int(rng.integers(5, 9))):
                x = mx + 50 + (W - 2 * mx - 100) * (k + rng.uniform(0.2, 0.8)) / 8
                step = int(rng.integers(0, 9)); y = 12 + step * 5.5
                d.ellipse([x - 9, y - 6, x + 9, y + 6], fill=255)
                if step <= 4:
                    d.line([(x - 8, y), (x - 8, y + 32)], fill=255, width=3)
                else:
                    d.line([(x + 8, y), (x + 8, y - 32)], fill=255, width=3)
    return np.asarray(im, np.float32) / 255, np.asarray(acc, np.float32) / 255, info


def _wave(audio, sr, t0, t1, ref, K, h):
    seg = audio[int(t0 * sr):int(t1 * sr)]; W, mx = K["w"], K["mx"]
    width = W - 2 * mx
    cols = np.array_split(seg, width)
    hi = np.array([c.max() if len(c) else 0 for c in cols]) / ref
    lo = np.array([c.min() if len(c) else 0 for c in cols]) / ref
    im = Image.new("L", (W, h), 0); d = ImageDraw.Draw(im)
    mid = h / 2; amp = h * 0.46
    d.line([(mx, mid), (W - mx, mid)], fill=90, width=2)
    for k in range(0, width, max(1, width // 20)):
        d.line([(mx + k, h - 10), (mx + k, h - 4)], fill=120, width=2)
    for i in range(width):
        d.line([(mx + i, mid - max(hi[i], 0.004) * amp), (mx + i, mid - min(lo[i], -0.004) * amp)], fill=255, width=1)
    return np.asarray(im, np.float32) / 255


def _edges(K, h, rng, seed):
    W = K["w"]; a = np.ones((h, W), np.float32); e = K["edge"]
    if e == "teeth":
        ys = h - 24
        for xi in range(W):  # serrated tear-off bottom edge
            ph = (xi % 36) / 36.0
            a[int(ys + 24 * (1 - abs(ph * 2 - 1)) + rng.normal(0, 1.2)):, xi] = 0
    elif e == "round_hole":
        r = 30; yy, xx = np.mgrid[0:h, 0:W]
        for cx, cy in ((r, r), (W - r, r), (r, h - r), (W - r, h - r)):
            corner = ((xx < r) if cx == r else (xx > W - r)) & ((yy < r) if cy == r else (yy > h - r))
            a[corner & ((xx - cx) ** 2 + (yy - cy) ** 2 > r * r)] = 0
        cv2.circle(a, (W // 2, 70), 19, 0.0, -1, cv2.LINE_AA)
    elif e == "spiral":  # torn out of a spiral notebook: punched holes and a ragged top
        jag = (np.abs(fbm(1, W, seed + 3, 5, 40)[0]) * 10 + 3).astype(int)
        for x in range(W):
            a[:jag[x], x] = 0
        for x in range(40, W - 20, 46):
            cv2.circle(a, (x, 44), 11, 0.0, -1, cv2.LINE_AA)
            if rng.random() < 0.35:  # some holes tore through to the edge
                cv2.rectangle(a, (x - 7, 0), (x + 7, 44), 0.0, -1)
    elif e == "torn":
        L = max(W, h)
        prof = [(np.abs(fbm(1, L, seed + 5 + k, 5, 30)[0]) * 20 + 3).astype(int) for k in range(4)]
        for x in range(W):
            a[:prof[0][x], x] = 0; a[h - prof[1][x]:, x] = 0
        for y in range(h):
            a[y, :prof[2][y]] = 0; a[y, W - prof[3][y]:] = 0
    elif e == "tractor":
        for y in range(31, h - 10, 50):
            for x in (36, W - 36):
                cv2.circle(a, (x, y), 10, 0.0, -1, cv2.LINE_AA)
    return cv2.GaussianBlur(a, (0, 0), 0.7)


def _deco(K, kind, pap, metas, h):
    """Printed furniture of the paper (rules, grid, bands), under the ink."""
    W, mx = K["w"], K["mx"]; dec = K["deco"]
    lay = np.zeros((h, W, 3), np.float32); amt = np.zeros((h, W), np.float32)

    def stroke(draw, color, alpha):
        sub = np.zeros((h, W), np.float32); draw(sub)
        a = sub * alpha
        lay[:] = lay * (1 - a[..., None]) + np.array(color, np.float32) * a[..., None]
        amt[:] = np.maximum(amt, a)

    if dec in ("ruled", "index"):
        b, lh = K["baseline"], K["lh"]; top = K["top"]
        first = 0
        if dec == "index" and metas and metas[0]["spec"].startswith("h:"):
            first = metas[0]["h"] // lh - 1  # the red rule sits under the title
        n = -1 if dec == "ruled" else first
        while True:
            y = int(top + (n + b) * lh + 2)
            if y > h - 40:
                break
            if y > 70:
                red = dec == "index" and n == first
                stroke(lambda s, y=y: cv2.line(s, (0, y), (W, y), 1.0, 3 if red else 2, cv2.LINE_AA),
                       (205, 72, 64) if red else (118, 150, 206), 0.75 if red else 0.5)
            n += 1
        if dec == "ruled":
            stroke(lambda s: cv2.line(s, (mx - 26, 0), (mx - 26, h), 1.0, 2, cv2.LINE_AA), (206, 86, 86), 0.55)
    elif dec == "grid":
        for k in range(0, max(W, h), 40):
            stroke(lambda s, k=k: (cv2.line(s, (k, 0), (k, h), 1.0, 1, cv2.LINE_AA), cv2.line(s, (0, k), (W, k), 1.0, 1, cv2.LINE_AA)),
                   (210, 226, 245), 0.22 if k % 200 == 0 else 0.1)
        stroke(lambda s: cv2.rectangle(s, (22, 22), (W - 22, h - 22), 1.0, 3, cv2.LINE_AA), (225, 235, 248), 0.5)
    elif dec == "greenbar":
        for k, m in enumerate(metas):
            if (k // 2) % 2 == 0:
                stroke(lambda s, m=m: s.__setitem__((slice(int(m["y"]), int(m["y"] + m["h"])), slice(66, W - 66)), 1.0),
                       (200, 228, 204), 0.45)
        for x in (66, W - 66):  # perforations
            for y in range(0, h, 14):
                cv2.line(amt, (x, y), (x, y + 6), 0.25, 2)
    elif dec == "staff":
        for m in metas:
            if m["spec"][:2] in ("l:", "c:", "r:") or not (":" in m["spec"][:6] or m["spec"] in ("rule", "rule2", "gap")):
                for k in range(5):
                    y = int(m["y"] + 12 + k * 11)
                    stroke(lambda s, y=y: cv2.line(s, (mx, y), (W - mx, y), 1.0, 2, cv2.LINE_AA), (70, 66, 72), 0.55)
    elif dec == "card":
        stroke(lambda s: s.__setitem__((slice(0, 18), slice(None)), 1.0), VERMILION, 1.0)
        cv2.circle(amt, (W // 2, 70), 27, 0.3, 5, cv2.LINE_AA)  # the hole's reinforcement ring
    elif dec == "sticky":
        yy = np.arange(h, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
        pap *= (1 - 0.05 * (yy < h * 0.15))[..., None]  # adhesive band
        lift = np.clip((xx / W + yy / h - 1.5) / 0.5, 0, 1)
        pap *= (1 - 0.14 * lift ** 1.5)[..., None]  # the free corner curls up out of the light
    elif dec == "newsprint":
        yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
        edge = np.minimum(np.minimum(xx, W - xx), np.minimum(yy, h - yy))
        pap *= ((1 - 0.08 * np.exp(-edge / 26))[..., None] * np.array([1.0, 0.98, 0.94], np.float32))  # yellowed edges
    return pap * (1 - amt[..., None]) + lay


def document(kind, lines, seed, audio=None, sr=None, wave_ref=1.0, K=None):
    """Returns (paper RGBA uint8, [(ink RGBA uint8, accent RGBA uint8 or None)], meta)."""
    if kind not in KINDS:
        raise SystemExit(f"unknown document kind {kind!r}; one of {sorted(KINDS)}")
    K = K or KINDS[kind]; W = K["w"]
    rng = np.random.default_rng(seed)
    metas, y = [], K["top"]
    for i, spec in enumerate(lines):
        lh = line_height(K, spec)
        metas.append({"i": i, "spec": spec, "y": y, "h": lh, "wave": spec.startswith("WAVE:")}); y += lh
    teeth = 24 if K["edge"] == "teeth" else 0
    h = max(y + K["bottom"] + teeth, K.get("min_h", 0))
    spare = h - (y + K["bottom"] + teeth)
    if spare > 0:  # a short note on a fixed-size sheet: centre the writing below the adhesive band
        for m in metas:
            m["y"] += int(spare * 0.45)
    pap = paper_tex(h, W, seed, K["paper"], grain=K["grain"], fibres=K["fibres"])
    yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
    if kind == "receipt":
        x = np.linspace(-1, 1, W, dtype=np.float32)
        pap *= (1 - 0.035 * x ** 4 + 0.018 * np.exp(-((x + 0.35) / 0.25) ** 2))[None, :, None]  # cylindrical curl
    else:
        pap *= (1.0125 - 0.025 * (xx / W + yy / h) / 2)[..., None]  # one soft light from the top left
    if kind == "newsprint" or K["deco"] == "newsprint":  # halftone tooth of cheap paper
        pap *= (1 - 0.03 * (np.sin(xx * 0.9) * np.sin(yy * 0.9) > 0.6))[..., None]
    for _ in range(K.get("creases", 2)):  # handling creases: soft relief lines
        y0 = rng.uniform(0.15, 0.9) * h; ang = rng.uniform(-0.25, 0.25)
        dd = (yy - y0 - np.tan(ang) * (xx - W / 2))
        pap *= (1 + 0.035 * np.exp(-(dd / 6) ** 2) - 0.03 * np.exp(-((dd - 7) / 5) ** 2))[..., None]
    pap = _deco(K, kind, pap, metas, h)
    alpha = _edges(K, h, rng, seed)
    imgs = []
    for m in metas:
        spec, lh = m["spec"], m["h"]
        if m["wave"]:
            _, a0, a1 = spec.split(":")
            a = _wave(audio, sr, float(a0), float(a1), wave_ref, K, lh); acc = np.zeros_like(a); info = {"text": "", "xs": [], "pad": 0}
        else:
            a, acc, info = _text_layer(K, kind, spec, lh, rng)
        ph = a.shape[0]  # the padded canvas
        if K.get("tilt"):  # a hand never writes perfectly level
            M = cv2.getRotationMatrix2D((W / 2, ph / 2), rng.normal(0, K["tilt"]), 1.0); M[1, 2] += rng.normal(0, 1.5)
            a = cv2.warpAffine(a, M, (W, ph)); acc = cv2.warpAffine(acc, M, (W, ph))
        dens = 0.80 + 0.2 * rng.random() + 0.08 * fbm(ph, W, seed + 50 + m["i"], 3, 6)
        if kind == "receipt":  # a worn thermal element leaves a faint column
            col = int(rng.uniform(0.2, 0.8) * W); dens[:, col:col + 5] *= 0.55
        a = cv2.GaussianBlur(a, (0, 0), 0.75) * np.clip(dens, 0.5, 1.0)
        acc = cv2.GaussianBlur(acc, (0, 0), 0.75) * np.clip(dens + 0.1, 0.6, 1.0)
        rows = np.where((a + acc).max(1) > 0.003)[0]  # keep only the rows with ink: small, and free to overhang
        r0, r1 = (max(0, int(rows[0]) - 2), min(ph, int(rows[-1]) + 3)) if len(rows) else (info["pad"], info["pad"] + 1)
        a, acc = a[r0:r1], acc[r0:r1]
        cols = np.where((a + acc).max(0) > 0.05)[0]
        m.update(text=info["text"], xs=info["xs"], x0=int(cols[0]) if len(cols) else K["mx"],
                 x1=int(cols[-1]) + 1 if len(cols) else K["mx"], acc=bool(acc.max() > 0.05),
                 iy=int(m["y"] - info["pad"] + r0))
        ink = np.zeros((a.shape[0], W, 4), np.uint8); ink[..., :3] = K["ink"]; ink[..., 3] = np.clip(a * 255, 0, 255)
        ac = None
        if m["acc"]:
            ac = np.zeros((a.shape[0], W, 4), np.uint8); ac[..., :3] = VERMILION; ac[..., 3] = np.clip(acc * 255, 0, 255)
        imgs.append((ink, ac))
    paper = np.dstack([np.clip(pap, 0, 255), alpha * 255]).astype(np.uint8)
    return paper, imgs, {"kind": kind, "w": W, "h": h, "lines": metas, "body_end": h - teeth, "reveal": K["reveal"]}


def screenshot(r, seed):
    """A REAL screenshot as a photo print: the image (r["image"], cropped by r["crop"] = [x0, y0, x1,
    y1] fractions) on matte stock with a white border, its source (r["source"]) typed on the deep
    bottom edge. Line 0 is the image: stamps land on it and `marker: {box: [x0, y0, x1, y1]}` circles
    part of it. Line 1 is the source. Returns what document() returns. Never feed it a post or a
    headline rebuilt to look real: the print is evidence, so the picture must be the real one."""
    img = Image.open(r["image"]).convert("RGB")
    if r.get("crop"):
        x0, y0, x1, y1 = (float(v) for v in r["crop"]); w0, h0 = img.size
        img = img.crop((int(x0 * w0), int(y0 * h0), int(round(x1 * w0)), int(round(y1 * h0))))
    K = dict(KINDS["screenshot"]); W, b = K["w"], K["mx"]
    iw = W - 2 * b; ih = int(round(img.height * iw / img.width))
    if ih > 1.8 * iw:
        print(f"  [documents] screenshot is {ih / iw:.1f}x taller than wide: crop it to the part that matters "
              f"(crop: [x0, y0, x1, y1])")
    src = str(r.get("source") or "").strip()
    K["top"] = b + ih + 18
    K["bottom"] = 34 if src else b - 18
    paper, imgs, meta = document("screenshot", [f"c:{src.upper()}"] if src else [], seed, K=K)
    shot = np.asarray(img.resize((iw, ih), Image.LANCZOS), np.float32) * 0.95 + 6  # matte: the blacks lift a little
    paper[b - 2:b + ih + 2, b - 2:b + iw + 2, :3] = (196, 194, 190)  # a keyline, so a white page never melts into the border
    paper[b:b + ih, b:b + iw, :3] = np.clip(shot, 0, 255).astype(np.uint8)
    for L in meta["lines"]:  # the source line: printed with the paper, never written on his words
        L["i"] += 1; L["caption"] = True
    meta["lines"].insert(0, {"i": 0, "spec": "IMAGE", "y": b, "h": ih, "wave": False, "text": "", "xs": [], "x0": b,
                             "x1": b + iw, "acc": False, "iy": b, "image": True})
    meta.update(image=[b, b, iw, ih], source=src)
    return paper, [(np.zeros((1, W, 4), np.uint8), None)] + imgs, meta
