#!/usr/bin/env python3
"""Camera grade, analog finish and print treatments for talking-head edits.

Import into a frame renderer (numpy RGB uint8 in, uint8 out) or run on files:
  look.py still IN.png OUT.png [--grade --track track.json --t 3.2] [--finish medium]
  look.py video IN.mp4 OUT.mp4 [--grade --track track.json] [--finish medium]
  look.py print IN.png OUT.png --mode halftone|xerox [--cell 7]

Order inside a renderer: grade_webcam(camera crop) -> composite graphics ->
finish(whole frame, frame_index). Print treatments go on photos and cutouts
only, never on the face. The finish is the glue that makes paper, photos,
type and camera read as one physical object; it must never lift the blacks.
"""
import argparse, json, math, subprocess, sys
from pathlib import Path
import cv2
import numpy as np

PRESETS = {  # grain, halation, bloom, weave_px, ca, vignette
    "subtle": dict(grain=0.016, halation=0.10, bloom=0.05, weave=0.35, ca=0.0008, vignette=0.18),
    "medium": dict(grain=0.026, halation=0.16, bloom=0.07, weave=0.60, ca=0.0014, vignette=0.26),
    "heavy":  dict(grain=0.040, halation=0.24, bloom=0.10, weave=0.90, ca=0.0022, vignette=0.34),
}


def _f(img):
    return img.astype(np.float32) / 255.0


def _u8(x):
    return (np.clip(x, 0, 1) * 255.0 + 0.5).astype(np.uint8)


def _luma(x):
    return x[..., 0] * 0.2126 + x[..., 1] * 0.7152 + x[..., 2] * 0.0722


def _shoulder(x, knee=0.72):
    """Film-like highlight rolloff: linear below knee, asymptotic to 1 above."""
    o = np.maximum(x - knee, 0)
    return np.where(x > knee, knee + o / (1 + o / (1 - knee)), x)


