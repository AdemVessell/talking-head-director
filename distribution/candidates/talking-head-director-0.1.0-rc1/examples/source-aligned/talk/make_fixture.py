"""Synthetic speech source for the source-aligned example. No marks, no diagram.

Two lines sit in source order. The plan plays the later line first.
Word times are this script's own concatenation record.
"""
import shutil, subprocess, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
W, H = 720, 1280
FPS = 24000 / 1001
DUR = 6.0
SR = 48000
LINES = [("detail", 0.40, ["Detail", "comes", "next."]),
         ("opening", 3.10, ["Start", "with", "this."])]


def espeak_word(espeak, word):
    wav = ROOT / "_w.wav"
    subprocess.run([espeak, "-s", "140", "-w", str(wav), word], check=True)
    with wave.open(str(wav)) as f:
        raw = f.readframes(f.getnframes())
        sr = f.getframerate()
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:
        audio = np.interp(np.linspace(0, len(audio), int(len(audio) * SR / sr), endpoint=False),
                          np.arange(len(audio)), audio).astype(np.float32)
    nz = np.where(np.abs(audio) > 0.02)[0]
    if len(nz):
        audio = audio[max(0, nz[0] - 80):min(len(audio), nz[-1] + 200)]
    return audio


def main():
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if not espeak:
        raise SystemExit("fixture needs espeak-ng")
    blob = Path(espeak).read_bytes()[:2500]
    if blob.startswith(b"#!") and b"flite" in blob:
        raise SystemExit("fixture refused: espeak-ng here is an ffmpeg flite stand-in, not espeak-ng")
    n = int(DUR * SR)
    audio = np.zeros(n, np.float32)
    times = []
    gap = np.zeros(int(0.06 * SR), np.float32)
    for _name, start, words in LINES:
        t = start
        for word in words:
            piece = espeak_word(espeak, word)
            i = int(t * SR)
            audio[i:i + len(piece)] += piece
            times.append({"w": word, "s": round(t, 3), "e": round(t + len(piece) / SR, 3)})
            t += len(piece) / SR + 0.06
        print(_name, "ends", round(t, 3))
    (ROOT / "_w.wav").unlink(missing_ok=True)
    wav = ROOT / "source.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s16le", str(wav)], input=audio.tobytes(), check=True)
    frames = int(DUR * FPS)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", "24000/1001", "-i", "-", "-i", str(wav),
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                             str(ROOT / "source.mp4")], stdin=subprocess.PIPE)
    for i in range(frames):
        img = np.full((H, W, 3), (196, 188, 170), np.uint8)
        img[80:H - 80, 80:W - 80] = (150, 170, 160)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
    (ROOT / "words_src.json").write_text(__import__("json").dumps(times, indent=1))
    print("talk fixture", ROOT / "source.mp4")


if __name__ == "__main__":
    main()
