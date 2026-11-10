"""Edit audio from the source samples named by the EDL.

One gain for the whole edit. Six-millisecond fades only at speech cuts.
Room-tone segments are real spans from the same file, crossfaded under the joins.
A true-peak limiter, if the plan asks for one, starts at one source time
inside one segment. Audio before that time stays at the one gain.
"""
import subprocess
import numpy as np
import soundfile as sf

SR = 48000


def load_audio(src, wav_path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1",
                    "-af", "aresample=48000:resampler=soxr:precision=28", "-c:a", "pcm_f32le", str(wav_path)], check=True)
    audio, sr = sf.read(wav_path, dtype="float64")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, sr


def build(edl, audio, gain_db, tail_room_src=None):
    fade = int(0.006 * SR)
    cross = int(0.040 * SR)
    spans = []
    for s in edl.segments:
        a = int(round(s["src_in"] * SR))
        b = int(round(s["src_out"] * SR))
        spans.append((s, a, b - a))
    tail = int(round((edl.plan.get("tail") or 0) * SR))
    total = sum(n for _, _, n in spans) + tail
    y = np.zeros(total, np.float64)
    pos = 0
    beds = []
    for s, a, n in spans:
        if s["room"]:
            beds.append((pos, a, n))
            pos += n
            continue
        seg = audio[a:a + n].copy()
        if n > 2 * fade:
            ramp = np.linspace(0, 1, fade)
            seg[:fade] *= ramp
            seg[-fade:] *= ramp[::-1]
        y[pos:pos + n] += seg
        pos += n
    if tail and tail_room_src is not None:
        beds.append((pos, int(round(float(tail_room_src) * SR)), tail))
    for p0, a, n in beds:
        lo = min(cross, p0)
        hi = min(cross, total - (p0 + n))
        bed = audio[max(0, a - lo):a + n + hi].copy()
        need = lo + n + hi
        if len(bed) < need:
            bed = np.pad(bed, (0, need - len(bed)))
        env = np.ones(len(bed))
        if lo:
            env[:2 * lo] = np.linspace(0, 1, 2 * lo)
        if hi:
            env[-2 * hi:] = np.linspace(1, 0, 2 * hi)
        y[p0 - lo:p0 + n + hi] += bed[:need] * env[:need]
    y *= 10 ** (float(gain_db) / 20)
    return y


def limit_tail(y, edl, sr=SR):
    """Limiter only from a configured source time. Audio before that point stays at the one gain."""
    spec = edl.plan.get("limiter") or {}
    if not spec:
        return y
    sid = spec["segment"]
    src_t = float(spec["at_source"])
    k = int(round(edl.edit_time(sid, src_t) * sr))
    k = max(0, min(k, len(y) - 1))
    ceiling = 10 ** (float(spec.get("ceiling_db", -1.5)) / 20)
    tmp_in = edl.plan["_work"] / "_speech.wav"
    tmp_out = edl.plan["_work"] / "_speech_lim.wav"
    sf.write(tmp_in, y[k:].astype(np.float32), sr, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp_in), "-af",
                    f"aresample=192000:resampler=soxr,alimiter=limit={ceiling:.4f}:attack=3:release=60:level=0:asc=1:latency=1,aresample=48000:resampler=soxr",
                    "-c:a", "pcm_f32le", str(tmp_out)], check=True)
    sp = sf.read(tmp_out, dtype="float64")[0][:len(y) - k]
    return np.concatenate([y[:k], sp])
