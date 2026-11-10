"""Physical materials, generated procedurally and cached per plan: documents (documents.py:
one texture per line and per accent, so each reveals on its words), photo-print paper,
tape, push pins, rubber stamps and typed labels. Desk surfaces are shared across plans
(surfaces.py) and chosen by the plan's treatment (treatments.py).

Plan keys: `documents: {name: {kind, lines, ...life}}`; `receipts:` is the same thing with
kind receipt (the original key, still accepted). A `kind: screenshot` document has `image:`
(relative paths are read from the plan's folder), `crop:` and `source:` instead of lines.
"""
import hashlib, json, math
from pathlib import Path
import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

from . import documents, surfaces, treatments
from .texture import fbm, paper_tex  # noqa: F401  (re-exported for older callers)

from . import fonts as _fonts


def print_paper(seed=3):
    """Matte photo-print stock for window borders (tiles are cut per shot)."""
    return np.clip(paper_tex(1600, 1300, seed, (238, 233, 223), grain=0.014, fibres=0.04), 0, 255).astype(np.uint8)


def tape(seed, w=380, h=112):
    """Semi-transparent masking tape at 2x resolution (190x56 layout px at scale 0.5)."""
    rng = np.random.default_rng(seed)
    a = np.ones((h, w), np.float32)
    for side in (0, 1):  # torn ends
        for yy in range(h):
            cut = int(abs(rng.normal(0, 7)) + 4)
            if side == 0:
                a[yy, :cut] = 0
            else:
                a[yy, w - cut:] = 0
    a = cv2.GaussianBlur(a, (0, 0), 1.2)
    crinkle = fbm(h, w, seed, 4, 6)
    lum = 1 + 0.06 * crinkle / (np.abs(crinkle).max() + 1e-6)
    rgb = np.array([231, 220, 192], np.float32)[None, None] * lum[..., None]
    alpha = a * (0.55 + 0.08 * crinkle / (np.abs(crinkle).max() + 1e-6))
    return np.dstack([np.clip(rgb, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)


def pin(color=(214, 62, 38), d=84):
    """Push pin seen from above at 2x: a glossy dome with one highlight toward the desk light."""
    yy, xx = np.mgrid[0:d, 0:d].astype(np.float32); c = (d - 1) / 2; r = d * 0.42
    rr = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / r
    a = np.clip((1 - rr) * r / 1.2, 0, 1)
    z = np.sqrt(np.clip(1 - rr ** 2, 0, 1))
    nx, ny = (xx - c) / r, (yy - c) / r
    lit = np.clip(0.35 + 0.65 * (-0.45 * nx - 0.55 * ny + 0.7 * z), 0, 1.2)
    spec = np.exp(-(((xx - c + r * 0.38) ** 2 + (yy - c + r * 0.42) ** 2) / (2 * (r * 0.13) ** 2)))
    rgb = np.array(color, np.float32) * lit[..., None] + 255 * 0.85 * spec[..., None]
    return np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)


def stamp(text="TESTED", seed=21):
    """Rubber stamp: double border, heavy condensed caps, uneven ink."""
    f = _fonts.load("futura", 230)
    tw = ImageDraw.Draw(Image.new("L", (8, 8))).textlength(text, font=f); w, h = int(tw + 150), 330
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
    d.rounded_rectangle((14, 14, w - 14, h - 14), radius=22, outline=255, width=16)
    d.rounded_rectangle((40, 40, w - 40, h - 40), radius=12, outline=255, width=6)
    d.text(((w - tw) / 2, (h - 230) / 2 - 28), text, font=f, fill=255)
    a = np.asarray(im, np.float32) / 255.0
    rng = np.random.default_rng(seed)
    blot = fbm(h, w, seed, 5, 5, 0.65)
    speck = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 1.2)
    ink = np.clip(0.78 + 0.5 * blot / (np.abs(blot).max() + 1e-6), 0, 1) * (speck > 0.43)
    edge = cv2.GaussianBlur(a, (0, 0), 1.6)
    a = np.clip(a * ink * 1.15, 0, 1) * np.clip(edge * 1.4, 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 0.8) * 0.93
    rgba = np.zeros((h, w, 4), np.uint8); rgba[..., :3] = (214, 62, 38); rgba[..., 3] = np.clip(a * 255, 0, 255)
    return rgba


def label(text, seed=5):
    """Typed paper label strip at 2x resolution."""
    f = _fonts.load("courier", 54)
    tw = ImageDraw.Draw(Image.new("L", (8, 8))).textlength(text, font=f)
    w, h = int(tw + 84), 116
    im = Image.new("L", (w, h), 0); ImageDraw.Draw(im).text((42, (h - 54) / 2 - 6), text, font=f, fill=255)
    ink = cv2.GaussianBlur(np.asarray(im, np.float32) / 255, (0, 0), 0.7)
    rng = np.random.default_rng(seed)
    paper = np.array([241, 236, 225], np.float32) * (1 + 0.02 * cv2.GaussianBlur(
        rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.2))[..., None]
    rgb = paper * (1 - ink[..., None]) + np.array([42, 40, 37], np.float32)[None, None] * ink[..., None]
    a = np.ones((h, w), np.float32)
    for x in range(w):  # slightly uneven cut edges
        a[:int(abs(rng.normal(0, 1.2))), x] = 0; a[h - int(abs(rng.normal(0, 1.2))):, x] = 0
    return np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)


