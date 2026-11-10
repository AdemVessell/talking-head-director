"""Stage: a rostrum camera over physical layers, lit by one warm desk light.

Layers (bottom to top): the treatment's surface (charcoal, cork, kraft, mat,
walnut, linen, slate), photo print of the presenter (live video, face-tracked
crop, graded), film prints (any footage, played inside one shot), labels, paper
documents (drop or slap in, taped or pinned; each line reveals on its words in
its kind's manner, accents on theirs, marker, stamps). Layout coordinates are
output pixels at camera zoom 1.

Camera keys per beat: [time-expr, target, ease]. Targets:
  {"center": [x, y], "zoom": z}
  {"face": "W|H|C|X" or 0.6, "eye": 0.36, "screen_x": 0.5}   frame the presenter's face
  {"doc": "r1", "line": 10, "zoom": 2.6, "screen_y": 0.5}   centre a document line ("receipt": too)
  {"fit": ["r1", "r2", "presenter", "film:0"], "band": [0.27, 0.66]}  fit into a screen band
Any target also takes "zoom_mul", "dx", "dy" (layout px) to make a push or drift.
"""
import json, math, sys
import cv2
import numpy as np
from PIL import Image

from . import lives, surfaces, treatments
from .plan import SCRIPTS
from .prep import load_ranges

sys.path.insert(0, str(SCRIPTS))
from face_track import Track  # noqa: E402
from look import grade_webcam  # noqa: E402

LADDER = {"W": 0.35, "H": 0.50, "C": 0.67, "X": 0.95, "XX": 1.25}
VERMILION = np.array([226, 69, 43], np.float32) / 255


def c01(x): return max(0.0, min(1.0, x))
def seg(t, a, b): return c01((t - a) / (b - a)) if b > a else float(t >= b)
def lerp(a, b, u): return a + (b - a) * u


EASE = {
    "linear": lambda x: c01(x),
    "io2": lambda x: (lambda x: 2 * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 2 / 2)(c01(x)),
    "io3": lambda x: (lambda x: 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2)(c01(x)),
    "o3": lambda x: 1 - (1 - c01(x)) ** 3,
    "oexp": lambda x: 1.0 if c01(x) >= 1 else 1 - 2 ** (-10 * c01(x)),
}


def e_oback(x, s=0.9):
    x = c01(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


# ---------------------------------------------------------------- affine + compositing

def A_place(pos, rot, scale, anchor=(0.0, 0.0)):
    th = math.radians(rot); c, s = math.cos(th) * scale, math.sin(th) * scale
    return np.array([[c, -s, pos[0] - c * anchor[0] + s * anchor[1]],
                     [s, c, pos[1] - s * anchor[0] - c * anchor[1]], [0, 0, 1]])


def T(dx, dy): return np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1.0]])


