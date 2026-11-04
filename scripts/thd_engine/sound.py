"""Sound: voice chain on the dialogue edit, a designed SFX track keyed to the
same time expressions as the picture, then a loudness pass on the mix.

plan["sfx"]: [{"kit": "tick", "at": "A.w:5-0.02", "db": -19, "align": "onset"}, ...]
  align: onset (default) | peak | start      dur: seconds (printer, pencil, marker)
  pitch: semitones                            room: true adds a short room tail
Kit (Apple's Final Cut Pro sound library; a missing file gets a synthetic stand-in; paper foley is synthesised):
  printer tick sub lfe lfe_big swish swish_short whoosh shutter thud knock stamp
  pencil marker typewriter (one key per character: "chars", "text") paper_slap flutter tape burn
plan["sfx_auto"] (default on when the plan has shots): every paper event gets its sound from
treatments.SOUNDS: a slap or drop as it lands, tape, each line's pen, keys or print head for
exactly as long as the line takes to appear, red marks, the marker circle, stamps, film prints,
punch-ins and the end burn. Hand-written `sfx` play on top; `sfx_mute: [kit, ...]` silences a kit.
plan["mix"]: {"voice_lufs": -16, "lufs": -14, "voice_chain": "full|light", "fade_out": ["END-0.26", "END-0.10"]}
"""
import subprocess, zlib
from pathlib import Path
import numpy as np
import soundfile as sf

from .plan import SCRIPTS

SR = 48000
FCP = Path("/Library/Audio/Apple Loops/Apple/Final Cut Pro Sound Effects")
FILES = {  # kit name -> (library file, trim-from-onset seconds or None, fade-out)
    "printer": ("Mech:Tech/Adding Machine 1.caf", None, 0.07),
    "tick": ("Mech:Tech/Adding Machine 2.caf", None, 0.05),
    "sub": ("Motions & Transitions/Low Frequency Hit FX.caf", None, 0.05),
    "lfe": ("Impacts & Crashes/LFE Hit Impact 03.caf", 1.3, 0.5),
    "lfe_big": ("Impacts & Crashes/LFE Hit Impact 05.caf", 1.4, 0.6),
    "swish": ("Motions & Transitions/Swish 2.caf", None, 0.03),
    "swish_short": ("Motions & Transitions/Swish 1.caf", None, 0.03),
    "whoosh": ("Motions & Transitions/Whoosh 02.caf", None, 0.1),
    "shutter": ("Mech:Tech/Camera 2.caf", None, 0.05),
    "thud": ("Impacts & Crashes/Thud.caf", None, 0.05),
    "knock": ("Impacts & Crashes/Impact Knock.caf", None, 0.05),
    "pencil": ("Work:Home/Pencil Writing.caf", None, 0.08),
    "typewriter": ("Work:Home/Typewriter Manual.caf", None, 0.02),
}
rng = np.random.default_rng(9)


def load(plan, name):
    """Library sound -> mono 48 kHz float, peak-normalised; cached in work/sfx."""
    rel = FILES[name][0]
    out = plan.wp("sfx", Path(rel).stem.replace(" ", "_") + ".wav")
    if not out.exists():
        src = FCP / rel
        if not src.exists():
            return stand_in(name)
        # every channel folded in (the LFE hits are 5.1 with the hit on the LFE channel)
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=channels", "-of", "csv=p=0",
                                f"file:{src}"], capture_output=True, text=True).stdout.strip()
        ch = int(probe or 2)
        pan = "pan=mono|c0=" + "+".join(f"c{i}" for i in range(ch))
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", f"file:{src}", "-af", pan,
                        "-ar", str(SR), "-c:a", "pcm_f32le", str(out)], check=True)
    a, sr = sf.read(out, dtype="float32")
    return a / (np.abs(a).max() + 1e-9)


_missing = set()


def stand_in(name):
    """A plain synthetic tick for a library sound that is not installed, so the edit still
    finishes (`thd doctor` lists what is missing). Not cached: the real file wins once it exists."""
    if name not in _missing:
        _missing.add(name)
        print(f"sound: {FCP / FILES[name][0]} is missing; '{name}' uses a synthetic stand-in")
    n = int(0.12 * SR)
    tick = bandnoise(0.12, 1800, 7000)[:n] * np.exp(-np.linspace(0, 9, n)).astype(np.float32)
    return np.concatenate([np.zeros(int(0.1 * SR), np.float32), tick])


