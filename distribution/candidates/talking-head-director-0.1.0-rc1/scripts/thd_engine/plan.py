"""Load a per-video edit plan (JSON or YAML) and lay out its work directory.

The plan is the single source of truth for one edit: source, story segments,
layouts, beats, receipts, captions and sound cues. All times inside it are
time expressions (see timeline.py), never typed seconds, except segment
source in/out points.
"""
import json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "fps": 30,
    "size": [1080, 1920],
    "finish": "medium",
    "tail": 1.0,          # seconds after the last segment (callback, ending)
    "flip": False,        # mirror the source (set True if the recording is mirrored)
    "margins": [1.2, 1.2],  # extraction handles around each segment (s)
}
CAPTION_DEFAULTS = {"y": 1330, "size": 80, "max_width": 920, "hide": [], "keywords": []}


class Plan(dict):
    """dict with resolved paths. `plan.wp("prep", "edl.json")` -> work-dir path."""

    @classmethod
    def load(cls, path):
        p = Path(path).expanduser().resolve()
        text = p.read_text()
        if p.suffix in (".yaml", ".yml"):
            import yaml
            d = yaml.safe_load(text)
        else:
            d = json.loads(text)
        plan = cls({**DEFAULTS, **d})
        plan.path = p
        plan["captions"] = {**CAPTION_DEFAULTS, **d.get("captions", {})}
        work = Path(plan.get("work_dir") or (p.parent / "work")).expanduser()
        if not work.is_absolute():
            work = (p.parent / work).resolve()
        plan.work = work
        for sub in ("prep", "materials", "sfx", "render", "review", "out"):
            (work / sub).mkdir(parents=True, exist_ok=True)
        plan.validate()
        return plan

    def wp(self, *parts):
        return self.work.joinpath(*parts)

    @property
    def W(self):
        return int(self["size"][0])

    @property
    def H(self):
        return int(self["size"][1])

    @property
    def fps(self):
        return float(self["fps"])

    def segment(self, sid):
        return next(s for s in self["segments"] if s["id"] == sid)

    def validate(self):
        need = ["source", "segments"]
        missing = [k for k in need if k not in self]
        if missing:
            raise SystemExit(f"plan is missing {missing}")
        ids = [s["id"] for s in self["segments"]]
        if len(ids) != len(set(ids)):
            raise SystemExit("segment ids must be unique")
        for s in self["segments"]:
            if s["out"] <= s["in"]:
                raise SystemExit(f"segment {s['id']}: out <= in")
            if "text" not in s:
                raise SystemExit(f"segment {s['id']}: needs 'text' (verbatim words for forced alignment)")
        for b in self.get("beats", []):
            if b.get("layout") not in self.get("layouts", {}):
                raise SystemExit(f"beat {b.get('name')}: unknown layout {b.get('layout')}")
