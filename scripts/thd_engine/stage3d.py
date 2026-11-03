"""Stage3D: the same desk seen by a perspective camera (the opt-in `journey` look).

Every layer the stage draws is placed through one camera matrix, so a plane
homography in place of the rostrum camera's affine shows the same desk from any
height, tilt and heading. With no view on a shot the matrix is exactly the
rostrum camera's, so a journey plan frames everything the way the flat one does.

Per-shot views, `shots: [{..., view: NAME or {tilt, yaw, roll, push}}]`:
  descend  from high and oblique down onto the shot's framing (an opening)
  glide    leans in to ~22 deg and drifts its heading across the shot
  lean     a gentle 12 deg lean that keeps writing readable (doc shots)
  low      a low sweeping pass, 50 -> 36 deg with the heading swinging (overviews)
  {tilt: a or [a, b], yaw: ..., roll: ..., push: ...}   eased from a to b over the shot
journey: {focal: 1.15, pulses: [time-expr, ...], pulse: 0.12, dark: 0.35, fog: 0.9}
  focal  pinhole focal length as a multiple of the frame height
  pulses quick punch-ins that ease back (a word that lands)
  dark   how much deeper the light falls off at the desk's edges (a lit stage)
  fog    how fast the far desk sinks into darkness when the camera tilts
"""
import math
import cv2
import numpy as np

from .stage import EASE, Canvas, Stage, Tex, c01, e_oback, lerp, read_at, seg


def affine(M):
    return abs(M[2, 0]) < 1e-12 and abs(M[2, 1]) < 1e-12


def local_scale(M, x, y):
    """Linear scale of a homography at texture point (x, y)."""
    X = M @ np.array([x, y, 1.0]); w = X[2]
    u, v = X[0] / w, X[1] / w
    J = np.array([[M[0, 0] - u * M[2, 0], M[0, 1] - u * M[2, 1]], [M[1, 0] - v * M[2, 0], M[1, 1] - v * M[2, 1]]]) / w
    return math.sqrt(abs(np.linalg.det(J)))


