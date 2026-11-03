"""Journeys: plane changes between shots, depth of field and an optional monochrome stage.

A shot with `via:` arrives through a plane change instead of a cut. The last frame
of the outgoing shot becomes a card in 3D and leaves; the incoming shot plays live.
  fall    the old plane hinges at its foot and falls away into the dark (0.55 s)
  dive    the camera falls through the old plane into the next one below (0.6 s)
  travel  a lateral whip: the old plane swings out, the next swings in (0.42 s)
  flip    the plane turns over and the next shot is on its back (0.5 s)
  cut     a plain cut (the default)
`via_dur` overrides the length. Each transition is motion-blurred across the shutter.

journey: {dof: 1.0, mono: false}
  dof   depth-of-field strength when the camera tilts (0 turns it off)
  mono  a black-and-white stage with one accent: the presenter print, films and the
        vermilion ink keep their colour (a lit diorama)
"""
import math
import cv2
import numpy as np

from .stage import EASE, VERMILION, c01, lerp

DUR = {"fall": 0.55, "dive": 0.6, "travel": 0.42, "flip": 0.5}


def ease_in(x, p=2.2):
    return c01(x) ** p


class Journey:
    def __init__(self, plan, stage):
        self.plan, self.st = plan, stage
        cfg = plan.get("journey") or {}
        self.dof_k, self.mono = cfg.get("dof", 1.0), cfg.get("mono", False)
        W, H = stage.W, stage.H
        self.W, self.H, self.f = W, H, stage.focal * stage.scale
        self.ones = np.ones((H, W), np.float32)
        self.trans = []
        for k, s in enumerate(plan.get("shots", [])):
            kind = s.get("via", "cut")
            if kind == "cut" or k not in stage.spans:
                continue
            t0 = stage.spans[k][0]
            prev = [b for b in stage.beats if b["t1"] <= t0 + 1e-6]
            if not prev:
                continue
            self.trans.append(dict(kind=kind, t0=t0, dur=s.get("via_dur", DUR[kind]), t_out=max(prev[-1]["t0"], t0 - 1 / stage.fps)))
        self.frozen = {}

    # ---- the finished stage frame: depth of field and grade
    def grade(self, img, t):
        st = self.st
        if self.dof_k > 0:
            r = st.depth_ratio(t)
            if r is not None:
                img = self.dof(img, r)
        if self.mono:
            img = self.monochrome(img, t)
        return img

    def dof(self, img, r):
        """Blur by distance from the focus plane (the frame centre), in two levels."""
        A = 9.0 * self.dof_k * self.W / 1080
        coc = np.clip(A * np.abs(1 - 1 / np.maximum(r, 1e-3)), 0, A)
        if coc.max() < 0.6:
            return img
        small = cv2.resize(img, (self.W // 2, self.H // 2), interpolation=cv2.INTER_AREA)
        b1 = cv2.resize(cv2.GaussianBlur(small, (0, 0), A / 6), (self.W, self.H), interpolation=cv2.INTER_LINEAR)
        b2 = cv2.resize(cv2.GaussianBlur(small, (0, 0), A / 2), (self.W, self.H), interpolation=cv2.INTER_LINEAR)
        w = (coc / A)[..., None]
        w1 = np.clip(w / 0.35, 0, 1); w2 = np.clip((w - 0.35) / 0.65, 0, 1)
        return img * (1 - w1) + (b1 * (1 - w2) + b2 * w2) * w1

    def monochrome(self, img, t):
        """Grey stage, colour only where it means something: his print, films, the accent ink."""
        st = self.st; b = st.beat_at(t); lay = b["lay"]; M, _ = st.cam(t)
        if "scene" in lay:  # a scene is art-directed in its own palette
            return img
        keep = np.zeros((self.H, self.W), np.float32)
        names = (["presenter"] if "presenter" in lay else []) + [f"film:{i}" for i in range(len(b["films"]))]
        placed = st.lay_docs(lay)
        shown = [n for n in b["docs"] if n in placed and st.docs[n].state(t, st.lives.get(n, {}), st.fps) is not None]
        for name, v in [(n, 1.0) for n in names] + [(n, 0.0) for n in shown]:
            pts = np.array(st.corners(lay, name), float)  # paper is drawn over the prints: it stays grey
            q = M @ np.column_stack([pts, np.ones(len(pts))]).T
            poly = np.round(np.stack([q[0] / q[2], q[1] / q[2]], 1)).astype(np.int32)
            cv2.fillConvexPoly(keep, poly[[0, 1, 3, 2]], v, cv2.LINE_AA)
        hsv = cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_RGB2HSV)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        hv = cv2.cvtColor(VERMILION[None, None, :], cv2.COLOR_RGB2HSV)[0, 0, 0]
        dh = np.minimum(np.abs(h - hv), 360 - np.abs(h - hv))
        ink = np.clip((s - 0.45) / 0.2, 0, 1) * np.clip((14 - dh) / 6, 0, 1)
        keep = np.maximum(cv2.GaussianBlur(keep, (0, 0), 1.5), ink)[..., None]
        grey = (img @ np.array([0.30, 0.59, 0.11], np.float32))[..., None]
        grey = np.clip((grey - 0.5) * 1.12 + 0.5, 0, 1)  # a little more contrast in the paper world
        return img * keep + np.repeat(grey, 3, 2) * (1 - keep)

    # ---- plane changes
    def active(self, t):
        for tr in self.trans:
            if tr["t0"] <= t < tr["t0"] + tr["dur"]:
                return tr
        return None

    def outgoing(self, tr):
        key = tr["t0"]
        if key not in self.frozen:
            st = self.st; t = tr["t_out"]
            rl = st.footage.map(t)
            img = np.clip(st.render(t, st.footage.frame(*rl), rl), 0, 1)
            self.frozen = {key: self.grade(img, t)}  # one transition at a time per worker
        return self.frozen[key]

    def project(self, pts):
        """Camera-space points (x right, y down, z forward; the frame sits at z = f) -> screen."""
        f = self.f
        return np.float32([[f * x / z + self.W / 2, f * y / z + self.H / 2] for x, y, z in pts])

    def card(self, img, pts, shade=1.0):
        """Warp a full frame onto a projected quad. Returns (premultiplied rgb, alpha)."""
        src = np.float32([[0, 0], [self.W, 0], [self.W, self.H], [0, self.H]])
        Hm = cv2.getPerspectiveTransform(src, self.project(pts))
        a = cv2.warpPerspective(self.ones, Hm, (self.W, self.H), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
        rgb = cv2.warpPerspective(img, Hm, (self.W, self.H), flags=cv2.INTER_LINEAR, borderValue=0) * shade
        return rgb, a

    def corners(self, rot_x=0.0, rot_y=0.0, pivot=(0.0, 0.0, None), move=(0.0, 0.0, 0.0), roll=0.0):
        """The frame's corners in camera space after a rotation about a pivot and a move."""
        w, h, f = self.W / 2, self.H / 2, self.f
        px, py, pz = pivot[0], pivot[1], (f if pivot[2] is None else pivot[2])
        out = []
        for x, y in ((-w, -h), (w, -h), (w, h), (-w, h)):
            x, y, z = x - px, y - py, f - pz
            c, s = math.cos(roll), math.sin(roll); x, y = c * x - s * y, s * x + c * y
            c, s = math.cos(rot_x), math.sin(rot_x); y, z = c * y - s * z, s * y + c * z
            c, s = math.cos(rot_y), math.sin(rot_y); x, z = c * x + s * z, -s * x + c * z
            out.append((x + px + move[0], y + py + move[1], z + pz + move[2]))
        return out

    def composite(self, kind, u, out, inc):
        f, W, H = self.f, self.W, self.H
        if kind == "fall":  # hinged at its foot, the old plane falls back and away; the next is beneath it
            a = math.radians(84) * ease_in(u)
            drop = ease_in(u, 2.6)
            pts = self.corners(rot_x=-a, pivot=(0, H / 2, None), move=(0, 0.3 * H * drop, 0.9 * H * drop))
            s = lerp(1.06, 1.0, EASE["o3"](u))
            base = cv2.warpAffine(inc, np.float32([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]]), (W, H),
                                  borderMode=cv2.BORDER_REFLECT_101) * (1 - 0.45 * (1 - u) ** 2)
            rgb, al = self.card(out, pts, 0.3 + 0.7 * math.cos(a))
            al = al * (1 - c01((u - 0.78) / 0.22))
            return base * (1 - al) + rgb * (1 - c01((u - 0.78) / 0.22))
        if kind == "dive":  # through the old plane and down onto the next
            e = ease_in(c01(u / 0.55), 2.0)
            z_out = f * (1 - 0.72 * e)
            fade = 1 - c01((u - 0.22) / 0.3)  # gone by u = 0.52: never a double exposure for long
            q = EASE["io2"](c01((u - 0.2) / 0.8))
            z_in = f * lerp(1.8, 1.0, q)
            base, _ = self.card(inc, self.corners(roll=math.radians(7) * (1 - q), move=(0, 0, z_in - f)), lerp(0.4, 1.0, q))
            if fade <= 0:
                return base
            rgb, al = self.card(out, self.corners(move=(0, 0, z_out - f)))
            return base * (1 - al * fade) + rgb * fade
        if kind == "travel":  # a whip across: the old plane swings out left, the next swings in from the right
            e = EASE["io3"](u)
            o = self.corners(rot_y=math.radians(-20) * e, move=(-1.25 * W * e, 0, 0.18 * H * math.sin(math.pi * e)))
            i = self.corners(rot_y=math.radians(20) * (1 - e), move=(1.25 * W * (1 - e), 0, 0.18 * H * math.sin(math.pi * e)))
            r1, a1 = self.card(out, o, 0.85 + 0.15 * (1 - e)); r2, a2 = self.card(inc, i, 0.85 + 0.15 * e)
            return r2 + r1 * (1 - a2)  # (they never overlap much; incoming on top)
        if kind == "flip":  # the plane turns over; the next shot is on its back
            b = math.pi * EASE["io3"](u)
            lift = (0, 0, 0.35 * f * math.sin(b))
            if b < math.pi / 2:
                rgb, _ = self.card(out, self.corners(rot_y=b, move=lift), 0.35 + 0.65 * math.cos(b))
            else:
                rgb, _ = self.card(inc, self.corners(rot_y=b - math.pi, move=lift), 0.35 + 0.65 * math.cos(math.pi - b))
            return rgb
        return inc

    def post(self, img, t):
        """The finished stage frame at t: graded, and inside a plane change if one is running."""
        img = self.grade(img, t)
        tr = self.active(t)
        if not tr:
            return img
        out = self.outgoing(tr); fps = self.st.fps
        n = {"travel": 28, "dive": 18, "fall": 14, "flip": 14}.get(tr["kind"], 10)
        acc = None
        for k in range(n):  # a 216-degree shutter across the move
            ts = t + (k / (n - 1) - 0.5) * 0.6 / fps
            c = self.composite(tr["kind"], c01((ts - tr["t0"]) / tr["dur"]), out, img)
            acc = c if acc is None else acc + c
        return np.clip(acc / n, 0, 1)
