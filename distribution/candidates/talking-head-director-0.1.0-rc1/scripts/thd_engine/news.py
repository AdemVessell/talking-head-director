"""News shorts in one command (see docs/WORKFLOW.md):

  thd news RECORDING --out DIR [--look newsroom|lab] [--title "AI NEWS"]
           [--headline "the verbatim headline" --source "The Verge" --date "Nov 3"] [--image shot.png]
           [--stamp REPORTED|UNCONFIRMED|CONFIRMED] [--flat]

Runs autocut, then writes DIR/plan.yaml in the news shape, one shot per kept line:
  0          his face with a title sticky: the first frame is the thumbnail
  evidence   the line where he states the news (the first segment that says the headline's
             words, else the second): a screenshot print (--image) or a clipping carrying the
             verbatim headline and its source, stamped if --stamp is given
  take       a wider face for his take
  then       split (him and the evidence) / face P / face W, alternating
  last line  the desk: every paper
By default it is drafted as a colour journey: the camera descends
onto him on frame 0, papers being read lean, and plane changes with their own air dive into the
evidence, travel to the desk and fall back to his take, on at most half the shot changes
(docs/WORKFLOW.md). --flat drafts the plain rostrum camera instead.
The draft renders as it stands. The editor's work is the story (reorder, drop, merge), the
papers (his words; headlines verbatim) and the stamps. Nothing here writes a claim: the
headline and the source come from the command line, everything else from his transcript.
"""
from pathlib import Path
import yaml

from . import autocut
from .timeline import norm

JOURNEY = {"focal": 1.15, "dark": 0.35, "fog": 0.9, "dof": 0.8, "pulse": 0.12, "pulses": []}
PLANE_SFX = {"dive": {"kit": "whoosh", "db": -21, "pitch": -2}, "fall": {"kit": "whoosh", "db": -21, "pitch": -4},
             "travel": {"kit": "swish", "db": -20}, "flip": {"kit": "swish_short", "db": -19}}
STOP = {"a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "is", "are", "was", "were", "be", "it", "its",
        "at", "by", "with", "as", "from", "this", "that", "new", "says", "after", "over"}


def wrap(text, width):
    lines, cur = [], ""
    for w in str(text).split():
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + ([cur] if cur else [])


def evidence_segment(segs, headline):
    """The first kept line that says enough of the headline's words; else the second line."""
    want = {norm(w) for w in str(headline or "").split()} - STOP - {""}
    if want:
        need = min(len(want), max(2, round(0.4 * len(want))))
        for k, s in enumerate(segs):
            if len(want & {norm(w) for w in s["text"].split()}) >= need:
                return k
    return 1 if len(segs) > 1 else 0


def headline_lines(headline, label):
    """A clipping: the headline verbatim (big type while it fits in four lines), a rule, then "VIA" and the
    source, so it reads as a quotation in his look, never as the outlet's own page."""
    big = wrap(headline, 15)
    lines = [f"h:{x}" for x in big] if len(big) <= 4 else [f"l:{x}" for x in wrap(headline, 34)]
    return lines + ["rule", f"c:VIA {label.upper()}"]


