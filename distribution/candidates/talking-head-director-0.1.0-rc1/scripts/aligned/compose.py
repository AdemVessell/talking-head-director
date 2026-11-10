"""Workshop frame for a source-aligned edit.

Imports the engine's surfaces, fonts, texture, materials, and look. It does not
reimplement them. Labels, waveform windows, and diagram copy come from the plan.
A waveform is drawn only when the plan names two windows of the same source audio.
A diagram is always marked as a simplified illustration, not a measurement.
"""
import json, math, os, sys
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from thd_engine import surfaces, fonts, texture, materials
import look

from edl import EDL, load_plan, probe
from words import load_src_words, map_words

W, H = 1080, 1920
IVORY = (239, 232, 218)
INK = (24, 21, 18)
PENCIL = (112, 107, 99)
VERM = (226, 69, 43)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def eo(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


class Compose:
    def __init__(self, plan_path, preview_ids=None):
        self.plan = load_plan(plan_path)
        self.src = self.plan["source"]
        info = probe(self.src)
        self.edl = EDL(self.plan, info)
        from edl import work_dir
        self.work = work_dir(self.plan)
        self.work.mkdir(parents=True, exist_ok=True)
        self.plan["_work"] = self.work
        if preview_ids:
            rows = [self.edl.by_id[i] for i in preview_ids]
            from edl import table_of
            segs, dur = table_of(rows, 0)
            self.edl.segments = segs
            self.edl.by_id = {s["id"]: s for s in segs}
            self.edl.dur = dur
            self.edl.nframes = int(math.floor(dur * self.edl.fps + 1e-6))
            self.edl.room = {s["id"] for s in segs if s["room"]}
        self.finish = look.Finish(W, H, "medium", grain=0.020)
        self.cache = {}
        self.cap = cv2.VideoCapture(self.src)
        words = map_words(self.edl, load_src_words(self.plan["words"])) if self.plan.get("words") else []
        self.captions = self._cards(words)
        self.audio = None

    def _cards(self, words):
        spec = self.plan.get("caption_groups", "auto")
        if not words:
            return []
        if spec == "auto":
            cards, cur = [], []
            for w in words:
                cur.append(w)
                if w["w"].rstrip().endswith((".", "?", "!")) or len(cur) >= 4:
                    cards.append(cur)
                    cur = []
            if cur:
                cards.append(cur)
        else:
            cards, k = [], 0
            for phrase in spec:
                cards.append(words[k:k + len(phrase)])
                k += len(phrase)
        caps = []
        for ws in cards:
            caps.append({"start": max(0.0, ws[0]["s"] - 0.04), "end": ws[-1]["e"] + 0.22, "words": ws})
        for i in range(len(caps) - 1):
            caps[i]["end"] = min(caps[i]["end"], caps[i + 1]["start"])
        return caps

    def font(self, role, size):
        return fonts.load(role, size)

    def mat(self):
        if "mat" not in self.cache:
            im = np.array(Image.open(surfaces.path("mat")).convert("RGB"), np.float32)
            self.cache["mat"] = cv2.resize(im, (W + 80, H + 80), interpolation=cv2.INTER_AREA)
        return self.cache["mat"]

    def paper(self, w, h, seed, base=IVORY):
        key = ("paper", w, h, seed)
        if key not in self.cache:
            self.cache[key] = np.clip(texture.paper_tex(h, w, seed, base, grain=0.016, fibres=0.04), 0, 255).astype(np.float32)
        return self.cache[key]

    def frame_src(self, i):
        i = int(min(max(i, 0), self.edl.src_frames - 1))
        key = ("f", i)
        if key not in self.cache:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, bgr = self.cap.read()
            if not ok:
                bgr = np.zeros((1280, 720, 3), np.uint8)
            self.cache[key] = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
            if sum(1 for k in self.cache if isinstance(k, tuple) and k[0] == "f") > 8:
                for k in [k for k in self.cache if isinstance(k, tuple) and k[0] == "f"][:4]:
                    del self.cache[k]
        return self.cache[key]

    def over(self, dst, rgba, cx, cy, rot=0.0, scale=1.0):
        h, w = rgba.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
        M[0, 2] += cx - w / 2
        M[1, 2] += cy - h / 2
        rgb, a = rgba[..., :3], rgba[..., 3:] / 255.0
        if a.shape[2] == 1:
            a = a[..., 0]
        wa = cv2.warpAffine(a, M, (W, H))
        wr = cv2.warpAffine(rgb, M, (W, H))
        if wa.ndim == 2:
            wa = wa[..., None]
        dst[:] = dst * (1 - wa) + wr * wa

    def tape(self, dst, cx, cy, ang, seed):
        t = materials.tape(seed).astype(np.float32)
        self.over(dst, t, cx, cy, ang, 0.42)

    def print_of(self, img, crop, out_w):
        x, y, cw, ch = crop
        out_h = int(round(out_w * ch / cw))
        border = 16
        pw, ph = out_w + 2 * border, out_h + 2 * border
        M = np.array([[out_w / cw, 0, -x * out_w / cw + border], [0, out_h / ch, -y * out_h / ch + border]], np.float32)
        base = self.paper(pw, ph, 7, (238, 233, 223)).copy()
        pic = cv2.warpAffine(img, M, (pw, ph), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        base[border:border + out_h, border:border + out_w] = pic[border:border + out_h, border:border + out_w]
        return np.dstack([base, np.full((ph, pw), 255, np.float32)])

    def card(self, lines, sub, active, seed):
        w, h = 460, 250
        im = Image.fromarray(self.paper(w, h, seed).astype(np.uint8))
        d = ImageDraw.Draw(im)
        d.text((24, 16), "PASSAGE", font=self.font("menlo_bold", 22), fill=PENCIL)
        d.text((24, 52), lines[0], font=self.font("caption_heavy", 54), fill=VERM if active else INK)
        if len(lines) > 1:
            d.text((24, 112), lines[1], font=self.font("caption_heavy", 54), fill=INK)
        d.text((24, 190), sub, font=self.font("typewriter", 26), fill=PENCIL)
        return np.dstack([np.array(im, np.float32), np.full((h, w), 255, np.float32)])

    def _audio(self):
        if self.audio is None:
            import soundfile as sf
            wav = self.work / "src48.wav"
            if not wav.exists():
                from audio import load_audio
                self.audio, _ = load_audio(self.src, wav)
            else:
                self.audio, _ = sf.read(wav, dtype="float64")
                if self.audio.ndim > 1:
                    self.audio = self.audio.mean(axis=1)
        return self.audio

    def wave_card(self, t):
        spec = self.plan.get("waveform")
        if not spec or len(spec.get("rows") or []) < 2:
            return None
        audio = self._audio()
        pps = float(spec.get("pixels_per_second", 120))
        amp = float(spec.get("amplitude_px", 40))
        w, h = 960, 330
        im = Image.fromarray(self.paper(w, h, 21).astype(np.uint8))
        d = ImageDraw.Draw(im)
        d.text((24, 14), "SAME SOURCE  ·  SAME SCALE", font=self.font("menlo_bold", 22), fill=PENCIL)
        peaks = []
        for i, row in enumerate(spec["rows"]):
            a, b = float(row["src_in"]), float(row["src_out"])
            sl = audio[int(a * 48000):int(b * 48000)]
            px = max(2, int((b - a) * pps))
            n = max(1, len(sl) // px)
            env = np.array([np.max(np.abs(sl[k * n:(k + 1) * n])) if len(sl) else 0 for k in range(px)])
            peaks.append(float(env.max()) if len(env) else 0)
            sid = row["segment"]
            t0 = self.edl.by_id[sid]["edit_in"] + (a - self.edl.by_id[sid]["src_in"])
            prog = int(np.clip((t - t0) * pps, 0, px))
            yc = 110 + i * 110
            d.text((24, yc - 36), row.get("label", sid), font=self.font("didot", 36), fill=INK)
            x0 = 160
            for k in range(prog):
                hh = max(1.0, env[k] * amp)
                d.line((x0 + k, yc - hh, x0 + k, yc + hh), fill=INK)
        d.text((24, h - 36), spec.get("disclaimer", "same recording · not a controlled measurement"),
               font=self.font("typewriter", 22), fill=INK)
        self.cache["wave_peaks"] = peaks
        return np.dstack([np.array(im, np.float32), np.full((h, w), 255, np.float32)])

    def diagram(self, t, cues):
        spec = self.plan.get("diagram") or {}
        w, h = 1000, 720
        im = Image.fromarray(self.paper(w, h, 31).astype(np.uint8)).convert("RGBA")
        d = ImageDraw.Draw(im)
        d.text((32, 24), spec.get("title", "DIAGRAM"), font=self.font("menlo_bold", 34), fill=INK)
        d.text((32, 68), spec.get("subtitle", "simplified illustration · not to scale"),
               font=self.font("typewriter", 24), fill=PENCIL)
        rows = spec.get("rows") or [{"label": "1"}, {"label": "2"}]
        if t >= cues["row1"]:
            d.text((32, 140), "1  " + rows[0]["label"], font=self.font("caption_heavy", 40), fill=INK)
            d.rounded_rectangle((80, 230, 900, 280), radius=16, outline=INK, width=4)
            if t >= cues["pulse"]:
                u = min(1.0, (t - cues["pulse"]) / 0.8)
                x = 80 + u * 820
                d.ellipse((x - 16, 238, x + 16, 272), fill=VERM)
        if t >= cues["row2"]:
            d.text((32, 360), "2  " + rows[1]["label"], font=self.font("caption_heavy", 40), fill=INK)
            d.rounded_rectangle((80, 470, 900, 510), radius=16, outline=INK, width=4)
            d.line((200, 510, 200, 620), fill=VERM, width=6)
            d.line((700, 510, 700, 620), fill=VERM, width=6)
            d.text((32, 650), rows[1].get("note", ""), font=self.font("typewriter", 22), fill=PENCIL)
        return np.array(im, np.float32)

    def track_mark(self, img):
        spec = self.plan.get("track")
        if not spec:
            return None
        hsv = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2HSV)
        h_max = int(spec.get("h_max", 12))
        s_min = int(spec.get("s_min", 120))
        v_min = int(spec.get("v_min", 80))
        m = ((hsv[..., 0] < h_max) | (hsv[..., 0] > 170)) & (hsv[..., 1] > s_min) & (hsv[..., 2] > v_min)
        ys, xs = np.nonzero(m)
        if len(xs) < 30:
            return None
        return float(xs.mean()), float(ys.mean())

    def draw_captions(self, dst, t):
        g = next((g for g in self.captions if g["start"] <= t < g["end"]), None)
        if not g:
            return
        font = self.font("caption_heavy", 72)
        words = [w["w"].upper() for w in g["words"]]
        lay = Image.new("RGBA", (W, 160), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        widths = [font.getlength(x) for x in words]
        sp = font.getlength(" ")
        x = (W - (sum(widths) + sp * (len(words) - 1))) / 2
        for wd, wi, meta in zip(words, widths, g["words"]):
            active = meta["s"] <= t < max(meta["e"], meta["s"] + 0.08)
            d.text((x, 40), wd, font=font, fill=VERM + (255,) if active else (246, 241, 230, 255))
            x += wi + sp
        arr = np.array(lay, np.float32)
        y = 1700
        a = arr[..., 3:] / 255
        dst[y:y + 160] = dst[y:y + 160] * (1 - a) + arr[..., :3] * a

    def frame(self, n):
        t = n / self.edl.fps
        si = int(round(self.edl.src_time(t) * self.edl.fps))
        src = self.frame_src(si)
        sh, sw = src.shape[:2]
        dst = self.mat()[:H, :W].copy()
        seg = self.edl.seg_at(t)
        labelled = bool(seg.get("card"))
        pr = self.print_of(src, (0, 0, sw, sh), 780 if labelled else 860)
        self.over(dst, pr, 540, 820 if labelled else 700, -0.6)
        self.tape(dst, 220, 430, -28, 3)
        self.tape(dst, 860, 430, 24, 4)
        if labelled:
            self.over(dst, self.card(seg["card"], seg["sub"], True, 11), 280, 1280, -1.5)
        if self._wave_on(seg):
            wave = self.wave_card(t)
            if wave is not None:
                self.over(dst, wave, 540, 1620, 0.4)
        cues = self._cues()
        if cues and not labelled and t >= cues["row1"]:
            self.over(dst, self.diagram(t, cues), 540, 1180, 0.4, 0.72)
        if not seg.get("room") and not labelled:
            self.draw_captions(dst, t)
        mark = self.track_mark(src)
        if mark:
            px = 540 + (mark[0] / sw - 0.5) * 780
            py = 820 + (mark[1] / sh - 0.5) * (780 * sh / sw)
            yy, xx = np.ogrid[:H, :W]
            rr = (xx - px) ** 2 + (yy - py) ** 2
            dst[(rr > 28 ** 2) & (rr < 40 ** 2)] = VERM
        out = self.finish.apply(np.clip(dst, 0, 255).astype(np.uint8), n)
        return out

    def _wave_on(self, seg):
        rows = (self.plan.get("waveform") or {}).get("rows") or []
        return len(rows) >= 2 and seg["id"] in {r["segment"] for r in rows}

    def _cues(self):
        spec = (self.plan.get("diagram") or {}).get("cues")
        if not spec:
            return None
        def at(item):
            s = self.edl.by_id[item["segment"]]
            return s["edit_in"] + float(item["offset"])
        return {k: at(v) for k, v in spec.items()}