# ---------------------------------------------------------------- plan -> materials

def docs_of(plan):
    """Every document in the plan with its kind: legacy `receipts` first (their seeds stay put)."""
    out = {}
    for name, r in (plan.get("receipts") or {}).items():
        out[name] = dict(r, kind=r.get("kind", "receipt"))
    for name, r in (plan.get("documents") or {}).items():
        if name in out:
            raise SystemExit(f"document {name!r} is defined twice (receipts and documents)")
        out[name] = dict(r, kind=r.get("kind") or treatments.default_kind(plan))
    return out


def image_path(plan, r):
    """A screenshot's file: absolute, or relative to the plan's folder."""
    p = Path(str(r.get("image") or "")).expanduser()
    if not str(r.get("image") or "").strip():
        raise SystemExit("a screenshot document needs image: path/to/screenshot.png")
    p = p if p.is_absolute() else (plan.path.parent / p).resolve()
    if not p.exists():
        raise SystemExit(f"screenshot image not found: {p}")
    return p


def _doc_key(plan, v):
    if v["kind"] == "screenshot":  # the picture itself is the content: its file, size and date
        p = image_path(plan, v); st = p.stat()
        return {"kind": "screenshot", "image": str(p), "size": st.st_size, "mtime": st.st_mtime, "crop": v.get("crop"),
                "source": v.get("source"), "stamps": v.get("stamps", [])}
    return {"kind": v["kind"], "lines": v["lines"], "stamps": v.get("stamps", [])}


def _key(plan):
    docs = {k: _doc_key(plan, v) for k, v in docs_of(plan).items()}
    blob = json.dumps({"d": docs, "l": plan.get("labels", {}), "v": 5}, sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:12]


def build(plan, force=False):
    d = plan.wp("materials")
    meta_p = d / "meta.json"
    key = _key(plan)
    for s in treatments.surfaces_used(plan):
        surfaces.path(s)  # shared cache, generated once per machine
    if meta_p.exists() and not force and json.loads(meta_p.read_text()).get("key") == key:
        return json.loads(meta_p.read_text())
    if not all((d / f).exists() for f in ("print_paper.png", "tape3.png", "pin2.png")) or force:
        Image.fromarray(print_paper()).save(d / "print_paper.png")
        for i in range(4):
            Image.fromarray(tape(31 + i)).save(d / f"tape{i}.png")
        for i, col in enumerate([(214, 62, 38), (236, 228, 210), (38, 36, 34)]):
            Image.fromarray(pin(col)).save(d / f"pin{i}.png")
    docs = docs_of(plan)
    audio = sr = None; waves = [s for r in docs.values() for s in r.get("lines", []) if s.startswith("WAVE:")]
    ref = 1.0
    if waves:
        audio, sr = sf.read(plan.wp("prep", "audio48.wav"), dtype="float32")
        ref = max(float(np.abs(audio[int(float(s.split(':')[1]) * sr):int(float(s.split(':')[2]) * sr)]).max())
                  for s in waves) or 1.0
    meta = {"key": key, "docs": {}, "labels": {}, "stamps": []}
    for old in list(d.glob("*_line[0-9][0-9]*.png")) + list(d.glob("*_paper.png")):
        if old.name != "print_paper.png":  # stale document textures only
            old.unlink()
    for k, (name, r) in enumerate(docs.items()):
        if r["kind"] == "screenshot":
            paper, imgs, m = documents.screenshot(dict(r, image=str(image_path(plan, r))), 11 + k)
        else:
            paper, imgs, m = documents.document(r["kind"], r["lines"], 11 + k, audio, sr, ref)
        Image.fromarray(paper).save(d / f"{name}_paper.png")
        for i, (ink, acc) in enumerate(imgs):
            Image.fromarray(ink).save(d / f"{name}_line{i:02d}.png")
            if acc is not None:
                Image.fromarray(acc).save(d / f"{name}_line{i:02d}_acc.png")
        meta["docs"][name] = m
        for st in r.get("stamps", []):
            txt = st.get("text", "TESTED")
            if txt not in meta["stamps"]:
                Image.fromarray(stamp(txt)).save(d / f"stamp_{txt}.png"); meta["stamps"].append(txt)
    for name, lb in plan.get("labels", {}).items():
        Image.fromarray(label(lb["text"])).save(d / f"label_{name}.png"); meta["labels"][name] = lb["text"]
    meta_p.write_text(json.dumps(meta, indent=1))
    return meta