def onset(a, frac=0.1):
    return int(np.argmax(np.abs(a) > frac * np.abs(a).max()))


def fade(a, fin=0.003, fout=0.06):
    a = a.copy(); n1 = int(fin * SR); n2 = min(len(a), int(fout * SR))
    if n1:
        a[:n1] *= np.linspace(0, 1, n1)
    if n2:
        a[-n2:] *= np.linspace(1, 0, n2)
    return a


def pitch(a, semis):
    r = 2 ** (semis / 12)
    return np.interp(np.arange(0, len(a) - 1, r), np.arange(len(a)), a).astype(np.float32)


def bandnoise(dur, lo, hi):
    n = int(dur * SR); x = rng.standard_normal(n).astype(np.float32)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n).astype(np.float32)
    return y / (np.abs(y).max() + 1e-9)


def paper_slap(dur=0.16):
    t = np.arange(int(dur * SR)) / SR
    y = bandnoise(dur, 700, 7000) * np.exp(-t / 0.035) + 0.5 * np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.03)
    return y / np.abs(y).max()


def flutter(dur=0.24):
    t = np.arange(int(dur * SR)) / SR
    am = 0.55 + 0.45 * np.sin(2 * np.pi * 26 * t + rng.uniform(0, 6)) ** 2
    y = bandnoise(dur, 900, 6500) * am * np.sin(np.pi * t / dur) ** 0.7
    return y / np.abs(y).max()


def tape(dur=0.13):
    n = int(dur * SR); t = np.arange(n) / SR
    clicks = (rng.random(n) > 0.985).astype(np.float32) * rng.uniform(0.3, 1, n)
    y = np.convolve(clicks, np.exp(-np.arange(60) / 8.0), mode="same") * bandnoise(dur, 2000, 9000)
    y = y * np.sin(np.pi * t / dur) ** 0.5
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def room(a, rt=0.32, wet_db=-13):
    n = int(rt * SR); t = np.arange(n) / SR
    ir = bandnoise(rt, 150, 5000) * np.exp(-6.9 * t / rt)
    wet = np.convolve(a, ir) / (np.abs(ir).sum() ** 0.5 + 1e-9)
    out = np.zeros(len(wet), np.float32); out[:len(a)] = a
    return out + wet / (np.abs(wet).max() + 1e-9) * 10 ** (wet_db / 20)


def keystrokes(plan):
    """Single key strikes cut from the typewriter recording (not the two carriage returns)."""
    p = plan.wp("sfx", "keystrokes.npy")
    if p.exists():
        return list(np.load(p))
    a = load(plan, "typewriter"); hop = 240
    env = np.array([np.abs(a[i:i + hop]).max() for i in range(0, len(a) - hop, hop)])
    on = []
    for i in range(12, len(env)):
        if env[i] > 0.08 and env[i] > 3.5 * (np.median(env[i - 12:i]) + 1e-4) and (not on or i - on[-1] > 10):
            on.append(i * hop)
    keys = []
    for k, s in enumerate(on):
        t = s / SR
        if min(abs(t - 20.07), abs(t - 40.67)) < 0.6:
            continue
        nxt = on[k + 1] if k + 1 < len(on) else len(a)
        n = min(int(0.11 * SR), nxt - s - int(0.004 * SR))
        if n < int(0.06 * SR):
            continue
        keys.append(fade(a[max(0, s - 200):s - 200 + n], fin=0.002, fout=0.02))
    pk = np.array([np.abs(x).max() for x in keys]); lo, hi = np.percentile(pk, [25, 90])
    keys = [x / np.abs(x).max() for x, v in zip(keys, pk) if lo <= v <= hi][:32]
    np.save(p, np.array([np.pad(x, (0, int(0.11 * SR) - len(x))) for x in keys]))
    return keys


