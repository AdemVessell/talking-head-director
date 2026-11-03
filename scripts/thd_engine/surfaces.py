"""Desk surfaces under the paper, one per treatment (treatments.py maps subjects to them).

  charcoal  painted fibreboard        evidence, costs, verdicts (the house default)
  cork      pinboard                  planning, ideas, research, lists
  kraft     brown wrapping paper      making, products, unboxing, craft
  mat       green cutting mat         workshop, gear, builds, how-to
  walnut    dark wood desk            studio, music, writing, personal
  linen     indigo bookcloth          reflection, quotes, calm explainers
  slate     chalkboard                teaching, definitions, maths

Each is generated once (2600 x 3400, seeded) and cached in ~/.cache/thd_engine.
"""
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

from .texture import fbm, noise

SIZE = (2600, 3400)
CACHE = Path.home() / ".cache" / "thd_engine"
VERSION = 2


def _n(a):
    return a / (np.abs(a).max() + 1e-6)


def _scratches(h, w, rng, n, ang_mu, ang_sd, lmin, lmax, straight=False):
    lay = np.zeros((h, w), np.float32)
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        ang = (rng.choice([0, math.pi / 2]) + rng.normal(0, 0.01)) if straight else rng.normal(ang_mu, ang_sd)
        L = rng.uniform(lmin, lmax)
        cv2.line(lay, (int(x), int(y)), (int(x + math.cos(ang) * L), int(y + math.sin(ang) * L)),
                 float(rng.uniform(0.25, 1.0)), 1, cv2.LINE_AA)
    return cv2.GaussianBlur(lay, (0, 0), 0.6)


def charcoal(w, h, seed=5):
    """Charcoal pinboard/desk: mottled paint over fibreboard, scratches, old pin holes, tape ghosts."""
    rng = np.random.default_rng(seed)
    base = np.array([47, 44, 40], np.float32)
    mott = fbm(h, w, seed, octaves=5, base=3, falloff=0.55)
    fib = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), sigmaX=2.2, sigmaY=0.6)
    fine = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 0.8)
    lum = 1 + 0.13 * mott / (np.abs(mott).max() + 1e-6) + 0.05 * fib / fib.std() + 0.04 * fine / fine.std()
    img = base[None, None, :] * lum[..., None]
    lay = np.zeros((h, w), np.float32)
    for _ in range(420):  # fine scratches, slightly lighter, mostly one direction like a used desk
        x, y = rng.uniform(0, w), rng.uniform(0, h); ang = rng.normal(0.25, 0.5); L = rng.uniform(20, 260)
        x2, y2 = x + math.cos(ang) * L, y + math.sin(ang) * L
        cv2.line(lay, (int(x), int(y)), (int(x2), int(y2)), float(rng.uniform(0.25, 1.0)), 1, cv2.LINE_AA)
    img += 18 * cv2.GaussianBlur(lay, (0, 0), 0.6)[..., None]
    for _ in range(70):  # pin holes from earlier evidence
        x, y = int(rng.uniform(0, w)), int(rng.uniform(0, h)); r = int(rng.uniform(2, 4))
        cv2.circle(img, (x, y), r + 2, (48, 45, 41), -1, cv2.LINE_AA); cv2.circle(img, (x, y), r, (12, 11, 10), -1, cv2.LINE_AA)
    ghost = np.zeros((h, w), np.float32)
    for _ in range(26):  # faint tape ghosts (adhesive residue holds dust)
        cx, cy = rng.uniform(0, w), rng.uniform(0, h); tw, th = rng.uniform(120, 220), rng.uniform(36, 56)
        box = cv2.boxPoints(((cx, cy), (tw, th), rng.uniform(-50, 50))).astype(np.int32)
        cv2.fillPoly(ghost, [box], 1.0)
    ghost = cv2.GaussianBlur(ghost, (0, 0), 3) * (0.6 + 0.4 * (fbm(h, w, seed + 9, 4, 8) > -0.1))
    img = img * (1 + 0.10 * ghost[..., None]) + ghost[..., None] * np.array([6, 5, 2], np.float32)
    dust = (rng.random((h, w)) > 0.99965).astype(np.float32)
    img += 60 * cv2.GaussianBlur(dust, (0, 0), 0.7)[..., None]
    return img


