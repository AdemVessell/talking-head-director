"""QA: silent-hold strips (the burp check), the pacing/loudness audit, a sync
check against the dialogue edit, and an ASR pass over the finished audio."""
import difflib, json, re, subprocess, sys
import cv2
import numpy as np
import soundfile as sf

from .plan import SCRIPTS
from .stage import Footage
from .timeline import Timeline, norm


def holds(plan, min_len=0.2):
    """Every stretch where the presenter is on screen and not speaking, as a frame strip.
    Look at each one: a silent look-down can be a burp, a swallow, a yawn or a glance away."""
    from .shots import prepare
    tl, _, _ = prepare(plan); fps = plan.fps
    fo = Footage(plan, tl.edl)
    beats = [(tl.t(b["from"]), tl.t(b["to"]), b) for b in plan.get("beats", [])
             if "presenter" in plan["layouts"][b["layout"]]]
    found = []
    for t0, t1, b in beats:
        t, run = t0, None
        while t < t1:
            quiet = not tl.speaking(t, pad=0.04)
            if quiet and run is None:
                run = t
            if (not quiet or t + 1 / fps >= t1) and run is not None:
                end = t if not quiet else t1
                if end - run >= min_len:
                    found.append((b["name"], run, end))
                run = None
            t += 1 / fps
    lines = []
    for k, (name, a, e) in enumerate(found):
        tiles = []
        for i in range(int(a * fps), int(e * fps) + 1, 2):
            rl = fo.map(i / fps); fr = fo.frame(*rl)
            h, w = fr.shape[:2]; s = 240 / h
            tiles.append(cv2.cvtColor(cv2.resize(fr, (int(w * s), 240)), cv2.COLOR_RGB2BGR))
        strip = np.hstack(tiles[:16])
        path = plan.wp("review", f"hold_{k:02d}_{name}.jpg"); cv2.imwrite(str(path), strip)
        lines.append(f"{name}: {a:.2f}-{e:.2f}s ({e - a:.2f}s silent on his face) -> {path.name}")
    text = "\n".join(lines) or "no silent presenter holds"
    plan.wp("review", "holds.txt").write_text(text + "\n")
    print(text)
    return found


def sync_ms(ref_wav, video):
    tmp = video.with_suffix(".qa.wav")
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "48000",
                    "-c:a", "pcm_f32le", str(tmp)], check=True)
    a, sr = sf.read(ref_wav, dtype="float32"); b, _ = sf.read(tmp, dtype="float32")
    n = min(len(a), len(b), int(30 * sr)); A = a[:n] - a[:n].mean(); B = b[:n] - b[:n].mean(); L = int(0.1 * sr)
    xc = np.fft.irfft(np.fft.rfft(B, 2 * n) * np.conj(np.fft.rfft(A, 2 * n))); xc = np.concatenate([xc[-L:], xc[:L + 1]])
    return (np.argmax(xc) - L) / sr * 1000, tmp


def asr_check(plan, wav):
    import warnings
    import stable_whisper
    warnings.filterwarnings("ignore")
    a, sr = sf.read(wav, dtype="float32")
    s16 = np.interp(np.arange(0, len(a), sr / 16000), np.arange(len(a)), a).astype(np.float32)
    m = stable_whisper.load_model("medium.en", device="cpu")
    r = m.transcribe(s16, language="en", word_timestamps=True, vad=False, verbose=None, initial_prompt="Um, uh, hmm.")
    heard = [norm(w.word) for s in r.segments for w in s.words if norm(w.word)]
    want = [norm(w) for s in plan["segments"] for w in s["text"].split() if norm(w)]
    sm = difflib.SequenceMatcher(a=want, b=heard, autojunk=False)
    diffs = [(op, want[i1:i2], heard[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
    return " ".join(heard), diffs


def qa(plan, video, asr=True):
    tl = Timeline(plan)
    out = plan.wp("review", "audit")
    subprocess.run([sys.executable, str(SCRIPTS / "th_audit.py"), str(video), "--words", str(plan.wp("prep", "words_edit.json")),
                    "--out", str(out)], check=True)
    lag, wav = sync_ms(plan.wp("prep", "dialogue_edit.wav"), video)
    lines = [(out / "audit.md").read_text(), f"\n## Sync\n\nFinal audio vs dialogue edit: {lag:+.2f} ms (target: within one frame).\n"]
    if asr:
        heard, diffs = asr_check(plan, wav)
        lines.append("\n## What the finished audio says (ASR)\n\n" + heard + "\n")
        if diffs:
            lines.append("\nDifferences from the plan's text (check each by ear; ASR mishears names and numbers):\n")
            lines += [f"- {op}: expected {' '.join(w) or '-'} / heard {' '.join(h) or '-'}" for op, w, h in diffs]
        else:
            lines.append("\nNo differences from the plan's text.\n")
    wav.unlink(missing_ok=True)
    report = "\n".join(lines)
    plan.wp("review", "QA.md").write_text(report)
    print(report)
    return report
