#!/usr/bin/env python3
"""Render the reference style frames (visual targets for art direction).

Shows how the building blocks compose: face-anchored crop -> grade_webcam ->
stage material -> print-treated elements with shadows -> devices -> captions ->
Finish. The copy is illustrative. These are direction, not templates.

usage: style_frames.py --source PRESENTER.mov --track track.json --out DIR [--photo IMG]
"""
import argparse, math, sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import look
from face_track import Track
from caption_cards import CardRenderer

W, H = 1080, 1920
from thd_engine import fonts as _fonts
F = _fonts.TABLE   # didot didot_r mono type cond hand_bold black
INK, PAPER, CHAR, VERM, AMBER = (21, 18, 15), (233, 225, 211), (34, 32, 29), (226, 69, 43), (255, 179, 71)


def font(k, size):
    p, i = F[k]; return ImageFont.truetype(p, size, index=i)


def rgba(a):
    return Image.fromarray(a).convert("RGBA")


def shadow_paste(base, layer, xy, blur=16, off=(10, 14), alpha=0.45):
    a = layer.split()[3].filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", layer.size, (8, 6, 4, 0)); sh.putalpha(a.point(lambda v: int(v * alpha)))
    base.alpha_composite(sh, (xy[0] + off[0], xy[1] + off[1])); base.alpha_composite(layer, xy)


def rotate(layer, deg):
    return layer.rotate(deg, resample=Image.Resampling.BICUBIC, expand=True)


def board(seed=3):
    """Charcoal board lit by one warm pool from top-left."""
    b = look.paper(W, H, seed=seed, base=CHAR, relief=0.10, fibres=120).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - 260) / 1250) ** 2 + ((yy - 360) / 1500) ** 2)
    pool = np.clip(1.0 - d, 0, 1) ** 1.6
    b *= (0.55 + 0.95 * pool)[..., None]
    b *= np.array([1.0, 0.97, 0.92])[None, None, :] ** pool[..., None]
    return Image.fromarray(np.clip(b, 0, 255).astype(np.uint8)).convert("RGBA")


def journal(seed=5):
    p = Image.fromarray(look.paper(W, H, seed=seed, relief=0.022, fibres=320)).convert("RGBA")
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for y in range(120, H, 48):  # faint 8px-baseline-derived ruling, barely there
        d.line([(0, y), (W, y)], fill=(110, 120, 130, 13), width=2)
    p.alpha_composite(g)
    return p


def tape(w=150, h=46, deg=0, seed=0):
    rng = np.random.default_rng(seed)
    t = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    pts = [(0, 0)] + [(w, 0)] + [(w - rng.integers(0, 6), y) for y in range(0, h, 6)] + [(w, h), (0, h)] + \
          [(rng.integers(0, 6), y) for y in range(h, 0, -6)]
    d.polygon(pts, fill=(222, 210, 180, 190))
    return rotate(t, deg)


def window(cam, border=22, edge="print"):
    """Camera image as a physical print (border) or torn paper."""
    cw, ch = cam.size
    if edge == "print":
        f = Image.new("RGBA", (cw + 2 * border, ch + 2 * border), (240, 236, 228, 255)); f.alpha_composite(cam, (border, border))
        return f
    rng = np.random.default_rng(9)
    m = Image.new("L", cam.size, 0); d = ImageDraw.Draw(m)
    top = [(x, int(rng.integers(0, 14))) for x in range(0, cw + 12, 12)]
    bot = [(x, ch - int(rng.integers(0, 16))) for x in range(cw, -12, -12)]
    d.polygon(top + bot, fill=255)
    cam = cam.copy(); cam.putalpha(m)
    return cam


