"""Source-aligned edit list. A plan names segments; times on the edit are derived from them.

The story order is the order of `segments` in the plan, which need not follow the source.
FPS and the last frame index come from the source file, not from a fixed recording.
"""
import hashlib, json, math, subprocess
from pathlib import Path


def probe(path):
    raw = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
                                   "-show_entries", "stream=r_frame_rate,duration,nb_frames",
                                   "-show_entries", "format=duration", "-of", "json", str(path)], text=True)
    info = json.loads(raw)
    st = info["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    dur = float(st.get("duration") or info["format"]["duration"])
    n = st.get("nb_frames")
    frames = int(n) if n and n != "N/A" else int(math.floor(dur * fps + 1e-6))
    return {"fps": fps, "duration": dur, "frames": max(1, frames)}


def table_of(segments, tail=0.0):
    t = 0.0
    out = []
    for s in segments:
        a, b = float(s["src_in"]), float(s["src_out"])
        if b <= a:
            raise SystemExit(f"segment {s['id']}: out <= in")
        out.append({"id": s["id"], "src_in": a, "src_out": b, "edit_in": round(t, 4),
                    "edit_out": round(t + (b - a), 4), "role": s.get("role", ""),
                    "room": bool(s.get("room")), "card": list(s.get("card") or []),
                    "sub": s.get("sub", "")})
        t += b - a
    return out, t + float(tail)


class EDL:
    def __init__(self, plan, src_info):
        self.plan = plan
        self.fps = float(plan.get("fps") or src_info["fps"])
        self.src_frames = int(src_info["frames"])
        self.segments, body = table_of(plan["segments"], plan.get("tail") or 0)
        self.dur = body
        self.nframes = int(math.floor(self.dur * self.fps + 1e-6))
        self.by_id = {s["id"]: s for s in self.segments}
        self.room = {s["id"] for s in self.segments if s["room"]}

    def seg_at(self, t):
        for s in self.segments:
            if s["edit_in"] <= t < s["edit_out"]:
                return s
        return self.segments[-1]

    def src_time(self, t):
        s = self.seg_at(t)
        if s["id"] in self.room:
            i = self.segments.index(s)
            prev = self.segments[max(0, i - 1)]
            return prev["src_out"] - 0.02
        return s["src_in"] + min(t, s["edit_out"] - 1e-4) - s["edit_in"]

    def edit_time(self, sid, src_t):
        s = self.by_id[sid]
        return s["edit_in"] + float(src_t) - s["src_in"]

    def preview_table(self):
        want = list(self.plan.get("preview_segments") or [self.segments[0]["id"]])
        rows = [self.by_id[i] for i in want]
        return table_of([{**r, "room": r["room"]} for r in rows], 0.0)

    def fingerprint(self):
        blob = json.dumps([{k: s[k] for k in ("id", "src_in", "src_out", "room")} for s in self.segments], sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()


def work_dir(plan):
    root = Path(plan["_root"])
    work = Path(plan.get("work") or "work")
    if not work.is_absolute():
        work = root / work
    return work.resolve()


def load_plan(path):
    import yaml
    p = Path(path)
    plan = yaml.safe_load(p.read_text())
    root = p.parent
    for key in ("source", "words"):
        if plan.get(key) and not Path(plan[key]).is_absolute():
            plan[key] = str((root / plan[key]).resolve())
    plan["_root"] = str(root)
    plan["_path"] = str(p.resolve())
    return plan