def grade_webcam(rgb, face=None, wb=(-0.06, 0.0, 0.05), contrast=0.30, relight=0.25,
                 bg_dim=0.50, sat=0.92, sharpen=0.45):
    """Tungsten webcam -> clean, contrasty, face-forward.
    face: (center_x, eye_y, face_width) in this image's pixels (see face_track.Track.at),
    used for a soft relight: + `relight` stops on the face, - `bg_dim` stops on the room."""
    x = _f(rgb)
    if sharpen:
        bl = cv2.GaussianBlur(x, (0, 0), max(0.8, x.shape[1] / 1100))
        x = x + sharpen * (x - bl)
    x *= np.array([1 + wb[0], 1 + wb[1], 1 + wb[2]], np.float32)
    if face is not None:
        h, w = x.shape[:2]
        cx, ey, fw = face
        k = 8  # the mask is smooth: build it at 1/8 size, then upscale
        yy, xx = np.mgrid[0:max(2, h // k), 0:max(2, w // k)].astype(np.float32) * k
        m = np.exp(-(((xx - cx) / (0.95 * fw)) ** 2 + ((yy - (ey + 0.30 * fw)) / (1.25 * fw)) ** 2))
        m = cv2.GaussianBlur(m, (0, 0), max(1.0, fw * 0.15 / k))
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)
        x *= np.exp2(relight * m - bg_dim * (1 - m))[..., None]
    x = np.clip(_shoulder(x), 0, 1)
    s = x * x * (3 - 2 * x)
    x = x + contrast * (s - x)
    l = _luma(x)[..., None]
    return _u8(l + sat * (x - l))


class Finish:
    """Film/print finish for full output frames. Deterministic per frame index."""

    def __init__(self, width, height, preset="medium", seed=7, **over):
        p = dict(PRESETS[preset]); p.update(over); self.p = p
        self.w, self.h = width, height
        rng = np.random.default_rng(seed)
        bank = []
        for _ in range(12):  # two-scale grain, unit std
            fine = cv2.GaussianBlur(rng.standard_normal((height, width)).astype(np.float32), (0, 0), 0.7)
            coarse = cv2.GaussianBlur(rng.standard_normal((height // 2, width // 2)).astype(np.float32), (0, 0), 1.0)
            coarse = cv2.resize(coarse, (width, height), interpolation=cv2.INTER_CUBIC)
            g = 0.85 * fine / fine.std() + 0.35 * coarse / coarse.std()
            bank.append(g / g.std())
        # padded by wrapping, so a per-frame offset is a slice (a view), not a full-frame np.roll copy
        self.bank = [np.pad(g, ((0, 128), (0, 128)), mode="wrap") for g in bank]
        yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
        r = np.sqrt(((xx - width / 2) / (width / 2)) ** 2 + ((yy - height / 2) / (height / 2)) ** 2) / math.sqrt(2)
        self.vig = (1 - p["vignette"] * np.clip(r, 0, 1) ** 2.2)[..., None]
        self.walk = rng.standard_normal((4096, 3)).astype(np.float32)

    def _weave(self, i):
        # smooth random walk, roughly 0..1 px; on 2s like a projector gate
        k = (i // 2) % 4000
        v = self.walk[k:k + 8].mean(0)
        return v[0] * self.p["weave"], v[1] * self.p["weave"], v[2] * 0.03

    def apply(self, rgb, i=0):
        """uint8 or float32 (0..1) RGB in, uint8 out. OpenCV ops throughout: no full-frame
        numpy temporaries (about 4x faster than the broadcasting version, same look)."""
        p = self.p; x = rgb if rgb.dtype == np.float32 else _f(rgb); h, w = x.shape[:2]
        # halation (red-orange, wide) + bloom (neutral, tight) from highlights only, built at 1/4 size
        small = cv2.resize(x, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
        hi = np.clip((_luma(small) - 0.70) / 0.30, 0, 1) ** 1.5
        hal = cv2.GaussianBlur(hi, (0, 0), w / 4 * 0.022) * p["halation"]
        blo = cv2.GaussianBlur(hi, (0, 0), w / 4 * 0.006) * p["bloom"]
        glow = cv2.merge([hal * 1.0 + blo, hal * 0.42 + blo, hal * 0.22 + blo])
        x = cv2.add(x, cv2.resize(glow, (w, h), interpolation=cv2.INTER_LINEAR))
        # gate weave and radial chromatic aberration in one warp per channel
        # (red scaled out, blue scaled in about the centre, all three on the same weave)
        dx, dy, rot = self._weave(i)
        chans = []
        for c, sc in ((0, 1 + p["ca"]), (1, 1.0), (2, 1 - p["ca"])):
            M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, sc); M[0, 2] += dx; M[1, 2] += dy
            chans.append(cv2.warpAffine(np.ascontiguousarray(x[..., c]), M, (w, h), flags=cv2.INTER_LINEAR,
                                        borderMode=cv2.BORDER_REFLECT))
        if not hasattr(self, "vig3"):
            self.vig3 = np.ascontiguousarray(np.repeat(self.vig, 3, axis=2))
        x = cv2.multiply(cv2.merge(chans), self.vig3)
        # luminance-weighted grain: strongest in mids, ~0 in deep black so blacks don't lift
        L = np.clip(cv2.transform(x, np.array([[0.2126, 0.7152, 0.0722]], np.float32)), 0, 1)
        amp = p["grain"] * (np.minimum(L * 10.0, 1.0) * (0.35 + 2.6 * L * (1 - L)))
        oy, ox = (i * 37) % 128, (i * 91) % 128
        ga = self.bank[(i * 5) % len(self.bank)][oy:oy + h, ox:ox + w] * amp
        x = cv2.add(x, cv2.merge([ga, ga * 0.97, ga * 1.04]))
        return cv2.convertScaleAbs(cv2.max(x, 0.0), alpha=255.0)


# ---------- print treatments for photos, cutouts and graphics (not the face) ----------

def halftone(rgb, cell=7, angle=22.0, ink=(22, 20, 18), paper=(234, 226, 212), contrast=1.15):
    """Mono halftone screen. cell = dot pitch in px at output size (6-9 reads at 1080 wide)."""
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    g = np.clip((g - 0.5) * contrast + 0.5, 0, 1)
    dark = cv2.GaussianBlur(1 - g, (0, 0), cell * 0.35)
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(angle)
    u = xx * math.cos(a) + yy * math.sin(a); v = -xx * math.sin(a) + yy * math.cos(a)
    du = (u / cell) % 1.0 - 0.5; dv = (v / cell) % 1.0 - 0.5
    d = np.sqrt(du * du + dv * dv) * cell
    r = np.sqrt(np.clip(dark, 0, 1)) * cell * 0.62
    m = np.clip(r - d + 0.5, 0, 1)[..., None]  # 1 px antialias
    out = np.array(paper, np.float32) * (1 - m) + np.array(ink, np.float32) * m
    return out.astype(np.uint8)


def xerox(rgb, seed=3, crush=0.28, toner=0.10):
    """Photocopy: crushed tones, toner speckle, slight smear. Good for cutouts and evidence."""
    rng = np.random.default_rng(seed)
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    g = np.clip((g - crush) / (1 - 2 * crush), 0, 1)
    g = g * g * (3 - 2 * g)
    n = cv2.GaussianBlur(rng.standard_normal(g.shape).astype(np.float32), (0, 0), 0.8)
    g = np.clip(g + toner * n * (1 - g) * 2, 0, 1)
    g = cv2.GaussianBlur(g, (0, 0), 0.6)
    return cv2.cvtColor((g * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)


def misregister(rgb, shift=(1.5, -1.0)):
    """Offset the red and blue plates like a cheap press. 1-2 px at 1080 wide."""
    out = rgb.copy()
    out[..., 0] = np.roll(rgb[..., 0], (int(round(shift[1])), int(round(shift[0]))), (0, 1))
    out[..., 2] = np.roll(rgb[..., 2], (-int(round(shift[1])), -int(round(shift[0]))), (0, 1))
    return out


def paper(width, height, seed=11, base=(233, 225, 211), relief=0.05, fibres=260):
    """Procedural paper: equal-weight octaves (no blotches), raking light, fibres.
    Prefer a real scan or a generated texture when one exists; this is the fallback."""
    rng = np.random.default_rng(seed)
    hgt = np.zeros((height, width), np.float32)
    for o in range(7):  # flat slope spectrum: each octave contributes the same slope
        s = 2 ** o
        n = rng.standard_normal((max(2, height // s), max(2, width // s))).astype(np.float32)
        n = cv2.resize(cv2.GaussianBlur(n, (0, 0), 1.0), (width, height), interpolation=cv2.INTER_CUBIC)
        hgt += n * s
    hgt /= np.abs(hgt).max()
    gy, gx = np.gradient(hgt * 40)
    shade = 1 + relief * (-0.7 * gx - 0.7 * gy) / (np.abs(gx).std() + np.abs(gy).std() + 1e-6)
    tone = 1 + 0.025 * cv2.GaussianBlur(rng.standard_normal((height, width)).astype(np.float32), (0, 0), width * 0.08) / 0.01
    img = np.array(base, np.float32)[None, None, :] * np.clip(shade * np.clip(tone, 0.94, 1.04), 0.85, 1.1)[..., None]
    lay = np.zeros((height, width), np.float32)
    for _ in range(fibres):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        ang = rng.uniform(0, math.pi); L = rng.uniform(8, 40)
        pts = []
        for k in range(6):
            ang += rng.normal(0, 0.25)
            x += math.cos(ang) * L / 6; y += math.sin(ang) * L / 6
            pts.append((int(x), int(y)))
        cv2.polylines(lay, [np.array(pts, np.int32)], False, float(rng.uniform(0.3, 1.0)), 1, cv2.LINE_AA)
    img *= (1 - 0.06 * cv2.GaussianBlur(lay, (0, 0), 0.5))[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)


# ---------- CLI ----------

def _face_at(track, t, crop=None):
    sys.path.insert(0, str(Path(__file__).parent))
    from face_track import Track
    tr = Track.load(track); cx, ey, fw = tr.at(t)
    return (cx, ey, fw)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("still", "video"):
        s = sub.add_parser(name); s.add_argument("inp"); s.add_argument("out")
        s.add_argument("--grade", action="store_true"); s.add_argument("--track")
        s.add_argument("--t", type=float, default=0.0); s.add_argument("--finish", choices=list(PRESETS))
        s.add_argument("--frame-index", type=int, default=0); s.add_argument("--crf", type=int, default=16)
    s = sub.add_parser("print"); s.add_argument("inp"); s.add_argument("out")
    s.add_argument("--mode", choices=["halftone", "xerox"], default="halftone"); s.add_argument("--cell", type=int, default=7)
    a = ap.parse_args()

    if a.cmd == "print":
        img = cv2.cvtColor(cv2.imread(a.inp), cv2.COLOR_BGR2RGB)
        out = halftone(img, a.cell) if a.mode == "halftone" else xerox(img)
        cv2.imwrite(a.out, cv2.cvtColor(out, cv2.COLOR_RGB2BGR)); return

    if a.cmd == "still":
        img = cv2.cvtColor(cv2.imread(a.inp), cv2.COLOR_BGR2RGB)
        if a.grade:
            img = grade_webcam(img, _face_at(a.track, a.t) if a.track else None)
        if a.finish:
            img = Finish(img.shape[1], img.shape[0], a.finish).apply(img, a.frame_index)
        cv2.imwrite(a.out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR)); return

    # video: decode -> grade/finish -> encode, audio copied
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height,r_frame_rate", "-of", "json", a.inp],
                                   capture_output=True, text=True).stdout)["streams"][0]
    w, h = pr["width"], pr["height"]; fr = pr["r_frame_rate"]
    num, den = fr.split("/"); fps = float(num) / float(den)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.inp, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                            "-r", fr, "-i", "-", "-i", a.inp, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264",
                            "-preset", "medium", "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-c:a", "copy",
                            "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    fin = Finish(w, h, a.finish) if a.finish else None
    tr = None
    if a.grade and a.track:
        sys.path.insert(0, str(Path(__file__).parent)); from face_track import Track; tr = Track.load(a.track)
    i = 0
    while True:
        buf = dec.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            break
        img = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        if a.grade:
            img = grade_webcam(img, tuple(tr.at(i / fps)) if tr else None)
        if fin:
            img = fin.apply(img, i)
        enc.stdin.write(img.tobytes()); i += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print(f"wrote {a.out}: {i} frames")


if __name__ == "__main__":
    main()
