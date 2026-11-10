"""Environment check: `thd doctor`. One line per requirement, with the fix for
anything missing. FAIL: an edit cannot finish here. WARN: it finishes but loses
something (sound stand-ins, a first-run model download, a busy machine).
INFO: where the skill is linked and its git state. Imports only the standard
library up front, so it still reports when the engine's packages are missing.
"""
import importlib.metadata as md
import importlib.util
import os, re, shutil, subprocess, sys
from pathlib import Path

from .plan import SCRIPTS

SKILL = SCRIPTS.parent
PACKAGES = [("numpy", "numpy"), ("opencv-contrib-python", "cv2"), ("Pillow", "PIL"), ("soundfile", "soundfile"),
            ("PyYAML", "yaml"), ("stable-ts", "stable_whisper"), ("openai-whisper", "whisper"), ("torch", "torch")]
ENCODERS = ["libx264", "prores_ks", "aac"]
FILTERS = ["afftdn", "deesser", "acompressor", "alimiter", "equalizer", "highpass", "loudnorm", "ebur128",
           "aresample", "apad", "atrim", "pan", "drawtext", "tile", "select", "scale", "fps"]


def pins():
    """requirements.txt -> {distribution: version}; commented (optional) lines are skipped."""
    out = {}
    for line in (SKILL / "requirements.txt").read_text().splitlines():
        m = re.match(r"\s*([A-Za-z0-9_.-]+)==([^\s#]+)", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def version(dist, mod):
    if mod == "cv2":  # several opencv distributions provide cv2
        import cv2
        return cv2.__version__
    try:
        return md.version(dist)
    except md.PackageNotFoundError:
        return "?"


def run():
    rows = []
    add = lambda level, what, detail="": rows.append((level, what, detail))

    add("PASS" if sys.version_info >= (3, 9) else "FAIL", "python", f"{sys.version.split()[0]}  {sys.executable}")
    want = pins()
    have = {}
    for dist, mod in PACKAGES:
        if importlib.util.find_spec(mod) is None:
            add("FAIL", dist, f"missing: {sys.executable} -m pip install --user {dist}=={want.get(dist, '')}".rstrip("="))
            continue
        v = have[mod] = version(dist, mod)
        pin = want.get(dist)
        base = v.split("+", 1)[0]  # CPU torch reports 2.8.0+cpu for the 2.8.0 pin
        same = pin in (None, v, base) or (pin or "").startswith(base + ".")  # cv2 reports 4.13.0 for 4.13.0.92
        add("PASS" if same else "WARN", dist, v if same else f"{v} (proven with {pin})")

    ff, fp = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not (ff and fp):
        add("FAIL", "ffmpeg", "ffmpeg/ffprobe not on PATH: install ffmpeg (apt install ffmpeg, or brew install ffmpeg)")
    else:
        ver = subprocess.run([ff, "-version"], capture_output=True, text=True).stdout.split("\n")[0]
        enc = subprocess.run([ff, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
        flt = subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        have_e = {l.split()[1] for l in enc.splitlines() if len(l.split()) > 1}
        have_f = {l.split()[1] for l in flt.splitlines() if len(l.split()) > 1}
        miss = [e for e in ENCODERS if e not in have_e] + [f for f in FILTERS if f not in have_f]
        add("FAIL" if miss else "PASS", "ffmpeg", (f"missing {', '.join(miss)} (a full ffmpeg build has them)" if miss
                                                  else re.sub(r"\s*Copyright.*", "", ver.replace("ffmpeg version ", ""))))

    from . import fonts as F
    rep = F.report(); lost = [r for r, kind, _ in rep if kind is None]; n_open = sum(kind == "open" for _, kind, _ in rep)
    add("FAIL" if lost else "PASS", "fonts",
        f"no file for {', '.join(lost)}: assets/fonts is incomplete" if lost
        else f"{len(rep)} roles: {n_open} open-licensed, {len(rep) - n_open} system")

    model = "medium.en"
    try:
        import inspect
        from . import prep
        model = inspect.signature(prep.align).parameters["model"].default
    except Exception:
        pass
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "whisper" / f"{model}.pt"
    add("PASS" if cache.exists() else "WARN", "whisper model",
        f"{model} cached" if cache.exists() else f"{model} not cached: the first prep downloads ~1.5 GB (needs network)")

    if "cv2" in have:
        import cv2
        haar = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        ok = Path(haar).exists() and not cv2.CascadeClassifier(haar).empty()
        add("PASS" if ok else "FAIL", "face detector", "OpenCV Haar cascade" if ok else f"cannot load {haar}")

    if "numpy" in have and "soundfile" in have:
        from . import sound
        lost = [k for k, (rel, *_) in sound.FILES.items() if not (sound.FCP / rel).exists()]
        add("PASS", "sound kit", (f"{len(sound.FILES) - len(lost)} library sounds, {len(lost)} synthesised"
                                  if lost else f"{len(sound.FILES)} library sounds"))

    cache_dir = Path.home() / ".cache" / "thd_engine"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / ".write_test").write_text("ok"); (cache_dir / ".write_test").unlink()
        add("PASS", "cache", str(cache_dir))
    except OSError as e:
        add("FAIL", "cache", f"{cache_dir} not writable: {e}")

    tts = next((t for t in ("say", "espeak-ng", "espeak") if shutil.which(t)), None)
    stand_in = False
    if tts and tts != "say":
        blob = Path(shutil.which(tts)).read_bytes()[:2500]
        stand_in = blob.startswith(b"#!") and b"flite" in blob
    if stand_in:
        add("WARN", "selftest voice", f"{tts} is an ffmpeg flite stand-in, not espeak-ng. Selftest only. Not a production voice.")
    else:
        add("PASS" if tts else "WARN", "selftest voice", tts or "none: `thd selftest` needs espeak-ng (apt install espeak-ng), or macOS say")
    load, cores = os.getloadavg()[0], os.cpu_count() or 1
    add("WARN" if load > 0.75 * cores else "PASS", "machine",
        f"{cores} cores, load {load:.1f}" + ("  (busy: renders will run slower; see what else is running)"
                                             if load > 0.75 * cores else ""))

    print(f"{SKILL.name} doctor  ({SKILL})")
    for level, what, detail in rows:
        print(f"  {level:4s}  {what:22s} {detail}")
    n = {k: sum(r[0] == k for r in rows) for k in ("PASS", "WARN", "FAIL")}
    print(f"{n['PASS']} pass, {n['WARN']} warn, {n['FAIL']} fail")
    return 1 if n["FAIL"] else 0