class Tex:
    """Premultiplied float32 texture with lazy mip levels (no aliasing when zoomed out)."""
    def __init__(self, arr, dtype=np.float32):
        self.lv = [np.ascontiguousarray(arr, dtype) if dtype else np.ascontiguousarray(arr)]

    def pick(self, M):
        s = math.sqrt(abs(np.linalg.det(M[:2, :2])))
        k = 0
        while s * 2 ** k < 0.55 and k < 4:
            k += 1
        while len(self.lv) <= k:
            a = self.lv[-1]
            self.lv.append(cv2.resize(a, (max(1, a.shape[1] // 2), max(1, a.shape[0] // 2)), interpolation=cv2.INTER_AREA))
        f = 2 ** k
        return self.lv[k], M @ np.diag([f, f, 1.0])


def premult(rgb, a):
    return np.dstack([rgb * a[..., None], a]).astype(np.float32)


def soft_shadow(alpha, sigma):
    """Blurred, padded alpha for a cast shadow. Returns (Tex, pad)."""
    pad = int(3 * sigma) + 2
    a = cv2.copyMakeBorder(alpha.astype(np.float32), pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    small = cv2.resize(a, (max(2, a.shape[1] // 4), max(2, a.shape[0] // 4)), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma / 4)
    return Tex(cv2.resize(small, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_LINEAR)), pad


def load_rgba(path):
    return np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255


class Canvas:
    def __init__(self, W, H):
        self.W, self.H = W, H

    def warp(self, tex, M):
        arr, M = tex.pick(M) if isinstance(tex, Tex) else (tex, M)
        h, w = arr.shape[:2]
        pts = M @ np.array([[0, w, 0, w], [0, 0, h, h], [1, 1, 1, 1]], float)
        x0 = max(0, int(math.floor(pts[0].min())) - 2); x1 = min(self.W, int(math.ceil(pts[0].max())) + 2)
        y0 = max(0, int(math.floor(pts[1].min())) - 2); y1 = min(self.H, int(math.ceil(pts[1].max())) + 2)
        if x1 <= x0 or y1 <= y0:
            return None
        Ms = M.copy(); Ms[0, 2] -= x0; Ms[1, 2] -= y0
        out = cv2.warpAffine(arr, Ms[:2], (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if out.ndim == 2:
            out = out[..., None]
        return out, (x0, y0, x1, y1)

    def over(self, dst, tex, M):
        r = self.warp(tex, M)
        if r:
            o, (x0, y0, x1, y1) = r
            dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - o[..., 3:4]) + o[..., :3]

    def darken(self, dst, alpha_tex, M, k):
        r = self.warp(alpha_tex, M)
        if r:
            o, (x0, y0, x1, y1) = r
            dst[y0:y1, x0:x1] *= (1 - k * o[..., :1])

    def multiply(self, dst, tex, M):
        r = self.warp(tex, M)
        if r:
            o, (x0, y0, x1, y1) = r
            dst[y0:y1, x0:x1] *= (1 - o[..., 3:4] + o[..., :3])

    def fill_board(self, dst, tex, M):
        """The surface covers the whole frame; reflect at its edges so no camera move can find one."""
        arr, M = tex.pick(M)
        out = cv2.warpAffine(arr, M[:2], (self.W, self.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        if out.dtype == np.uint8:
            np.multiply(out[..., :3], np.float32(1 / 255), out=dst, casting="unsafe")
        else:
            dst[:] = out[..., :3]


# ---------------------------------------------------------------- documents

class Doc:
    """A paper document: drops or slaps onto the surface; each line's ink reveals on its own
    words in its kind's manner (thermal pop, typewriter, pen, plotter, print head) and its
    accent (strike, tick, bar fill) lands on its own cue."""
    def __init__(self, mdir, name, meta):
        self.name, self.m = name, meta
        p = load_rgba(mdir / f"{name}_paper.png")
        self.rgb, self.alpha = p[..., :3], p[..., 3]
        self.lines = []
        for L in meta["lines"]:
            ink = load_rgba(mdir / f"{name}_line{L['i']:02d}.png")
            acc = load_rgba(mdir / f"{name}_line{L['i']:02d}_acc.png") if L.get("acc") else None
            self.lines.append((L, ink, acc))
        self.shadow = soft_shadow(self.alpha, 14)  # the paper's outline never changes
        self.xs = np.arange(meta["w"], dtype=np.float32)
        self.cache = {}

    def state(self, t, life, fps):
        if t < life.get("appear", -1e9):
            return None
        out = []
        for i, (L, _, acc) in enumerate(self.lines):
            k = self.prog(t, life["cues"].get(i), fps, L)
            a = self.prog(t, life["marks"].get(i), fps, L) if acc is not None else 0.0
            out.append((k, a))
        return tuple(out)

    @staticmethod
    def prog(t, cue, fps, L):
        if cue is None:
            return 1.0
        t0, t1, mode = cue
        if mode == "ink":  # thermal paper darkens in three frames
            return round(EASE["o3"]((t - t0) * fps / 3), 2)
        u = c01((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)
        if mode == "type" and L.get("xs"):  # one key strike per character
            n = len(L["xs"]); return math.floor(u * n + 1e-6) / n
        if mode == "print":  # the print head moves in bursts
            return math.floor(u * 10 + 1e-6) / 10
        return round(u, 3)

    def mask(self, L, la, k, mode):
        if k >= 1:
            return la
        if mode == "ink":
            return la * k
        x0, x1 = L["x0"], L["x1"]
        if mode == "type" and L.get("xs"):
            n = int(round(k * len(L["xs"])))
            ramp = (self.xs < (L["xs"][n - 1] + 2 if n > 0 else -1)).astype(np.float32)
        elif mode in ("type", "print", "wipe"):
            ramp = (self.xs < x0 + k * (x1 - x0)).astype(np.float32)
        else:  # a pen: the newest ink fades in behind a soft head
            fe = 16.0 if mode == "draw" else 30.0
            ramp = np.clip((x0 - fe + k * (x1 - x0 + 2 * fe) - self.xs) / fe, 0, 1)
        return la * ramp[None, :, None]

    def texture(self, st, life, marker=0.0, marker_lines=None):
        key = (st, round(marker, 3))
        if key in self.cache:
            return self.cache[key]
        rgb = self.rgb.copy(); H = rgb.shape[0]
        for (L, ink, acc), (k, ka) in zip(self.lines, st):
            y0 = L.get("iy", L["y"])  # a line's ink may overhang its box (descenders), never the paper
            a0, a1 = max(0, -y0), min(ink.shape[0], H - y0)
            if a1 <= a0 or (k <= 0 and ka <= 0):
                continue
            band = rgb[y0 + a0:y0 + a1]; mode = life["modes"][L["i"]]
            if k > 0:
                la = self.mask(L, ink[a0:a1, :, 3:4], k, mode)
                band *= (1 - la); band += ink[a0:a1, :, :3] * la
            if acc is not None and ka > 0:
                la = self.mask(L, acc[a0:a1, :, 3:4], ka, "wipe" if mode == "ink" else "write")
                band *= (1 - la); band += acc[a0:a1, :, :3] * la
        if marker > 0 and marker_lines:
            draw_marker(rgb, self.m, marker, marker_lines)
        tex = Tex(premult(rgb, self.alpha))
        if len(self.cache) > 60:
            self.cache.clear()
        self.cache[key] = tex
        return tex


def draw_marker(rgb, m, prog, lines):
    """Vermilion felt-tip ellipse around document lines a..b (on a screenshot, around ("box", x0, y0,
    x1, y1): fractions of the image), wobbly, drawn on twos."""
    if lines[0] == "box":
        ix, iy, iw, ih = m["image"]; x0, y0, x1, y1 = lines[1:]
        cx, cy = ix + (x0 + x1) / 2 * iw, iy + (y0 + y1) / 2 * ih
        rx, ry = (x1 - x0) / 2 * iw * 1.08 + 18, (y1 - y0) / 2 * ih + 24
    else:
        a, b = lines
        y0 = m["lines"][a]["y"] - 8; y1 = m["lines"][b]["y"] + m["lines"][b]["h"] + 4
        cx, cy, rx, ry = m["w"] / 2 + 2, (y0 + y1) / 2, m["w"] / 2 - 10, (y1 - y0) / 2 + 26
    rng = np.random.default_rng(4)
    n = 140; total = 2 * math.pi * 1.08
    th = -math.pi * 0.62 + np.linspace(0, total * prog, max(2, int(n * prog)))
    wob = 1 + 0.025 * np.sin(th * 3.0 + 1.3) + 0.015 * np.sin(th * 7.0)
    drift = 1 + 0.05 * (th - th[0]) / total  # the pen spirals out a little as it closes
    pts = np.stack([cx + rx * wob * drift * np.cos(th), cy + ry * wob * drift * np.sin(th)], 1)
    lay = np.zeros(rgb.shape[:2], np.float32)
    cv2.polylines(lay, [np.round(pts * 4).astype(np.int32)], False, 1.0, 13, cv2.LINE_AA, shift=2)
    lay = cv2.GaussianBlur(lay, (0, 0), 0.8) * (0.86 + 0.1 * rng.random())
    rgb *= (1 - lay[..., None]) + lay[..., None] * VERMILION[None, None, :]


# ---------------------------------------------------------------- footage

def read_at(caps, key, path, idx):
    """Frame idx of a ProRes file. Rendering is sequential, so seek only when the wanted frame
    is not the next one (a seek per frame cost ~40 ms); repeat requests hit a one-frame cache."""
    st = caps.get(key)
    if st is None or isinstance(st, cv2.VideoCapture):
        cap = st if isinstance(st, cv2.VideoCapture) else cv2.VideoCapture(path)
        st = caps[key] = {"cap": cap, "pos": -1, "idx": None, "img": None}
    if st["idx"] == idx:
        return st["img"]
    if idx != st["pos"] + 1:
        st["cap"].set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, fr = st["cap"].read()
    assert ok, (key, idx)
    st["pos"], st["idx"], st["img"] = idx, idx, cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
    return st["img"]


class Footage:
    """Presenter video by edit time: EDL picture mapping into the extracted ranges."""
    def __init__(self, plan, edl):
        self.plan, self.edl, self.fps = plan, edl, plan.fps
        self.ranges = load_ranges(plan)
        self.tracks = {r: Track.load(plan.wp("prep", f"track_{r}.json")) for r in self.ranges}
        self.caps = {}

    def map(self, t):
        segs = self.edl["segments"]
        s = next((s for s in segs if s["p_in"] <= t < s["p_out"]), segs[-1])
        src = s["src_in"] + (t - s["edit_in"])
        r = s["range"]; local = src - self.ranges[r][0]
        n = self.tracks[r].a.shape[0]
        return r, min(n - 1, max(0, int(round(local * self.fps)))) / self.fps

    def frame(self, r, local):
        return read_at(self.caps, r, str(self.plan.wp("prep", f"{r}.mov")), int(round(local * self.fps)))


class Films:
    def __init__(self, plan):
        self.plan, self.fps, self.caps = plan, plan.fps, {}

    def frame(self, fid, film_t):
        f = self.plan["films"][fid]
        if fid not in self.caps:
            self.caps[fid] = cv2.VideoCapture(str(self.plan.wp("prep", f"film_{fid}.mov")))
        st = self.caps[fid]
        n = int((st if isinstance(st, cv2.VideoCapture) else st["cap"]).get(cv2.CAP_PROP_FRAME_COUNT))
        return read_at(self.caps, fid, None, min(n - 1, max(0, int(round((film_t - f["from"]) * self.fps)))))


# ---------------------------------------------------------------- the stage

class Stage:
    def __init__(self, plan, tl, meta, scale=1.0, lives=None):
        self.plan, self.tl, self.meta, self._lives = plan, tl, meta, lives
        self.scale = scale  # proof renders draw the same layout at a fraction of the size
        self.W, self.H, self.fps = int(round(plan.W * scale)), int(round(plan.H * scale)), plan.fps
        self.cv = Canvas(self.W, self.H)
        md = plan.wp("materials")
        self.surfaces = {}
        self.print_paper = load_rgba(md / "print_paper.png")[..., :3]
        self.tapes, self.pins = [], []
        for i in range(4):
            t_ = load_rgba(md / f"tape{i}.png")
            sh, pad = soft_shadow(t_[..., 3] * 0.9, 4)
            self.tapes.append((Tex(premult(t_[..., :3], t_[..., 3])), sh, pad, t_.shape[1], t_.shape[0]))
        for i in range(3):
            p_ = load_rgba(md / f"pin{i}.png")
            sh, pad = soft_shadow(p_[..., 3], 4)
            self.pins.append((Tex(premult(p_[..., :3], p_[..., 3])), sh, pad, p_.shape[1], p_.shape[0]))
        self.docs = {k: Doc(md, k, m) for k, m in meta["docs"].items()}
        self.labels = {}
        for k in meta["labels"]:
            l_ = load_rgba(md / f"label_{k}.png")
            self.labels[k] = (Tex(premult(l_[..., :3], l_[..., 3])), soft_shadow(l_[..., 3], 6), l_.shape[1], l_.shape[0])
        self.stamps = {k: load_rgba(md / f"stamp_{k}.png") for k in meta["stamps"]}
        self.footage = Footage(plan, tl.edl)
        self.films = Films(plan)
        self.shadow_cache = {}
        self.mounts = {}
        self.print_cache = {}
        self._resolve()

    def surface(self, name):
        if name not in self.surfaces:  # 8-bit and loaded on first use: one per layout's surface, not all seven
            self.surfaces[name] = Tex(np.asarray(Image.open(surfaces.path(name)).convert("RGB")), dtype=None)
        return self.surfaces[name]

    @staticmethod
    def lay_docs(lay):
        """A layout's document placements (`documents` plus the older `receipts`)."""
        if "_docs" not in lay:
            d = dict(lay.get("receipts", {})); d.update(lay.get("documents", {})); lay["_docs"] = d
        return lay["_docs"]

    # ---- plan -> numbers
    def _resolve(self):
        tl, plan = self.tl, self.plan
        self.lives = self._lives if self._lives is not None else lives.resolve(plan, tl, self.meta)
        self.stamp_times = sorted(s["at"] for life in self.lives.values() for s in life["stamps"])
        self.beats = []
        for b in plan.get("beats", []):
            lay = plan["layouts"][b["layout"]]
            t0, t1 = tl.t(b["from"]), tl.t(b["to"])
            keys = []
            for k in b["camera"]:
                kt, target = tl.t(k[0]), k[1]
                ease = EASE[k[2]] if len(k) > 2 and k[2] else None
                keys.append((kt, self.target(lay, target), ease))
            films = []
            for f in lay.get("films", []):
                f = dict(f); f["appear_t"] = tl.t(f.get("appear", t0)); films.append(f)
            labels = []
            for l_ in lay.get("labels", []):
                l_ = dict(l_); l_["appear_t"] = tl.t(l_.get("appear", t0)); labels.append(l_)
            docs = b.get("docs", b.get("documents", b.get("receipts", list(self.lay_docs(lay).keys()))))
            self.beats.append(dict(name=b["name"], t0=t0, t1=t1, lay=lay, keys=keys, films=films, labels=labels,
                                   docs=docs, surface=treatments.surface(plan, lay), light=treatments.light(plan, lay)))
        self.beats.sort(key=lambda b: b["t0"])

    def target(self, lay, tg):
        W, H = self.plan.W, self.plan.H
        if "center" in tg:
            cx, cy = tg["center"]; z = tg["zoom"]
        elif "face" in tg:
            P = lay["presenter"]; iw, ih = P["inner"]
            size = LADDER.get(tg["face"], tg["face"]) if isinstance(tg["face"], str) else float(tg["face"])
            z = size * W / (P["face_frac"] * iw)
            th = math.radians(P.get("rot", 0)); fx = P.get("x_offset", 0.0) * iw; fy = -ih / 2 + P.get("eye", 0.36) * ih
            px = P["center"][0] + fx * math.cos(th) - fy * math.sin(th)
            py = P["center"][1] + fx * math.sin(th) + fy * math.cos(th)
            cx = px - (tg.get("screen_x", 0.5) - 0.5) * W / z
            cy = py - (tg.get("eye", 0.36) - 0.5) * H / z
        elif "doc" in tg or "receipt" in tg:
            px, py = self.rc_pt(lay, tg.get("doc", tg.get("receipt")), tg.get("line", 0))
            z = tg["zoom"]; cx = px; cy = py - (tg.get("screen_y", 0.5) - 0.5) * H / z
        elif "fit" in tg:
            xs, ys = [], []
            for name in tg["fit"]:
                for x, y in self.corners(lay, name):
                    xs.append(x); ys.append(y)
            top, bot = tg.get("band", [0.27, 0.66]); m = tg.get("margin", 0.04)
            bw, bh = max(xs) - min(xs), max(ys) - min(ys)
            z = min((1 - 2 * m) * W / bw, (bot - top) * H / bh)
            cx = (max(xs) + min(xs)) / 2
            cy = (max(ys) + min(ys)) / 2 - ((top + bot) / 2 - 0.5) * H / z
        else:
            raise ValueError(f"unknown camera target {tg}")
        z *= tg.get("zoom_mul", 1.0)
        return (cx + tg.get("dx", 0.0), cy + tg.get("dy", 0.0), z)

    def rc_len(self, name, R):
        return self.docs[name].m["h"] * R["width"] / self.docs[name].m["w"]

    def rc_pt(self, lay, name, line):
        """Layout point at the centre of a document line, including the paper's hang angle."""
        R = self.lay_docs(lay)[name]; m = self.docs[name].m; L = m["lines"][line]
        d = (L["y"] + L["h"] / 2) * R["width"] / m["w"]; th = math.radians(R.get("rot", 0))
        x0 = R["left"] + R["width"] / 2
        return x0 - d * math.sin(th), R["top"] + d * math.cos(th)

    def corners(self, lay, name):
        if name == "presenter":
            P = lay["presenter"]; b = P.get("border", 20)
            w, h = P["inner"][0] + 2 * b, P["inner"][1] + 2 * b
            return self._rect(P["center"], w, h, P.get("rot", 0))
        if name.startswith("film:"):
            P = lay["films"][int(name.split(":")[1])]; b = P.get("border", 16)
            return self._rect(P["center"], P["inner"][0] + 2 * b, P["inner"][1] + 2 * b, P.get("rot", 0))
        R = self.lay_docs(lay)[name]; L = self.rc_len(name, R)
        th = math.radians(R.get("rot", 0)); x0 = R["left"] + R["width"] / 2
        pts = [(-R["width"] / 2, 0), (R["width"] / 2, 0), (-R["width"] / 2, L), (R["width"] / 2, L)]
        return [(x0 + x * math.cos(th) - y * math.sin(th), R["top"] + x * math.sin(th) + y * math.cos(th)) for x, y in pts]

    @staticmethod
    def _rect(c, w, h, rot):
        th = math.radians(rot)
        return [(c[0] + x * math.cos(th) - y * math.sin(th), c[1] + x * math.sin(th) + y * math.cos(th))
                for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (-w / 2, h / 2), (w / 2, h / 2))]

    # ---- time -> state
    def beat_at(self, t):
        t = min(max(t, 0.0), self.tl.total - 1e-6)
        for b in self.beats:
            if b["t0"] <= t < b["t1"]:
                return b
        return self.beats[-1] if t >= self.beats[-1]["t0"] else self.beats[0]

    def drop_offset(self, t, life):
        d = life.get("drop")
        if not d:
            return 0.0
        t0, t1, D = d
        return -D * (1 - e_oback(seg(t, t0, t1)))

    def cam(self, t):
        b = self.beat_at(t); ks = b["keys"]
        if t <= ks[0][0]:
            cx, cy, z = ks[0][1]
        else:
            cx, cy, z = ks[-1][1]
            for (t0, c0, _), (t1, c1, ez) in zip(ks, ks[1:]):
                if t <= t1:
                    u = (ez or EASE["io2"])(seg(t, t0, t1))
                    cx, cy, z = lerp(c0[0], c1[0], u), lerp(c0[1], c1[1], u), math.exp(lerp(math.log(c0[2]), math.log(c1[2]), u))
                    break
        sx = sy = rot = 0.0
        for t0 in self.stamp_times:  # an impact shakes the camera group, never the captions
            i = (t - t0) * self.fps
            if 0 <= i < 8:
                amp = 10 * math.exp(-0.45 * i); ph = i * 2.3 + t0 * 7
                sx += amp * math.sin(ph); sy += amp * math.cos(ph * 1.3); rot += 0.35 * math.exp(-0.45 * i) * math.sin(ph * 0.7)
        th = math.radians(rot); c, s = math.cos(th) * z, math.sin(th) * z
        W, H = self.plan.W, self.plan.H
        M = np.array([[c, -s, W / 2 + sx - c * cx + s * cy], [s, c, H / 2 + sy - s * cx - c * cy], [0, 0, 1]])
        if self.scale != 1.0:
            M = np.diag([self.scale, self.scale, 1.0]) @ M
        return M, (cx, cy, z)

    def motion_px(self, t):
        """Screen travel per frame: camera moves plus any paper in flight (sets the blur samples)."""
        h = 0.5 / self.fps
        if self.beat_at(t - h) is not self.beat_at(t + h):
            return 0.0
        M0, _ = self.cam(t - h); M1, c1 = self.cam(t + h)
        p = np.array([[self.W / 2, 0, self.W], [self.H / 2, 0, self.H], [1, 1, 1]], float)
        d = float(np.abs(np.linalg.inv(M0) @ p - np.linalg.inv(M1) @ p)[:2].max() * c1[2] * self.scale)
        for name in self.beat_at(t)["docs"]:
            life = self.lives.get(name, {})
            if life.get("drop") and t >= life.get("appear", -1e9):
                d = max(d, abs(self.drop_offset(t + h, life) - self.drop_offset(t - h, life)) * c1[2])
        return d

    # ---- drawing
    def light_map(self, M, light):
        lx, ly, sig, lo, hi = light
        X, Y = np.meshgrid(np.arange(0, self.W + 16, 16, dtype=np.float64), np.arange(0, self.H + 16, 16, dtype=np.float64))
        Mi = np.linalg.inv(M)
        Lx = Mi[0, 0] * X + Mi[0, 1] * Y + Mi[0, 2]; Ly = Mi[1, 0] * X + Mi[1, 1] * Y + Mi[1, 2]
        g = np.exp(-((Lx - lx) ** 2 + (Ly - ly) ** 2) / (2 * sig ** 2)).astype(np.float32)
        gain = lo + (hi - lo) * g
        tint = np.stack([1 + 0.03 * g - 0.025 * (1 - g), 1 - 0.01 * (1 - g), 1 - 0.045 * g + 0.03 * (1 - g)], -1)
        return cv2.resize(gain[..., None] * tint, (self.W, self.H), interpolation=cv2.INTER_LINEAR)

    def mount(self, img, P, res, tag="print"):
        """Mount an image as a matte photo print: paper border, faint sheen, raised black point.
        The mount (border, sheen, alpha) is cached per size; each frame only writes its image."""
        th, tw = img.shape[:2]
        B = int(round(P.get("border", 20) * res))
        key = (tag, id(P), tw, th, B)  # one buffer per print, so two prints never share pixels
        if key not in self.mounts:
            ow, oh = tw + 2 * B, th + 2 * B
            pp = cv2.resize(self.print_paper, (ow, oh), interpolation=cv2.INTER_LINEAR)
            a = np.ones((oh, ow), np.float32)
            a[0, :] = a[-1, :] = a[:, 0] = a[:, -1] = 0.5
            buf = premult(pp, a)
            gy, gx = np.mgrid[0:th, 0:tw].astype(np.float32)
            sheen = (1 + 0.035 * (1 - (gx / tw + gy / th) / 2)) * 0.975  # light from top-left; black point 0.02
            self.mounts[key] = (buf, np.ascontiguousarray(np.repeat(sheen[..., None], 3, 2)), (ow / res, oh / res))
        buf, sheen, size = self.mounts[key]
        inner = cv2.add(cv2.multiply(img.astype(np.float32, copy=False), sheen), 0.02)
        buf[B:B + th, B:B + tw, :3] = inner
        buf[B - 1:B + th + 1, B - 1:B + tw + 1, :3][[0, -1], :] *= 0.82  # the print's inner edge
        buf[B - 1:B + th + 1, B - 1:B + tw + 1, :3][:, [0, -1]] *= 0.82
        return buf, size

    def presenter_print(self, fr, rl, P):
        key = (rl, id(P))
        if key in self.print_cache:
            return self.print_cache[key]
        if len(self.print_cache) > 4:
            self.print_cache.clear()
        out = self._presenter_print(fr, rl, P)
        self.print_cache[key] = out
        return out

    def _presenter_print(self, fr, rl, P):
        res = P.get("res", 1.2) * self.scale; iw, ih = P["inner"]; track = self.footage.tracks[rl[0]]
        x, y, w, h = track.crop(rl[1], face_frac=P["face_frac"], aspect=iw / ih, eye_line=P.get("eye", 0.36),
                                x_offset=P.get("x_offset", 0.0))
        cx, ey, fw = track.at(rl[1])
        g = grade_webcam(fr[y:y + h, x:x + w], face=(cx - x, ey - y, fw), **P.get("grade", {})).astype(np.float32) / 255
        tw, th = int(round(iw * res)), int(round(ih * res))
        return self.mount(cv2.resize(g, (tw, th), interpolation=cv2.INTER_CUBIC if tw > w else cv2.INTER_AREA), P, res, "presenter")

    def film_print(self, frame, P):
        res = P.get("res", 1.4) * self.scale; iw, ih = P["inner"]; tw, th = int(round(iw * res)), int(round(ih * res))
        fh, fw = frame.shape[:2]
        if P.get("cover", True):  # crop the film to the print's aspect, centred (or at "focus": [fx, fy])
            ar = iw / ih; fx, fy = P.get("focus", [0.5, 0.5])
            if fw / fh > ar:
                cw = int(fh * ar); x0 = int(np.clip(fx * fw - cw / 2, 0, fw - cw)); frame = frame[:, x0:x0 + cw]
            else:
                ch = int(fw / ar); y0 = int(np.clip(fy * fh - ch / 2, 0, fh - ch)); frame = frame[y0:y0 + ch]
        img = cv2.resize(frame, (tw, th), interpolation=cv2.INTER_AREA if frame.shape[1] > tw else cv2.INTER_CUBIC)
        return self.mount(img.astype(np.float32) / 255, P, res, "film")

    def print_shadow(self, ow, oh, res):
        key = (round(ow), round(oh), round(res, 4))
        if key not in self.shadow_cache:
            a = np.ones((int(round(oh * res / 2)), int(round(ow * res / 2))), np.float32)
            self.shadow_cache[key] = soft_shadow(a, 7 * res)
        return self.shadow_cache[key]

    def draw_print(self, dst, M, P, tex, ow, oh, sc=1.0):
        cv = self.cv; res = P.get("res", 1.2) * self.scale
        Mp = M @ A_place(P["center"], P.get("rot", 0), sc / res, (tex.shape[1] / 2, tex.shape[0] / 2))
        sh, pad = self.print_shadow(ow, oh, res)
        lift = 1 + 1.5 * (sc - 1) / 0.06
        # the shadow texture is half the print's texture resolution, padded by `pad`
        Ms = M @ T(9 * lift, 13 * lift) @ A_place(P["center"], P.get("rot", 0), 2 * sc / res,
                                                  (tex.shape[1] / 4 + pad, tex.shape[0] / 4 + pad))
        cv.darken(dst, sh, Ms, 0.55 / lift)
        cv.over(dst, Tex(tex) if not isinstance(tex, Tex) else tex, Mp)
        for side, ti, ang in P.get("tapes", []):  # tape on the top corners
            tx, tsh, tpad, tw, th = self.tapes[ti]
            hw, hh = ow / 2 * sc, oh / 2 * sc
            lx = side * (hw - 26); ly = -hh + 6
            r = math.radians(P.get("rot", 0))
            px = P["center"][0] + lx * math.cos(r) - ly * math.sin(r)
            py = P["center"][1] + lx * math.sin(r) + ly * math.cos(r)
            cv.darken(dst, tsh, M @ T(3, 4) @ A_place((px, py), ang + P.get("rot", 0), 0.5, (tw / 2 + tpad, th / 2 + tpad)), 0.3)
            cv.over(dst, tx, M @ A_place((px, py), ang + P.get("rot", 0), 0.5, (tw / 2, th / 2)))

    def render(self, t, fr, rl, t_ink=None):
        """One stage frame at time t. t_ink: the frame's own time, so motion-blur subframes share
        one ink state (a reveal is not blurred, and each document texture is built once a frame)."""
        t_ink = t if t_ink is None else t_ink
        b = self.beat_at(t); lay = b["lay"]; cv = self.cv
        M, _ = self.cam(t)
        dst = np.empty((self.H, self.W, 3), np.float32)
        bx, by = lay.get("board", [600, 800])
        cv.fill_board(dst, self.surface(b["surface"]), M @ T(-bx, -by))
        if "presenter" in lay:
            P = lay["presenter"]; tex, (ow, oh) = self.presenter_print(fr, rl, P)
            self.draw_print(dst, M, P, tex, ow, oh)
        for P in b["films"]:  # film prints slap onto the board on their cue, each playing one shot
            if t >= P["appear_t"]:
                k = (t - P["appear_t"]) * self.fps
                slap = 1.06 if k < 1 else (1.02 if k < 2 else 1.0)
                if not P.get("slap", True):
                    slap = 1.0
                f0, f1 = P["window"]
                frame = self.films.frame(P["film"], min(f1, f0 + t - P["appear_t"]))
                tex, (ow, oh) = self.film_print(frame, P)
                self.draw_print(dst, M, P, tex, ow, oh, slap)
        for L in b["labels"]:
            if t >= L["appear_t"]:
                ltex, (lsh, lpad), lw, lh = self.labels[L["label"]]
                s = L.get("scale", 0.62)
                cv.darken(dst, lsh, M @ T(4, 6) @ A_place(L["center"], L.get("rot", 0), s, (lw / 2 + lpad, lh / 2 + lpad)), 0.4)
                cv.over(dst, ltex, M @ A_place(L["center"], L.get("rot", 0), s, (lw / 2, lh / 2)))
        placed = self.lay_docs(lay)
        for name in b["docs"]:
            R = placed[name]; life = self.lives.get(name, {}); doc = self.docs[name]
            st = doc.state(t_ink, life, self.fps)
            if st is None:
                continue
            mk, ml = 0.0, None
            if "marker" in life:
                m0, m1, ml = life["marker"]
                tw2 = math.floor(t_ink * self.fps / 2 + 1e-6) * 2 / self.fps  # drawn on twos
                mk = c01((tw2 - m0) / (m1 - m0)) if t_ink >= m0 else 0.0
            rtex = doc.texture(st, life, mk, ml); rsh, rpad = doc.shadow
            pop = 1.0
            if "slap" in life:  # slapped down: two frames proud of the surface
                k = (t - life["slap"]) * self.fps
                pop = 1.06 if 0 <= k < 1 else (1.02 if 0 <= k < 2 else 1.0)
            s = R["width"] / doc.m["w"] * pop
            top = R["top"] + self.drop_offset(t, life)
            anchor = (R["left"] + R["width"] / 2, top)
            Mr = M @ A_place(anchor, R.get("rot", 0), s, (doc.m["w"] / 2, 0))
            lift = 1.0 + 0.8 * c01(-self.drop_offset(t, life) / 200) + 8 * (pop - 1)  # paper in the air: longer, softer shadow
            cv.darken(dst, rsh, M @ T(12 * lift, 16 * lift) @ A_place(anchor, R.get("rot", 0), s, (doc.m["w"] / 2 + rpad, rpad)), 0.5 / lift)
            cv.over(dst, rtex, Mr)
            if R.get("tape") and t >= life.get("tape_at", -1e9):
                k = (t - life.get("tape_at", -1e9)) * self.fps
                ts = 0.5 * (1.12 if k < 1 else (1.04 if k < 2 else 1.0))  # slapped on
                ang = R.get("rot", 0) + R.get("tape_angle", 3)
                tx, tsh, tpad, tw, th = self.tapes[R.get("tape_index", 1)]
                tp = (R["left"] + R["width"] / 2, top + 4)
                cv.darken(dst, tsh, M @ T(3, 4) @ A_place(tp, ang, ts, (tw / 2 + tpad, th / 2 + tpad)), 0.35)
                cv.over(dst, tx, M @ A_place(tp, ang, ts, (tw / 2, th / 2)))
            if R.get("pin") is not None and R.get("pin") is not False:  # a push pin through the top
                ptx, psh, ppad, pw, ph = self.pins[0 if R["pin"] is True else int(R["pin"])]
                d = 52 * s; th_ = math.radians(R.get("rot", 0))
                pp = (anchor[0] - d * math.sin(th_), top + d * math.cos(th_))
                cv.darken(dst, psh, M @ T(7, 10) @ A_place(pp, 0, 0.5, (pw / 2 + ppad, ph / 2 + ppad)), 0.55)
                cv.over(dst, ptx, M @ A_place(pp, 0, 0.5, (pw / 2, ph / 2)))
            for S in life["stamps"]:  # ink multiplies whatever it lands on
                if t < S["at"]:
                    continue
                i = (t - S["at"]) * self.fps
                sc = 1.16 if i < 1 else (1.05 if i < 2 else 1.0)
                fresh = 1.0 if i >= 2 else 0.85
                arr = self.stamps[S["text"]]; sw, shh = arr.shape[1], arr.shape[0]
                px, py = self.rc_pt(lay, name, S["line"])
                stt = premult(arr[..., :3] * 0.92 + 0.08, arr[..., 3] * fresh)
                cv.multiply(dst, stt, M @ A_place((px, py + top - R["top"] + 6), S["angle"], S["width"] / sw * sc, (sw / 2, shh / 2)))
        dst *= self.light_map(M, b["light"])
        return dst