def typing(plan, cue):
    """One key strike per character, each on the frame its character appears."""
    keys = keystrokes(plan); n = max(1, int(cue.get("chars", 8))); dur = float(cue.get("dur", 0.5))
    text = cue.get("text", "x" * n); r = np.random.default_rng(zlib.crc32(text.encode()))  # hash() changes per run
    y = np.zeros(int((dur + 0.15) * SR), np.float32)
    for k in range(1, n + 1):
        s = int(k / n * dur * SR); x = keys[int(r.integers(len(keys)))]
        g = 10 ** (r.uniform(-2.5, 1.0) / 20) * (0.55 if k - 1 < len(text) and text[k - 1] == " " else 1.0)
        y[s:s + len(x)] += x[:len(y) - s] * g
    return y


def kit(plan, name, cue):
    if name in ("paper_slap", "flutter", "tape"):
        return {"paper_slap": paper_slap, "flutter": flutter, "tape": tape}[name](), "onset"
    if name == "stamp":  # thud + knock + a short room
        thud, knock = load(plan, "thud"), load(plan, "knock")
        p = cue.get("pitch", 0.0)
        th = room(pitch(thud, p) if p else thud)
        kn = pitch(knock, p) if p else knock
        off = int(np.argmax(np.abs(th))) - int(np.argmax(np.abs(kn)))  # peaks together, knock 8 dB under
        pre = max(0, -off); y = np.zeros(max(len(th) + pre, len(kn) + max(0, off)), np.float32)
        y[pre:pre + len(th)] += th
        y[pre + off:pre + off + len(kn)] += 0.4 * kn
        return y, "peak"
    if name == "typewriter":
        return typing(plan, cue), "start"
    if name == "marker":  # felt tip: the pencil recording, lighter and squeakier
        cue = dict(cue, pitch=cue.get("pitch", 3)); name = "pencil"
    if name == "burn":
        sw = load(plan, "swish")
        return fade(sw[::-1].copy(), fin=0.08, fout=0.02), "peak"
    a = load(plan, name)
    _, trim, fo = FILES[name]
    o = onset(a)
    if name in ("printer", "pencil"):
        n = int(cue.get("dur", 0.4 if name == "printer" else 0.5) * SR)
        start = o if name == "printer" else int(0.12 * SR)
        if cue.get("vary") and len(a) - start > n + SR:  # a different stretch of the recording each time
            start += int((cue["vary"] * 7919) % (len(a) - start - n - 1))
        a = a[start:start + n]
        if name == "pencil":
            a = pitch(a, cue.get("pitch", -3))
        return fade(a, fin=0.01 if name == "pencil" else 0.003, fout=fo), "start"
    if trim:
        a = fade(a[o:o + int(trim * SR)], fout=fo)
    elif name == "tick":
        a = fade(a[o:], fout=fo)
    if cue.get("pitch") and name != "pencil":
        a = pitch(a, cue["pitch"])
    if cue.get("room"):
        a = room(a)
    default = "peak" if name in ("swish", "swish_short", "whoosh", "shutter", "thud", "knock") else "onset"
    return a, default