class Canvas3D(Canvas):
    """Canvas that also takes projective matrices (affine ones go through the flat path unchanged)."""

    def pick(self, tex, M, at=None):
        if not isinstance(tex, Tex):
            return tex, M
        h, w = tex.lv[0].shape[:2]
        pts = at or ((w / 2, h / 2), (0, 0), (w, 0), (0, h), (w, h))
        s = float(np.median([local_scale(M, x, y) for x, y in pts]))
        arr, Mf = tex.pick(np.diag([s, s, 1.0]))
        f = Mf[0, 0] / s
        return arr, M @ np.diag([f, f, 1.0])

    def warp(self, tex, M):
        if affine(M):
            return super().warp(tex, M)
        arr, M = self.pick(tex, M)
        h, w = arr.shape[:2]
        P = M @ np.array([[0, w, 0, w], [0, 0, h, h], [1, 1, 1, 1]], float)
        if (P[2] <= 1e-6).any():
            x0, y0, x1, y1 = 0, 0, self.W, self.H
        else:
            px, py = P[0] / P[2], P[1] / P[2]
            x0 = max(0, int(math.floor(px.min())) - 2); x1 = min(self.W, int(math.ceil(px.max())) + 2)
            y0 = max(0, int(math.floor(py.min())) - 2); y1 = min(self.H, int(math.ceil(py.max())) + 2)
        if x1 <= x0 or y1 <= y0:
            return None
        Ms = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1.0]]) @ M
        out = cv2.warpPerspective(arr, Ms, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if out.ndim == 2:
            out = out[..., None]
        return out, (x0, y0, x1, y1)

    def fill_board(self, dst, tex, M):
        if affine(M):
            return super().fill_board(dst, tex, M)
        Mi = np.linalg.inv(M)  # mip from the upper middle of the frame: between near and far
        q = Mi @ np.array([self.W / 2, self.H * 0.3, 1.0]); q = q / q[2]
        arr, M = self.pick(tex, M, at=((q[0], q[1]),))
        out = cv2.warpPerspective(arr, M, (self.W, self.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        if out.dtype == np.uint8:
            np.multiply(out[..., :3], np.float32(1 / 255), out=dst, casting="unsafe")
        else:
            dst[:] = out[..., :3]


def view_curve(view, p, s, dur):
    """(tilt, yaw, roll, push) at shot progress p (0-1), s seconds into a shot of dur seconds."""
    io = EASE["io2"]
    if view == "descend":  # frame 0 is the thumbnail: it starts close enough to read
        q = EASE["io3"](s / max(0.4, min(1.2, 0.6 * dur)))
        return 28 * (1 - q), -14 * (1 - q), 3 * (1 - q), lerp(0.80, 1.0, q)
    if view == "glide":
        return 22 * io(s / 1.2), lerp(-10, 12, p), 0.0, 1 + 0.05 * p
    if view == "lean":
        return 12 * io(s / 0.8), 5 * math.sin(math.pi * p), 0.0, 1.0
    if view == "low":
        q = io(p)
        return lerp(44, 32, q), lerp(-24, 6, q), 0.0, lerp(1.04, 1.14, q)
    if isinstance(view, dict):
        def ab(k, d):
            v = view.get(k, d)
            return (v, v) if not isinstance(v, (list, tuple)) else v
        q = io(p)
        return tuple(lerp(*ab(k, d), q) for k, d in (("tilt", 0.0), ("yaw", 0.0), ("roll", 0.0), ("push", 1.0)))
    return 0.0, 0.0, 0.0, 1.0


class Stage3D(Stage):
    def __init__(self, plan, tl, meta, scale=1.0, lives=None):
        super().__init__(plan, tl, meta, scale, lives)
        self.cv = Canvas3D(self.W, self.H)
        cfg = plan.get("journey") or {}
        self.focal = cfg.get("focal", 1.15) * plan.H  # plan pixels
        self.dark, self.fog = cfg.get("dark", 0.35), cfg.get("fog", 0.9)
        self.pulse_amp = cfg.get("pulse", 0.12)
        self.pulses = sorted(tl.t(e) for e in cfg.get("pulses", []))
        self.scene_caps, self.scene_len = {}, {}
        # which shot each beat came from (layout names are s{k:02d}_{shot}), and each shot's span
        shot_of = {b["name"]: int(b["layout"][1:3]) for b in plan.get("beats", []) if b.get("layout", "")[:1] == "s"}
        self.shot_of, self.spans = {}, {}
        for b in self.beats:
            k = shot_of.get(b["name"])
            self.shot_of[id(b)] = k
            if k is not None:
                a, z = self.spans.get(k, (b["t0"], b["t1"]))
                self.spans[k] = (min(a, b["t0"]), max(z, b["t1"]))

    # ---- scene shots: a full-frame clip (a Blender diorama) in place of the desk
    def render(self, t, fr, rl, t_ink=None):
        sc = self.beat_at(t)["lay"].get("scene")
        if sc:
            return self.scene_frame(sc, t)
        return super().render(t, fr, rl, t_ink)

    def scene_frame(self, sc, t):
        path = sc["clip"]
        if path not in self.scene_len:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                raise SystemExit(f"scene clip missing or unreadable: {path}")
            self.scene_len[path] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.release()
        idx = min(self.scene_len[path] - 1, max(0, int(round((t - sc["t0"] + sc["start"]) * self.fps))))
        img = read_at(self.scene_caps, path, path, idx)
        h, w = img.shape[:2]; s = max(self.W / w, self.H / h)  # cover the frame, centred
        img = cv2.resize(img, (max(self.W, int(round(w * s))), max(self.H, int(round(h * s)))), interpolation=cv2.INTER_AREA)
        y0 = (img.shape[0] - self.H) // 2; x0 = (img.shape[1] - self.W) // 2
        return img[y0:y0 + self.H, x0:x0 + self.W].astype(np.float32) / 255

    # ---- camera
    def view_at(self, t):
        k = self.shot_of.get(id(self.beat_at(t)))
        if k is None:
            return 0.0, 0.0, 0.0, 1.0
        view = self.plan["shots"][k].get("view")
        if not view:
            return 0.0, 0.0, 0.0, 1.0
        a, b = self.spans[k]
        return view_curve(view, seg(t, a, b), t - a, b - a)

    def pulse(self, t):
        g = 0.0
        for tp in self.pulses:
            x = t - tp
            if 0 <= x < 0.07:
                g = max(g, EASE["o3"](x / 0.07))
            elif 0.07 <= x < 1.2:
                g = max(g, math.exp(-(x - 0.07) / 0.16))
        return 1 + self.pulse_amp * g

    def homography(self, cx, cy, z, tilt, yaw, roll):
        """Pinhole camera looking at desk point (cx, cy) with scale z there (plan pixels)."""
        W, H, f = self.plan.W, self.plan.H, self.focal
        D = f / z
        th, ps, ph = math.radians(tilt), math.radians(yaw), math.radians(roll)
        fwd = np.array([math.sin(ps), -math.cos(ps), 0.0])  # screen-up on the desk
        right = np.array([math.cos(ps), math.sin(ps), 0.0])
        zc = math.cos(th) * np.array([0.0, 0.0, 1.0]) + math.sin(th) * fwd  # view axis, into the desk
        y0 = np.cross(zc, right)
        xc = math.cos(ph) * right + math.sin(ph) * y0; yc = -math.sin(ph) * right + math.cos(ph) * y0
        R = np.stack([xc, yc, zc])
        t = -R @ (np.array([cx, cy, 0.0]) - D * zc)
        K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1.0]])
        Hm = K @ np.column_stack([R[:, 0], R[:, 1], t])
        return Hm / Hm[2, 2]  # normalised, so an untilted view is exactly affine (and drawn as one)

    def cam(self, t):
        M, (cx, cy, z) = super().cam(t)
        tilt, yaw, roll, push = self.view_at(t)
        pz = push * self.pulse(t)
        if tilt == 0 and yaw == 0 and roll == 0 and pz == 1:
            return M, (cx, cy, z)
        W, H = self.plan.W, self.plan.H
        S = np.diag([self.scale, self.scale, 1.0])
        base = S @ np.array([[z, 0, W / 2 - z * cx], [0, z, H / 2 - z * cy], [0, 0, 1.0]])
        shake = M @ np.linalg.inv(base)  # the impact shake: an affine in screen space
        return shake @ S @ self.homography(cx, cy, z * pz, tilt, yaw, roll), (cx, cy, z * pz)

    def motion_px(self, t):
        """Screen travel per frame, measured on screen (projective moves are not uniform)."""
        h = 0.5 / self.fps
        if self.beat_at(t - h) is not self.beat_at(t + h):
            return 0.0
        M0, _ = self.cam(t - h); M1, c1 = self.cam(t + h)
        xs, ys = np.meshgrid(np.linspace(0, self.W, 5), np.linspace(0, self.H, 7))
        p = np.stack([xs.ravel(), ys.ravel(), np.ones(xs.size)])
        q = M1 @ np.linalg.inv(M0) @ p
        d = float(np.hypot(q[0] / q[2] - p[0], q[1] / q[2] - p[1]).max())
        for name in self.beat_at(t)["docs"]:
            life = self.lives.get(name, {})
            if life.get("drop") and t >= life.get("appear", -1e9):
                d = max(d, abs(self.drop_offset(t + h, life) - self.drop_offset(t - h, life)) * c1[2] * self.scale)
        return d

    # ---- light
    def light_map(self, M, light):
        lx, ly, sig, lo, hi = light
        lo = lo * (1 - self.dark)  # a lit stage: the light pools on the work, the edges go dark
        X, Y = np.meshgrid(np.arange(0, self.W + 16, 16, dtype=np.float64), np.arange(0, self.H + 16, 16, dtype=np.float64))
        Mi = np.linalg.inv(M)
        Q = Mi @ np.stack([X.ravel(), Y.ravel(), np.ones(X.size)])
        Lx = (Q[0] / Q[2]).reshape(X.shape); Ly = (Q[1] / Q[2]).reshape(X.shape)
        g = np.exp(-((Lx - lx) ** 2 + (Ly - ly) ** 2) / (2 * sig ** 2)).astype(np.float32)
        gain = lo + (hi - lo) * g
        if not affine(M):  # the far desk sinks into darkness: depth of each pixel's desk point
            depth = 1.0 / (Mi[2, 0] * X + Mi[2, 1] * Y + Mi[2, 2])
            c = Mi[2] @ np.array([self.W / 2, self.H / 2, 1.0])
            rel = np.maximum(0.0, depth * c - 1.0)
            gain = gain * np.exp(-self.fog * rel).astype(np.float32)
        tint = np.stack([1 + 0.03 * g - 0.025 * (1 - g), 1 - 0.01 * (1 - g), 1 - 0.045 * g + 0.03 * (1 - g)], -1)
        return cv2.resize(gain[..., None] * tint, (self.W, self.H), interpolation=cv2.INTER_LINEAR)

    def depth_ratio(self, t, step=16):
        """Per-pixel depth over the depth at the frame centre (1 everywhere for a flat camera)."""
        M, _ = self.cam(t)
        if affine(M):
            return None
        Mi = np.linalg.inv(M)
        X, Y = np.meshgrid(np.arange(0, self.W + step, step, dtype=np.float64), np.arange(0, self.H + step, step, dtype=np.float64))
        inv_depth = Mi[2, 0] * X + Mi[2, 1] * Y + Mi[2, 2]
        c = Mi[2] @ np.array([self.W / 2, self.H / 2, 1.0])
        r = (c / inv_depth).astype(np.float32)
        return cv2.resize(r, (self.W, self.H), interpolation=cv2.INTER_LINEAR)
