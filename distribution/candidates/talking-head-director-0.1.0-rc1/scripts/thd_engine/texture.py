"""Shared procedural noise: fractal noise and paper stock."""
import math
import cv2
import numpy as np


def fbm(h, w, seed, octaves=6, base=4, falloff=0.6):
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        s = base * 2 ** o
        n = rng.standard_normal((max(2, h * s // max(h, w) + 2), max(2, w * s // max(h, w) + 2))).astype(np.float32)
        out += amp * cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC); tot += amp; amp *= falloff
    return out / tot


def noise(h, w, rng, sigma, sy=None):
    """Blurred white noise, unit std (sy: a different vertical sigma for stretched grain)."""
    n = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), sigmaX=sigma, sigmaY=sy or sigma)
    return n / (n.std() + 1e-6)


def paper_tex(h, w, seed, base, grain=0.018, fibres=0.05):
    rng = np.random.default_rng(seed)
    n = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 0.9)
    m = fbm(h, w, seed + 1, octaves=4, base=3)
    lay = np.zeros((h, w), np.float32)
    for _ in range(int(w * h / 900)):
        x, y = rng.uniform(0, w), rng.uniform(0, h); ang = rng.uniform(0, math.pi); L = rng.uniform(6, 26)
        cv2.line(lay, (int(x), int(y)), (int(x + math.cos(ang) * L), int(y + math.sin(ang) * L)), 1.0, 1, cv2.LINE_AA)
    lum = 1 + grain * n / n.std() + 0.012 * m / (np.abs(m).max() + 1e-6) - fibres * cv2.GaussianBlur(lay, (0, 0), 0.5) * 0.4
    return np.array(base, np.float32)[None, None, :] * lum[..., None]