def auto_cues(plan, tl):
    """Sound for every paper event the plan already times (see the module notes)."""
    from . import shots, treatments
    if not plan.get("sfx_auto", bool(plan.get("shots"))):
        return []
    _, meta, lv = shots.prepare(plan, tl)
    out = []
    for name, life in lv.items():
        snd = treatments.SOUNDS.get(life["kind"], {}); m = meta["docs"][name]
        if "slap" in life:
            out.append({"kit": snd.get("enter", "paper_slap"), "at": life["slap"], "db": -22})
        if "drop" in life:
            t0, t1, _ = life["drop"]
            out += [{"kit": "flutter", "at": t0 + 0.02, "db": -27}, {"kit": snd.get("land", "paper_slap"), "at": t1 - 0.01, "db": -24}]
        if "tape_at" in life:
            out.append({"kit": "tape", "at": life["tape_at"], "db": -27})
        for i, (t0, t1, mode) in sorted(life["cues"].items()):
            L = m["lines"][i]
            if mode == "ink":
                out.append({"kit": snd.get("pop", "tick"), "at": t0 - 0.02, "db": -21})
            elif mode == "type" and L.get("xs"):
                out.append({"kit": "typewriter", "at": t0, "dur": t1 - t0, "chars": len(L["xs"]), "text": L["text"],
                            "db": -23, "align": "start"})
            elif snd.get("reveal"):
                out.append({"kit": snd["reveal"], "at": t0, "dur": max(0.2, t1 - t0), "db": -25, "align": "start",
                            "vary": round(t0, 2)})
        for i, (t0, t1, _) in sorted(life["marks"].items()):
            out.append({"kit": snd.get("mark", "pencil"), "at": t0, "dur": max(0.18, t1 - t0), "db": -23, "align": "start",
                        "vary": round(t0, 2)})
        if "marker" in life:
            m0, m1, _ = life["marker"]
            out.append({"kit": "marker", "at": m0, "dur": m1 - m0 + 0.08, "db": -21, "align": "start", "vary": round(m0, 2)})
        for st in life["stamps"]:
            out.append({"kit": "stamp", "at": st["at"], "db": -8})
    for b in plan.get("beats", []):
        for f in plan["layouts"][b["layout"]].get("films", []):
            if f.get("slap", True):
                out.append({"kit": "paper_slap", "at": f.get("appear", b["from"]), "db": -23})
    for s in plan.get("shots") or []:
        if s.get("punch"):
            out.append({"kit": "swish_short", "at": tl.t(s["punch"]) + 0.02, "db": -22})
    if plan.get("end", {}).get("burn"):
        out.append({"kit": "burn", "at": tl.t(plan["end"]["burn"][1]), "db": -24})
    mute = set(plan.get("sfx_mute", []))
    seen, uniq = set(), []
    for c in out:  # one sound per event, even when two papers share a cue
        k = (c["kit"], round(float(tl.t(c["at"])), 2))
        if c["kit"] not in mute and k not in seen:
            seen.add(k); uniq.append(c)
    plan.wp("review", "sfx_auto.json").write_text(__import__("json").dumps(uniq, indent=1, default=float))
    return uniq


def build(plan, tl):
    total = tl.total
    buf = np.zeros(int(total * SR) + SR, np.float32)
    for cue in auto_cues(plan, tl) + plan.get("sfx", []):
        a, default_align = kit(plan, cue["kit"], cue)
        align = cue.get("align", default_align)
        i = {"onset": onset(a), "peak": int(np.argmax(np.abs(a))), "start": 0}[align]
        s = int(round(tl.t(cue["at"]) * SR)) - i
        a = a * 10 ** (cue.get("db", -18) / 20)
        if s < 0:
            a = a[-s:]; s = 0
        buf[s:s + len(a)] += a[:len(buf) - s]
    buf = buf[:int(total * SR)]
    sf.write(plan.wp("render", "sfx.wav"), buf, SR, subtype="FLOAT")
    mix = plan.get("mix", {})
    chain = str(SCRIPTS / "voice_chain.sh")
    # "full": cleanup chain for raw recordings; "light": loudness only, for audio that is
    # already produced (downloads) or where relative levels are the evidence (a tap test)
    args = [str(mix.get("voice_lufs", -16))] + (["--mix"] if mix.get("voice_chain", "full") == "light" else [])
    subprocess.run(["bash", chain, str(plan.wp("prep", "dialogue_edit.wav")), str(plan.wp("render", "voice.wav"))] + args,
                   check=True)
    v, sr = sf.read(plan.wp("render", "voice.wav"), dtype="float32"); assert sr == SR
    v = v[:len(buf)]
    if len(v) < len(buf):
        v = np.pad(v, (0, len(buf) - len(v)))
    if mix.get("fade_out"):  # room tone and voice end with the picture (e.g. on a film burn)
        a, b = (tl.t(x) for x in mix["fade_out"])
        n0, n1 = int(a * SR), int(b * SR)
        v[n0:n1] *= np.linspace(1, 0, max(1, n1 - n0)); v[n1:] = 0
    sf.write(plan.wp("render", "mix_pre.wav"), v + buf, SR, subtype="FLOAT")
    subprocess.run(["bash", chain, str(plan.wp("render", "mix_pre.wav")), str(plan.wp("render", "mix.wav")),
                    str(mix.get("lufs", -14)), "--mix"], check=True)
