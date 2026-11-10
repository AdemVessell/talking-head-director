#!/usr/bin/env python3
"""Smoothed face track for face-anchored framing (punch-ins, offsets, reframes).

Detects the face every few frames, interpolates, and smooths offline (centred
Gaussian, so no lag). The output lets a renderer place the eyes on the same
line in every shot size, so jump cuts can hide behind scale changes.

CLI:  face_track.py SOURCE.mp4 --out track.json [--every 3] [--model face_landmarker.task]
      face_track.py SOURCE.mp4 --out track.json --debug sheet.jpg
Module:
      from face_track import Track
      tr = Track.load("track.json")
      x, y, w, h = tr.crop(t_seconds, face_frac=0.67, aspect=4/5)   # shot C

Detector: OpenCV Haar (always available, no download) unless --model points
at a MediaPipe Tasks face_landmarker.task file, which gives a true eye line.
The JSON records which detector ran. Check the debug sheet before trusting it.
"""
import argparse, json, math
from pathlib import Path
import cv2
import numpy as np


def _gauss_smooth(v, sigma):
    if sigma <= 0 or len(v) < 3:
        return v
    r = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(v, r, mode="edge")
    return np.convolve(p, k, mode="valid")


def detect(source, every=3, model=None, scale=0.5):
    cap = cv2.VideoCapture(str(source))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    landmarker = None
    if model:
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        opts = vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(model)), num_faces=1)
        landmarker = vision.FaceLandmarker.create_from_options(opts)
    else:
        haar = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    rows, i = [], 0
    while True:
        ok = cap.grab()
        if not ok:
            break
        if i % every == 0:
            ok, fr = cap.retrieve()
            if not ok:
                break
            if landmarker:
                import mediapipe as mp
                img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
                res = landmarker.detect(img)
                if res.face_landmarks:
                    pts = np.array([[p.x * W, p.y * H] for p in res.face_landmarks[0]])
                    x0, y0 = pts.min(0); x1, y1 = pts.max(0)
                    eyes = pts[[33, 133, 362, 263]].mean(0)  # eye corners
                    rows.append((i, (x0 + x1) / 2, float(eyes[1]), x1 - x0))
            else:
                g = cv2.cvtColor(cv2.resize(fr, None, fx=scale, fy=scale), cv2.COLOR_BGR2GRAY)
                g = cv2.equalizeHist(g)
                f = haar.detectMultiScale(g, 1.1, 6, minSize=(int(60 * scale), int(60 * scale)))
                if len(f):
                    x, y, w, h = max(f, key=lambda b: b[2] * b[3]) / scale
                    rows.append((i, x + w / 2, y + 0.40 * h, w))  # Haar: eyes ~40% down the box
        i += 1
    n = max(n, i)
    return rows, fps, W, H, n, ("mediapipe_face_landmarker" if landmarker else "opencv_haar_frontal")


def build(rows, fps, n, pos_sigma_s=0.35, size_sigma_s=1.2):
    if not rows:
        raise SystemExit("no face found: check the source or pass --model")
    f = np.array([r[0] for r in rows], float)
    cols = np.array([r[1:] for r in rows], float)
    # reject outliers (detector jumps) against a running median
    med = np.array([np.median(cols[max(0, k - 5):k + 6], axis=0) for k in range(len(cols))])
    good = np.all(np.abs(cols - med) <= np.array([0.25, 0.25, 0.30]) * med[:, 2:3], axis=1)
    f, cols = f[good], cols[good]
    allf = np.arange(n)
    out = [np.interp(allf, f, cols[:, j]) for j in range(3)]
    out[0] = _gauss_smooth(out[0], pos_sigma_s * fps)
    out[1] = _gauss_smooth(out[1], pos_sigma_s * fps)
    out[2] = _gauss_smooth(out[2], size_sigma_s * fps)
    return np.stack(out, 1), float(good.mean())


class Track:
    def __init__(self, d):
        self.d = d; self.fps = d["fps"]; self.W = d["width"]; self.H = d["height"]
        self.a = np.array(d["track"], float)  # per frame: cx, eye_y, face_w

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text()))

    def at(self, t):
        i = min(len(self.a) - 1, max(0, int(round(t * self.fps))))
        return self.a[i]

    def crop(self, t, zoom=1.0, aspect=9 / 16, eye_line=0.36, x_offset=0.0, base_face_frac=0.42, face_frac=None):
        """Source-space crop (x, y, w, h). face_frac sets the shot size as the
        face width / crop width (ladder: W .35, H .50, C .67, X .95; default
        base_face_frac). zoom multiplies it, so animate drift with zoom
        (e.g. face_frac=.50, zoom 1.00 -> 1.04 over the hold).
        eye_line is where the eyes sit (fraction from the top);
        x_offset shifts the face sideways (fraction of crop width, + = face moves
        right, opening room on the left). Clamped to the frame; if clamping wins,
        the eye line drifts, so check the shot."""
        cx, ey, fw = self.at(t)
        w = fw / ((face_frac or base_face_frac) * zoom)
        h = w / aspect
        if h > self.H:  # can't be that wide: fit height
            h = self.H; w = h * aspect
        if w > self.W:
            w = self.W; h = w / aspect
        x = cx - w / 2 - x_offset * w
        y = ey - eye_line * h
        x = min(max(0, x), self.W - w); y = min(max(0, y), self.H - h)
        return int(round(x)), int(round(y)), int(round(w)), int(round(h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source"); ap.add_argument("--out", required=True)
    ap.add_argument("--every", type=int, default=3); ap.add_argument("--model")
    ap.add_argument("--debug", help="write a contact sheet with the 1.0x and 1.35x crops drawn")
    a = ap.parse_args()
    rows, fps, W, H, n, det = detect(a.source, a.every, a.model)
    tr, keep = build(rows, fps, n)
    d = {"source": str(Path(a.source).resolve()), "detector": det, "fps": fps, "width": W, "height": H,
         "frames": n, "detections": len(rows), "kept_fraction": round(keep, 3),
         "columns": ["center_x", "eye_y", "face_width"], "track": np.round(tr, 2).tolist()}
    Path(a.out).write_text(json.dumps(d))
    print(f"{det}: {len(rows)} detections over {n} frames, kept {keep:.0%}; "
          f"median face width {np.median(tr[:,2]):.0f}px of {W}x{H}")
    if a.debug:
        T = Track(d); cap = cv2.VideoCapture(a.source); tiles = []
        for t in np.linspace(0, (n - 1) / fps, 12):
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
            if not ok:
                continue
            for z, col in ((1.0, (0, 255, 255)), (1.35, (0, 128, 255))):
                x, y, w, h = T.crop(t, zoom=z)
                cv2.rectangle(fr, (x, y), (x + w, y + h), col, 4)
                cv2.line(fr, (x, int(y + 0.36 * h)), (x + w, int(y + 0.36 * h)), col, 2)
            cv2.putText(fr, f"{t:.1f}s", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
            tiles.append(cv2.resize(fr, (480, int(480 * H / W))))
        rows_ = [np.hstack(tiles[k:k + 4]) for k in range(0, len(tiles) - len(tiles) % 4, 4)]
        cv2.imwrite(a.debug, np.vstack(rows_))
        print("debug sheet:", a.debug)


if __name__ == "__main__":
    main()