def cork(w, h, seed=7):
    """Pinboard cork: crisp granules of mixed tone, dark pores, old pin holes."""
    rng = np.random.default_rng(seed)
    base = np.array([176, 128, 84], np.float32)
    small = np.tanh(noise(h, w, rng, 1.6) * 1.4); big = np.tanh(noise(h, w, rng, 4.5) * 1.2)
    mott = _n(fbm(h, w, seed, 5, 3, 0.55))
    lum = 1 + 0.07 * small + 0.08 * big + 0.06 * mott
    hue = noise(h, w, rng, 3.5)
    img = base * lum[..., None] * np.stack([1 + 0.03 * hue, 1 - 0.01 * hue, 1 - 0.07 * hue], -1)
    pores = (rng.random((h, w)) > 0.9955).astype(np.float32)
    pores = cv2.GaussianBlur(cv2.dilate(pores, np.ones((2, 2), np.uint8)), (0, 0), 1.0)
    img *= (1 - 0.3 * np.clip(pores * 2, 0, 1))[..., None]
    for _ in range(110):
        x, y = int(rng.uniform(0, w)), int(rng.uniform(0, h))
        cv2.circle(img, (x, y), int(rng.uniform(2, 4)), (52, 34, 22), -1, cv2.LINE_AA)
    return img


def kraft(w, h, seed=9):
    """Brown kraft paper: long fibres, mottling, a few big soft wrinkles."""
    rng = np.random.default_rng(seed)
    base = np.array([168, 128, 86], np.float32)
    mott = _n(fbm(h, w, seed, 6, 3, 0.6))
    lum = 1 + 0.06 * mott + 0.025 * noise(h, w, rng, 0.9)
    lay = _scratches(h, w, rng, int(w * h / 500), 0, math.pi, 8, 60)
    dark = _scratches(h, w, rng, int(w * h / 900), 0, math.pi, 6, 40)
    lum += 0.10 * lay - 0.12 * dark
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for _ in range(16):  # short wrinkles: a soft ridge, light on one side, shade on the other
        cx, cy = rng.uniform(0, w), rng.uniform(0, h); ang = rng.uniform(0, math.pi); wd = rng.uniform(8, 22)
        L = rng.uniform(200, 700); amp = rng.uniform(0.015, 0.035)
        u = (xx - cx) * math.cos(ang) + (yy - cy) * math.sin(ang)
        d = (-(xx - cx) * math.sin(ang) + (yy - cy) * math.cos(ang)) / wd
        env = np.exp(-(u / L) ** 4)
        lum *= 1 + env * (amp * np.exp(-(d + 0.5) ** 2) - 1.2 * amp * np.exp(-(d - 0.6) ** 2))
    return base * lum[..., None]


def mat(w, h, seed=11):
    """Green self-healing cutting mat: 1 cm grid, heavy every 5 cm, 45-degree guides, knife scores."""
    rng = np.random.default_rng(seed)
    base = np.array([36, 82, 68], np.float32)
    lum = 1 + 0.035 * _n(fbm(h, w, seed, 5, 3, 0.55)) + 0.02 * noise(h, w, rng, 0.8)
    img = base * lum[..., None]
    grid = np.zeros((h, w), np.float32)
    for k in range(0, max(w, h), 60):
        heavy = k % 300 == 0; v = 0.55 if heavy else 0.26; t = 3 if heavy else 1
        cv2.line(grid, (k, 0), (k, h), v, t, cv2.LINE_AA); cv2.line(grid, (0, k), (w, k), v, t, cv2.LINE_AA)
    for k in range(-h, w, 900):  # 45-degree guides
        cv2.line(grid, (k, 0), (k + h, h), 0.22, 2, cv2.LINE_AA)
    grid = cv2.GaussianBlur(grid, (0, 0), 0.5)
    ink = np.array([196, 222, 206], np.float32)
    img = img * (1 - grid[..., None]) + ink * grid[..., None]
    cuts = _scratches(h, w, rng, 360, 0, 0, 40, 700, straight=True)
    img = img * (1 - 0.35 * cuts[..., None]) + np.array([92, 140, 120], np.float32) * 0.35 * cuts[..., None]
    return img