def receipt(lines, w=400, seed=4):
    fnt = font("mono", 34); lh = 48
    h = 80 + lh * len(lines) + 70
    r = Image.fromarray(look.paper(w, h, seed=seed, base=(243, 241, 234), relief=0.03, fibres=40)).convert("RGBA")
    d = ImageDraw.Draw(r)
    y = 50
    for ln in lines:
        if ln == "-":
            d.text((28, y), "- " * 20, font=fnt, fill=(120, 116, 110, 255))
        elif isinstance(ln, tuple):
            d.text((28, y), ln[0], font=fnt, fill=(80, 76, 72, 255))
            tw = d.textlength(ln[1], font=fnt); d.text((w - 28 - tw, y), ln[1], font=fnt, fill=(80, 76, 72, 255))
        else:
            d.text((28, y), ln, font=fnt, fill=(80, 76, 72, 255))
        y += lh
    # faded thermal print: uneven darkness
    a = np.array(r).astype(np.float32)
    n = cv2.GaussianBlur(np.random.default_rng(seed).standard_normal((h, w)).astype(np.float32), (0, 0), 6)
    a[..., :3] = 255 - (255 - a[..., :3]) * np.clip(0.85 + 0.25 * n, 0.6, 1.1)[..., None]
    r = Image.fromarray(a.astype(np.uint8))
    m = Image.new("L", (w, h), 255); d = ImageDraw.Draw(m)  # torn zigzag bottom
    zz = [(0, h)] + [(x, h - (14 if (x // 14) % 2 else 2)) for x in range(0, w + 14, 14)] + [(w, h)]
    d.polygon(zz, fill=0); r.putalpha(m)
    return r


def stamp(word, size=120, deg=-8, seed=2):
    fnt = font("black", size); pad = 28
    d0 = ImageDraw.Draw(Image.new("L", (8, 8))); tw = int(d0.textlength(word, font=fnt))
    w, h = tw + 2 * pad, int(size * 1.15) + 2 * pad
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    d.rounded_rectangle((6, 6, w - 6, h - 6), radius=18, outline=255, width=10)
    d.text((pad, pad - size * 0.12), word, font=fnt, fill=255)
    a = np.array(m).astype(np.float32) / 255
    rng = np.random.default_rng(seed)
    fine = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.2)
    broad = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 14)
    cover = np.clip((fine * 0.6 + broad * 1.4 + 1.1), 0, 1)  # ink voids, uneven pressure
    a = a * cover
    lay = Image.new("RGBA", (w, h), VERM + (0,)); lay.putalpha(Image.fromarray((a * 235).astype(np.uint8)))
    return rotate(lay, deg)


def marker_ellipse(size, cx, cy, rx, ry, seed=1, width=11, turns=1.12):
    lay = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(seed); pts = []
    for k in range(80):
        t = k / 79 * turns * 2 * math.pi - 0.9
        wob = 1 + 0.035 * math.sin(3 * t + rng.uniform(0, 0.3)) + rng.normal(0, 0.006)
        pts.append((cx + rx * wob * math.cos(t), cy + ry * wob * math.sin(t)))
    d.line(pts, fill=VERM + (225,), width=width, joint="curve")
    return lay.filter(ImageFilter.GaussianBlur(0.6))


def caption(img, text, active, keyword=(), light=False):
    words = [{"w": w, "s": i * 0.3, "e": i * 0.3 + 0.28} for i, w in enumerate(text.split())]
    card = {"words": words, "start": 0, "end": 10, "text": text}
    r = CardRenderer(y=img.info.get("cap_y", 1440), light_stage=light); t = words[active]["s"] + 0.2
    img.alpha_composite(r.render([card], t, keywords=keyword))


def cam_crop(src, track, t, zoom, aspect, size, eye=0.36):
    cap = cv2.VideoCapture(str(src)); cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
    rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
    g = look.grade_webcam(rgb, tuple(track.at(t)))
    x, y, w, h = track.crop(t, zoom=zoom, aspect=aspect, eye_line=eye)
    return rgba(cv2.resize(g[y:y + h, x:x + w], size, interpolation=cv2.INTER_LANCZOS4))


def finish(img, preset="medium", i=0):
    return Image.fromarray(look.Finish(W, H, preset).apply(np.array(img.convert("RGB")), i))


def frame_evidence(src, tr):
    img = board()
    cam = cam_crop(src, tr, 1.6, 1.0, 4 / 5, (760, 950))
    win = rotate(window(cam), -1.5); shadow_paste(img, win, (70, 330), blur=22, off=(14, 20), alpha=0.55)
    img.alpha_composite(tape(170, 50, 4, 1), (330, 300))
    r = rotate(receipt(["TEST 01 / AI VIDEO", "-", ("CREDITS", "$20.00"), ("TOOLS", "3"),
                        ("TIME", "3H 12M"), ("KEEPERS", "1"), "-", ("TOTAL", "$20.00")], w=430), 2.5)
    shadow_paste(img, r, (610, 120), blur=14, off=(10, 16), alpha=0.5)
    img.alpha_composite(tape(130, 44, -6, 2), (740, 100))
    s = stamp("TESTED", 104, -9); img.alpha_composite(s, (600, 1150))
    d = ImageDraw.Draw(img); d.text((72, 96), "FIELD TEST / 01", font=font("mono", 30), fill=(200, 192, 178, 255))
    img.info["cap_y"] = 1470; caption(img, "I SPENT $20 TESTING", 1)
    return finish(img, i=3)


def frame_journal(src, tr, photo):
    img = journal()
    cam = cam_crop(src, tr, 4.7, 1.0, 1.0, (470, 470))
    win = rotate(window(cam, edge="torn"), 1.2); shadow_paste(img, win, (552, 110), blur=12, off=(8, 10), alpha=0.35)
    d = ImageDraw.Draw(img)
    d.text((72, 128), "HOW IT WORKS", font=font("mono", 30), fill=(110, 104, 96, 255))
    d.text((66, 176), "Prompt in,", font=font("didot_r", 76), fill=INK + (255,))
    d.text((66, 262), "clip out.", font=font("didot_r", 76), fill=INK + (255,))
    # diagram: three boxes, ink lines, typewriter labels, on a 12-col grid
    y0, bw, bh = 690, 264, 150
    xs = [72, 408, 744]
    for x, lab in zip(xs, ["PROMPT", "MODEL", "CLIP"]):
        d.rectangle((x, y0, x + bw, y0 + bh), outline=INK + (255,), width=5)
        tw = d.textlength(lab, font=font("type", 46)); d.text((x + (bw - tw) / 2, y0 + 46), lab, font=font("type", 46), fill=INK + (255,))
    for x in (xs[0] + bw, xs[1] + bw):
        d.line((x + 10, y0 + bh / 2, x + 62, y0 + bh / 2), fill=INK + (255,), width=5)
        d.polygon([(x + 62, y0 + bh / 2 - 12), (x + 62, y0 + bh / 2 + 12), (x + 74, y0 + bh / 2)], fill=INK + (255,))
    img.alpha_composite(marker_ellipse((W, H), xs[1] + bw / 2, y0 + bh / 2, bw * 0.66, bh * 0.82, 3))
    d.text((xs[1] + 10, y0 + bh + 34), "the bottleneck", font=font("hand_bold", 46), fill=VERM + (255,))
    if photo:
        ph = cv2.cvtColor(cv2.imread(str(photo)), cv2.COLOR_BGR2RGB)
        ph = cv2.resize(ph, (330, 330), interpolation=cv2.INTER_AREA)
        clip = rgba(look.misregister(look.halftone(ph, cell=7), (1.5, -1)))
        shadow_paste(img, rotate(window(clip, 14), -2.5), (90, 960), blur=10, off=(8, 10), alpha=0.35)
        img.alpha_composite(tape(120, 40, -12, 4), (112, 944))
        d.text((480, 1060), "fig. 2", font=font("type", 36), fill=(90, 86, 80, 255))
        d.text((480, 1106), "one clip,", font=font("type", 36), fill=(90, 86, 80, 255))
        d.text((480, 1152), "eleven attempts", font=font("type", 36), fill=(90, 86, 80, 255))
    img.info["cap_y"] = 1420; caption(img, "THE MODEL IS THE BOTTLENECK", 1, light=True)  # inside the 1150-1450 zone
    return finish(img, "subtle", i=5)


def frame_signal(src, tr):
    img = Image.new("RGBA", (W, H), (16, 17, 19, 255))
    cam = np.array(cam_crop(src, tr, 7.9, 1.25, 9 / 16, (W, H)).convert("RGB")).astype(np.float32)
    k = 0.06; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)  # barrel + scanlines + chroma bleed
    nx, ny = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2); r2 = nx * nx + ny * ny
    mx = (nx * (1 + k * r2)) * W / 2 + W / 2; my = (ny * (1 + k * r2)) * H / 2 + H / 2
    cam = cv2.remap(cam, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    cam[..., 0] = np.roll(cv2.GaussianBlur(cam[..., 0], (0, 0), 1.2), 3, 1)
    cam *= (1 - 0.10 * ((np.arange(H) % 3) == 0)).astype(np.float32)[:, None, None]
    img = rgba(np.clip(cam, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 1540, W, 1626), fill=(12, 12, 13, 235))
    d.text((40, 1556), "CREDITS ARE THE NEW PAYWALL  ▪  CREDITS ARE THE NEW PAYWALL", font=font("mono", 40), fill=AMBER + (255,))
    d.rectangle((40, 110, 74, 144), fill=VERM + (255,))
    d.text((92, 104), "ON AIR / TAKE 03", font=font("mono", 34), fill=(235, 230, 220, 255))
    d.text((760, 104), "00:01:12:04", font=font("mono", 34), fill=AMBER + (255,))
    img.info["cap_y"] = 1360; caption(img, "HERE'S THE PROBLEM.", 2)
    return finish(img, i=7)


def frame_reveal():
    img = board(seed=8); d = ImageDraw.Draw(img)
    d.text((72, 520), "TOTAL TIME, THREE TOOLS", font=font("mono", 34), fill=(200, 192, 178, 255))
    big = font("didot", 400)
    d.text((40, 560), "3H", font=big, fill=(240, 234, 222, 255))
    d.text((40, 950), "12M", font=big, fill=VERM + (255,))
    img.alpha_composite(marker_ellipse((W, H), 455, 1384, 410, 22, 5, width=14, turns=0.55))
    d.text((72, 1470), "$20.00", font=font("mono", 48), fill=(240, 234, 222, 255))
    d.text((300, 1470), "\u2192", font=font("mono", 48), fill=(200, 192, 178, 255))
    d.text((390, 1470), "$0.00", font=font("mono", 48), fill=VERM + (255,))
    return finish(img, i=9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True); ap.add_argument("--track", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--photo")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True); tr = Track.load(a.track)
    frames = {"01-evidence-board-receipt-drop": frame_evidence(a.source, tr),
              "02-field-journal-proof": frame_journal(a.source, tr, a.photo),
              "03-signal-the-turn": frame_signal(a.source, tr),
              "04-the-reveal-cutaway": frame_reveal()}
    for k, im in frames.items():
        im.save(out / f"{k}.jpg", quality=92)
    sheet = Image.new("RGB", (4 * 540 + 3 * 12, 960), (10, 10, 10))
    for i, im in enumerate(frames.values()):
        sheet.paste(im.resize((540, 960), Image.Resampling.LANCZOS), (i * 552, 0))
    sheet.save(out / "00-overview.jpg", quality=90)
    print("wrote", ", ".join(frames), "->", out)


if __name__ == "__main__":
    main()
