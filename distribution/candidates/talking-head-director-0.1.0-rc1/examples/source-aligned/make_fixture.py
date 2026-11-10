"""Synthetic source for the source-aligned example. No real recording.

A short picture with a moving red mark, two tap passages at different levels
from the same click shape, one spoken line, and a quiet room-tone span.
Word times are the times this script concatenated, not a transcript of a person.
"""
import shutil, subprocess, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
W, H = 720, 1280
FPS = 24000 / 1001
DUR = 7.2
SR = 48000
WORDS = ["This", "is", "a", "synthetic", "check."]


def speech():
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if not espeak:
        raise SystemExit("fixture needs espeak-ng to build the spoken line")
    blob = Path(espeak).read_bytes()[:2500]
    if blob.startswith(b"#!") and b"flite" in blob:
        raise SystemExit("fixture refused: espeak-ng here is an ffmpeg flite stand-in, not espeak-ng")
    pieces = []
    times = []
    t = 0.30
    gap = int(0.08 * SR)
    silence = np.zeros(gap, np.float32)
    for word in WORDS:
        wav = ROOT / f"_w.wav"
        subprocess.run([espeak, "-s", "130", "-w", str(wav), word], check=True)
        with wave.open(str(wav)) as f:
            raw = f.readframes(f.getnframes())
            sr = f.getframerate()
            sw = f.getsampwidth()
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
        if audio.ndim > 1:
            audio = audio[:, 0]
        if sr != SR:
            audio = np.interp(np.linspace(0, len(audio), int(len(audio) * SR / sr), endpoint=False),
                              np.arange(len(audio)), audio).astype(np.float32)
        nz = np.where(np.abs(audio) > 0.02)[0]
        if len(nz):
            audio = audio[max(0, nz[0] - 80):min(len(audio), nz[-1] + 200)]
        pieces.append(audio)
        times.append({"w": word, "s": round(t, 3), "e": round(t + len(audio) / SR, 3)})
        t += len(audio) / SR
        pieces.append(silence[:int(0.06 * SR)])
        t += 0.06
    (ROOT / "_w.wav").unlink(missing_ok=True)
    return np.concatenate(pieces), times, t


def main():
    voice, times, _ = speech()
    n = int(DUR * SR)
    audio = np.zeros(n, np.float32)
    # place the spoken line at 0.30s, which speech() already timed from 0.30
    offset = int(times[0]["s"] * SR)
    audio[offset:offset + len(voice)] += voice
    click = np.zeros(int(0.04 * SR), np.float32)
    click[:200] = np.hanning(200) * 0.35
    def put(t, gain):
        i = int(t * SR)
        audio[i:i + len(click)] += click * gain
    for k in range(4):
        put(3.30 + k * 0.22, 1.0)
        put(4.80 + k * 0.22, 0.35)
    audio += 0.004 * np.random.default_rng(3).standard_normal(n).astype(np.float32)
    wav = ROOT / "source.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s16le", str(wav)], input=audio.astype(np.float32).tobytes(), check=True)
    frames = int(DUR * FPS)
    vid = ROOT / "_pic.mp4"
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", "24000/1001", "-i", "-", "-c:v", "libx264",
                             "-pix_fmt", "yuv420p", str(vid)], stdin=subprocess.PIPE)
    for i in range(frames):
        t = i / FPS
        img = np.zeros((H, W, 3), np.uint8)
        img[:] = (186, 196, 176)
        img[40:H - 40, 40:W - 40] = (210, 204, 190)
        if 3.2 <= t <= 4.5:
            x = int(360 + 80 * np.sin(t * 3))
            y = int(640 + 40 * np.cos(t * 3))
            yy, xx = np.ogrid[:H, :W]
            img[(xx - x) ** 2 + (yy - y) ** 2 < 18 ** 2] = (220, 32, 28)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
    out = ROOT / "source.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(vid), "-i", str(wav),
                    "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)], check=True)
    (ROOT / "words_src.json").write_text(__import__("json").dumps(times, indent=1))
    vid.unlink(missing_ok=True)
    print("fixture", out, "words", len(times))


if __name__ == "__main__":
    main()
