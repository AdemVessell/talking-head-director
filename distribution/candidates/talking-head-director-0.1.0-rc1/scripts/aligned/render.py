"""Preview gate, then the full source-aligned render.

  python3 render.py PLAN preview     first cut only, writes work/preview.mp4
  python3 render.py PLAN approve     records that this cut was accepted
  python3 render.py PLAN full        refuses until approve matches this EDL

Default workers: 3. Eight workers have exhausted memory on a small machine.
Run the engine launcher as `bash scripts/thd` when the executable bit is missing.
"""
import hashlib, json, os, subprocess, sys, time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("OMP_NUM_THREADS", "1")

from edl import EDL, load_plan, probe


def _init(plan_path, preview):
    global C
    from compose import Compose
    ids = None
    if preview:
        plan = load_plan(plan_path)
        ids = list(plan.get("preview_segments") or [])
    C = Compose(plan_path, ids)


def _frame(n):
    return C.frame(n)


def attach_work(edl):
    from edl import work_dir
    edl.work = work_dir(edl.plan)
    edl.work.mkdir(parents=True, exist_ok=True)
    edl.plan["_work"] = edl.work
    return edl


def approval_path(work):
    return Path(work) / "PREVIEW_APPROVED"


def write_approval(edl):
    approval_path(edl.work).write_text(json.dumps({"edl": edl.fingerprint(), "note": "accepted for full render"}))


def require_approval(edl):
    p = approval_path(edl.work)
    if not p.exists():
        raise SystemExit("preview gate: full render is blocked until this cut is approved.\n"
                         "Render preview, watch it, then run: render.py PLAN approve")
    got = json.loads(p.read_text()).get("edl")
    if got != edl.fingerprint():
        raise SystemExit("preview gate: the segment list changed after approval. Approve again.")


def render_cut(plan_path, preview, jobs):
    from compose import Compose
    ids = load_plan(plan_path).get("preview_segments") if preview else None
    probe_c = Compose(plan_path, ids)
    edl = attach_work(probe_c.edl)
    if not preview:
        require_approval(attach_work(EDL(load_plan(plan_path), probe(load_plan(plan_path)["source"]))))
    from audio import build, limit_tail, load_audio
    audio, _ = load_audio(edl.plan["source"], edl.work / "src48.wav")
    # preview audio uses only the preview segments already installed on edl
    y = build(edl, audio, edl.plan.get("gain_db", 0), edl.plan.get("tail_room_src"))
    if not preview and edl.plan.get("limiter"):
        y = limit_tail(y, edl)
    wav = edl.work / ("preview.wav" if preview else "edit.wav")
    import soundfile as sf
    sf.write(wav, y.astype("float32"), 48000, subtype="FLOAT")
    out = edl.work / ("preview.mp4" if preview else "full.mp4")
    fps = edl.fps
    rate = "24000/1001" if abs(fps - 24000 / 1001) < 1e-3 else f"{fps:.6f}"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", rate,
           "-i", "-", "-i", str(wav), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
           "-shortest", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    with Pool(jobs, initializer=_init, initargs=(str(plan_path), bool(preview))) as pool:
        for frame in pool.imap(_frame, range(edl.nframes), chunksize=2):
            proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode:
        raise SystemExit(f"ffmpeg exit {proc.returncode}")
    srt = edl.work / ("preview.srt" if preview else "full.srt")
    from words import write_srt
    write_srt(probe_c.captions, srt, {})
    print(f"{'preview' if preview else 'full'} {out}  {edl.nframes} frames  {time.time() - t0:.1f}s  jobs {jobs}")
    return out


def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: render.py PLAN preview|approve|full [jobs]")
    plan_path, cmd = sys.argv[1], sys.argv[2]
    jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    plan = load_plan(plan_path)
    if cmd == "approve":
        edl = EDL(plan, probe(plan["source"]))
        prev = edl.work / "preview.mp4" if False else Path(plan.get("work") or Path(plan["_root"]) / "work") / "preview.mp4"
        # work dir is created by Compose; use the same rule
        from compose import Compose
        c = Compose(plan_path)
        attach_work(c.edl)
        if not (c.work / "preview.mp4").exists():
            raise SystemExit("preview gate: no preview.mp4 to approve")
        write_approval(c.edl)
        print("approved", c.edl.fingerprint()[:12])
        return
    if cmd == "preview":
        render_cut(plan_path, True, jobs)
        return
    if cmd == "full":
        render_cut(plan_path, False, jobs)
        return
    raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    main()