def walnut(w, h, seed=13):
    """Dark walnut desk: planks with figured grain, pores, satin finish."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w, 3), np.float32)
    y0 = 0; k = 0
    while y0 < h:
        ph = int(rng.uniform(460, 620)); y1 = min(h, y0 + ph); hh = y1 - y0
        yy, xx = np.mgrid[0:hh, 0:w].astype(np.float32)
        warp = fbm(hh, w, seed + 10 * k, 4, 2, 0.55) * rng.uniform(60, 120) + 0.04 * xx * rng.normal(0, 0.4)
        period = rng.uniform(16, 30)
        rings = (0.5 + 0.5 * np.sin(2 * np.pi * (yy + warp) / period)) ** 5
        streak = noise(hh, w, rng, 60, 1.4)
        fine = noise(hh, w, rng, 12, 0.6)
        tone = rng.uniform(0.9, 1.1)
        lum = tone * (1 - 0.22 * rings + 0.06 * streak + 0.05 * fine)
        dark = np.array([70, 44, 28], np.float32); light = np.array([118, 80, 52], np.float32)
        mix = np.clip(0.45 + 0.25 * _n(fbm(hh, w, seed + 7 + k, 3, 2)), 0, 1)[..., None]
        pl = (dark * (1 - mix) + light * mix) * lum[..., None]
        pores = (rng.random((hh, w)) > 0.9975).astype(np.float32)
        pores = cv2.GaussianBlur(cv2.dilate(pores, np.ones((1, 4), np.uint8)), (0, 0), 0.8)
        pl *= (1 - 0.28 * np.clip(pores * 2, 0, 1))[..., None]
        pl[:3] *= 0.55; pl[3:5] *= 1.06  # the seam between planks
        out[y0:y1] = pl[:hh]
        y0 = y1; k += 1
    sheen = 1 + 0.05 * _n(fbm(h, w, seed + 99, 3, 2))
    return out * sheen[..., None]


def linen(w, h, seed=15):
    """Indigo bookbinding cloth: a fine plain weave with slubs."""
    rng = np.random.default_rng(seed)
    base = np.array([50, 58, 78], np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    slub_x = noise(h, w, rng, 40, 0.8); slub_y = noise(h, w, rng, 0.8, 40)
    wx = (0.5 + 0.5 * np.sin(2 * np.pi * xx / 5.2)) * (1 + 0.3 * slub_y)
    wy = (0.5 + 0.5 * np.sin(2 * np.pi * yy / 5.2)) * (1 + 0.3 * slub_x)
    check = (np.sin(np.pi * xx / 5.2) * np.sin(np.pi * yy / 5.2) > 0).astype(np.float32)
    weave = check * wx + (1 - check) * wy
    lum = 1 + 0.10 * (weave - 0.5) + 0.05 * _n(fbm(h, w, seed, 5, 3, 0.55)) + 0.02 * noise(h, w, rng, 0.7)
    return base * lum[..., None]


def slate(w, h, seed=17):
    """Chalkboard: dark green-black slate, chalk dust, eraser swipes, ghosts of old writing."""
    rng = np.random.default_rng(seed)
    base = np.array([38, 46, 43], np.float32)
    lum = 1 + 0.06 * _n(fbm(h, w, seed, 5, 3, 0.55)) + 0.025 * noise(h, w, rng, 0.8)
    img = base * lum[..., None]
    dust = np.clip(_n(fbm(h, w, seed + 3, 6, 4, 0.7)) - 0.1, 0, 1) * 0.10
    swipe = np.zeros((h, w), np.float32)
    for _ in range(40):  # eraser strokes: broad, mostly horizontal, overlapping
        x, y = rng.uniform(-200, w), rng.uniform(0, h); L = rng.uniform(400, 1200); ang = rng.normal(0, 0.12)
        cv2.line(swipe, (int(x), int(y)), (int(x + L * math.cos(ang)), int(y + L * math.sin(ang))),
                 float(rng.uniform(0.3, 1)), int(rng.uniform(90, 150)), cv2.LINE_AA)
    swipe = cv2.GaussianBlur(swipe, (0, 0), 14) * 0.05 * (0.6 + 0.4 * (noise(h, w, rng, 3) > 0))
    from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
    gi = _I.new("L", (w, h), 0); gd = _D.Draw(gi)
    words = ["x = 2y + 1", "f(x)", "area = pi r^2", "THEREFORE", "a + b", "why?", "1/2", "slope", "hypothesis", "n = 12"]
    for _ in range(70):  # ghosts of old lessons, half erased
        fnt = _F.truetype("/System/Library/Fonts/Supplemental/Chalkduster.ttf", int(rng.uniform(50, 120)))
        gd.text((rng.uniform(-100, w), rng.uniform(0, h)), str(rng.choice(words)), font=fnt, fill=int(rng.uniform(90, 255)))
    ghost = cv2.GaussianBlur(np.asarray(gi, np.float32) / 255, (0, 0), 2.2) * 0.07 * (noise(h, w, rng, 25) > -0.3)
    chalk = np.array([214, 220, 212], np.float32)
    a = np.clip(dust + swipe + ghost, 0, 0.3)[..., None]
    return img * (1 - a) + chalk * a


SURFACES = {"charcoal": charcoal, "cork": cork, "kraft": kraft, "mat": mat, "walnut": walnut,
            "linen": linen, "slate": slate}


def path(name):
    """Cached surface PNG, generated on first use."""
    if name not in SURFACES:
        raise SystemExit(f"unknown surface {name!r}; one of {sorted(SURFACES)}")
    p = CACHE / f"surface_{name}_v{VERSION}.png"
    if not p.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        img = SURFACES[name](*SIZE)
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(p)
    return p
