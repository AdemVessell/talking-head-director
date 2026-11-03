"""Frames: stage (with adaptive motion blur) -> captions -> house finish -> end burn.
Renders in parallel ProRes chunks, then assembles the review MP4 with the mix."""
import math, subprocess, sys
from multiprocessing import Pool
import cv2
import numpy as np
from PIL import Image

from . import captions, shots
from .plan import SCRIPTS, Plan
from .prep import fps_arg
from .stage import Stage, seg
from .timeline import Timeline

sys.path.insert(0, str(SCRIPTS))
from look import Finish  # noqa: E402


class Renderer:
    def __init__(self, plan, proof=False):
        self.plan, self.proof = plan, proof
        self.tl, meta, lv = shots.prepare(plan)
        sc = 0.5 if proof else 1.0  # proof: half size, no motion blur, for reviewing timing fast
        if plan.get("journey") is not None:  # the opt-in perspective camera and plane changes
            from .journeys import Journey
            from .stage3d import Stage3D
            self.stage = Stage3D(plan, self.tl, meta, sc, lv); self.journey = Journey(plan, self.stage)
        else:
            self.stage = Stage(plan, self.tl, meta, sc, lv); self.journey = None
        self.W, self.H = self.stage.W, self.stage.H
        self.finish = Finish(self.W, self.H, plan["finish"])
        self.cards = captions.cards(plan, self.tl)
        self.cap, self.cap_y0 = captions.band_renderer(plan, sc)
        burn = plan.get("end", {}).get("burn")
        self.burn = (self.tl.t(burn[0]), self.tl.t(burn[1])) if burn else None
        self.nf = int(round(self.tl.total * plan.fps))

    def frame(self, i):
        fps = self.plan.fps; t = i / fps; st = self.stage
        rl = st.footage.map(t); fr = st.footage.frame(*rl)
        n = int(np.clip(st.motion_px(t) * 0.6 / 5, 1, 28))  # ~one sample per 5 px of travel, 216-degree shutter
        if n > 2 and not self.proof:
            acc = None
            for k in range(n):
                s = st.render(t + (k / (n - 1) - 0.5) * 0.6 / fps, fr, rl, t_ink=t)
                acc = s if acc is None else acc + s
            stage = acc / n
        else:
            stage = st.render(t, fr, rl)
        np.clip(stage, 0, 1, out=stage)
        if self.journey:
            stage = self.journey.post(stage, t)
        c = self.cap.render(self.cards, t)  # a band around the caption line, not a full frame
        layer = np.asarray(c).astype(np.float32) / 255
        if layer[..., 3].any():
            y0 = self.cap_y0; band = stage[y0:y0 + layer.shape[0]]
            a = layer[..., 3:4]
            band *= (1 - a); band += layer[..., :3] * a
        img = self.finish.apply(stage, i)
        return self.end_burn(img, t)

    def end_burn(self, img, t):
        """Film burn into black (the ending's spice), after the finish."""
        if not self.burn:
            return img
        b0, b1 = self.burn
        if t >= b1:
            return np.zeros_like(img)
        if t >= b0:
            u = seg(t, b0, b1); H, W = img.shape[:2]
            X = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
            Y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
            leak = np.clip(1.6 * u + 1.2 * X - 1.0 + 0.25 * np.sin(Y * 9 + u * 3), 0, 1.4)
            out = img.astype(np.float32) / 255 + leak * np.array([1.0, 0.52, 0.22], np.float32) * (0.6 + 1.2 * u)
            out = out * (1 - 0.7 * u * u)
            return (np.clip(out, 0, 1) * 255).astype(np.uint8)
        return img


def stills(plan, times, proof=False):
    R = Renderer(plan, proof)
    ims = []
    for s in times:
        i = int(round(float(s) * plan.fps)); im = R.frame(i)
        Image.fromarray(im).save(plan.wp("review", f"still_{float(s):06.2f}.jpg"), quality=92); ims.append(im)
    if len(ims) > 1:
        th = [cv2.resize(x, (360, 640), interpolation=cv2.INTER_AREA) for x in ims]  # any render size
        while len(th) % 4:
            th.append(np.zeros_like(th[0]))
        sheet = np.vstack([np.hstack(th[k:k + 4]) for k in range(0, len(th), 4)])
        Image.fromarray(sheet).save(plan.wp("review", "stills_sheet.jpg"), quality=90)
    print("stills ->", plan.wp("review"))


_R = None


def _init(plan_path, proof):
    """One renderer per worker process (materials, grain bank, captions built once, not per chunk)."""
    global _R
    _R = Renderer(Plan.load(plan_path), proof)


def _worker(args):
    plan_path, a, b, out, proof = args
    R = _R; plan = R.plan
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{R.W}x{R.H}", "-r", fps_arg(plan), "-i", "-", "-c:v", "prores_ks", "-profile:v", "3",
           "-pix_fmt", "yuv422p10le", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(a, b):
        p.stdin.write(R.frame(i).tobytes())
    p.stdin.close(); p.wait()
    return out


def render(plan, jobs=8, proof=False, frames=None):
    tl, _, _ = shots.prepare(plan)  # materials once, before the workers fork
    nf = int(round(tl.total * plan.fps))
    lo, hi = frames or (0, nf)
    for old in plan.wp("render").glob("chunk_*.mov"):
        old.unlink()
    step = math.ceil((hi - lo) / (jobs * 3))  # small chunks balance the motion-blurred frames
    chunks = [(str(plan.path), s, min(hi, s + step), str(plan.wp("render", f"chunk_{s:05d}.mov")), proof)
              for s in range(lo, hi, step)]
    with Pool(min(jobs, len(chunks)), initializer=_init, initargs=(str(plan.path), proof)) as pool:
        outs = pool.map(_worker, chunks, chunksize=1)
    plan.wp("render", "chunks.txt").write_text("".join(f"file '{o}'\n" for o in outs))
    print(f"rendered {hi - lo} frames in {len(outs)} chunks")


def assemble(plan, name=None):
    out = plan.wp("out", (name or plan.get("name", "edit")) + ".mp4")
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(plan.wp("render", "chunks.txt")), "-i", str(plan.wp("render", "mix.wav")),
                    "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "18M",
                    "-bufsize", "36M", "-profile:v", "high", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-colorspace", "bt709", "-r", fps_arg(plan), "-c:a", "aac", "-b:a", "256k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print("->", out)
    return out