def draft(recording, out, look="newsroom", title=None, headline=None, source=None, date=None, image=None,
          stamp=None, pause=0.35, flat=False):
    if look not in ("newsroom", "lab"):
        raise SystemExit("--look is newsroom (kraft desk, clippings) or lab (linen desk, printouts)")
    if (headline or image) and not source:
        raise SystemExit('name the source: --source "The Verge" (every headline and screenshot shows where it came from)')
    out = Path(out).expanduser().resolve(); out.mkdir(parents=True, exist_ok=True)
    segs = autocut.draft(Path(recording).expanduser().resolve(), out, pause)
    if not segs:
        raise SystemExit("no speech found in the recording")
    base = yaml.safe_load((out / "plan_draft.yaml").read_text())
    ids, n = [s["id"] for s in segs], len(segs)
    label = " · ".join(str(x) for x in (source, date) if x)
    docs = {"title": {"kind": "sticky", "lines": [f"h:c:{x}" for x in wrap(str(title or "NEWS").upper(), 11)[:3]],
                      "appear": 0}}
    E = None
    if (image or headline) and n > 1:
        E = max(1, evidence_segment(segs, headline))
        if image:
            ev = {"kind": "screenshot", "image": str(Path(image).expanduser().resolve()), "source": label}
        else:
            ev = {"kind": "clipping", "source": label, "lines": headline_lines(headline, label)}
        if stamp:
            ev["stamps"] = [{"at": f"{ids[E]}.out-0.1", "text": str(stamp).upper()}]
        docs["evidence"] = ev
    by = {}
    if E is not None:
        by[E] = {"shot": "doc", "doc": "evidence"}
    if n > 2 and n - 1 not in by:
        by[n - 1] = {"shot": "desk", "docs": [d for d in ("evidence", "title") if d in docs]}
    take = E + 1 if E is not None else 1
    if take < n and take not in by:
        by[take] = {"shot": "face", "size": "W"}
    before = [{"shot": "face", "size": "W"}, {"shot": "split", "doc": "title"},  # the evidence waits for its line
              {"shot": "face", "size": "P"}]
    after = ([{"shot": "split", "doc": "evidence"}] if E is not None else []) + \
        [{"shot": "face", "size": "P"}, {"shot": "face", "size": "W", "move": "push"}]
    kb = ka = 0
    for i in range(1, n):
        if i in by:
            continue
        if E is not None and i > E:
            by[i] = after[ka % len(after)]; ka += 1
        else:
            by[i] = before[kb % len(before)]; kb += 1
    shots = [{"at": 0, "shot": "face", "size": "P", "docs": [{"doc": "title", "slot": "br"}], "snap": True}]
    shots += [dict({"at": f"{ids[i]}.pin"}, **by[i]) for i in sorted(by)]   # shots[i] is line i
    sfx, moved = [], []
    if not flat:  # the house colour journey
        shots[0]["view"] = "descend"
        for s in shots[1:]:
            if s["shot"] == "doc":
                s["view"] = "lean"   # a paper being read stays near flat
        moves = []   # plane changes are punctuation: the strongest first, at most about half the shot changes
        if E is not None:
            moves.append((E, "dive"))   # into the evidence
        if n > 2 and shots[n - 1]["shot"] == "desk":
            shots[n - 1]["view"] = "low"; moves.append((n - 1, "travel"))   # across to the whole desk
        if E is not None and take < n - 1 and shots[take]["shot"] == "face":
            moves.append((take, "fall"))   # the evidence falls away: his take
        for i, via in moves[:max(1, n // 2)]:
            shots[i]["via"] = via; moved.append(f"{via} at {shots[i]['at']}")
            sfx.append(dict({"kit": PLANE_SFX[via]["kit"], "at": shots[i]["at"]},
                            **{k: v for k, v in PLANE_SFX[via].items() if k != "kit"}))
    plan = {"name": out.name, "work_dir": str(out / "work"), "source": base["source"], "fps": base["fps"], "tail": 0.9,
            "treatment": look, "segments": base["segments"], "documents": docs,
            **({} if flat else {"journey": dict(JOURNEY)}), "shots": shots, **({"sfx": sfx} if sfx else {}),
            "mix": {"voice_chain": "full", "voice_lufs": -16, "lufs": -14, "fade_out": ["END-0.30", "END-0.12"]},
            "end": {"burn": ["END-0.34", "END-0.22"]}, "finish": "medium"}
    late = E is not None and E > max(2, n // 3)
    if late:
        print(f"  [news] the news is stated on line {E + 1} of {n}: it lands better in the first ten seconds; "
              f"consider moving {ids[E]} up")
    head = [f"# News draft (thd news): {headline or 'no headline given'}",
            (f"# Evidence on {ids[E]}: {segs[E]['text'][:80]!r}" if E is not None
             else "# No evidence paper: add one with --image or --headline (and --source)"),
            *([f"# The news is stated late (line {E + 1} of {n}): consider moving {ids[E]} up to the hook."] if late else []),
            *(["# Look: flat (the rostrum camera, --flat)."] if flat else
              ["# Look: the colour journey (docs/WORKFLOW.md). The camera descends onto the presenter; plane changes:",
               f"#   {', '.join(moved) or 'none'}, hard cuts between. Add pulses on the words that land.",
               "#   This package has no Blender diorama kit. Do not invent a scene to fill that slot."]),
            "# Renders as it stands: thd prep plan.yaml, thd inspect plan.yaml (fix every !), thd all plan.yaml.",
            "# Before posting (thd xcheck checks the starred lines):",
            "#    - Story: hook first (the news in one line), then the source, his take, why it matters, the verdict.",
            "#      Reorder or drop segments and keep his hedges; the shots follow the segments, so re-check them.",
            "#    * Headlines are verbatim, and every screenshot or clipping names its source (source: ...).",
            "#    - Stamp anything unconfirmed: stamps: [{at: ..., text: UNCONFIRMED}] (or REPORTED, CONFIRMED).",
            "#    - Screenshots are real captures. Never rebuild a post or a headline to look real.",
            "#    * No calls to action: never ask for likes, reposts, replies or follows.",
            "#    * Check every number and name listed in review/X_CHECK.md before posting."]
    path = out / "plan.yaml"
    path.write_text("\n".join(head) + "\n" + yaml.safe_dump(plan, sort_keys=False, default_flow_style=None, width=120,
                                                          allow_unicode=True))
    print(f"news plan -> {path}  ({n} lines, evidence on {ids[E] if E is not None else 'none'}, {len(shots)} shots, "
          f"{'flat' if flat else 'colour journey'})")
    return path
