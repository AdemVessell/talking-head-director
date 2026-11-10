"""Hands-free edit: one command from a raw recording to a finished, checked vertical video.

  thd auto RECORDING [--out DIR] [--style auto|NAME] [--brief brief.yaml]
           [--title T] [--points "first point|second point"]
           [--headline H --source S --date D] [--image shot.png] [--stamp REPORTED]
  thd auto RECORDING --draft          only transcribe and autocut: prints the numbered lines to brief from

With nothing but the recording it still finishes: fillers, repeats and long pauses out, a style
picked from the subject, a shot change every few seconds, word-timed captions, designed sound,
the loudness and sync audit and the pre-posting check. A brief makes it an edit with a point of
view. Everything in a brief is the editor's judgement and none of it adds a claim: titles and
points must be the presenter's own words, headlines verbatim with their source.

brief.yaml (every key optional):
  style: timeline                  # thd styles
  title: "THE REAL COST"           # two to four words for the first frame
  keep: [A, B, D, E]               # the story: which lines stay, in this order (ids from --draft)
  drop: [C]                        # or just the lines to leave out
  points:                          # written on a paper as each is said
    - {text: "usage hit 100%", line: B}
    - "serving it cost more than it earned"     # matched to the line that says it
  emphasis: [unsustainable]        # a snap closer on that word
  journey: true                    # the travelling camera on any style (false turns it off)
  headline: "..."  source: "The Verge"  date: "Nov 3"  image: shot.png  stamp: REPORTED
  post: "text to post with the video"           # checked for length and calls to action
  plan: {face: center, flip: true}              # anything else a plan can say (docs/WORKFLOW.md)

Delivers DIR/deliver/: the MP4, captions.srt, thumbnail.png, POST.md (draft text, never posted
by this tool), and the QA, pre-posting and critic reports, plus RESULT.json for the calling agent.
"""
import json, shutil, time
from pathlib import Path

import yaml

from . import audit, autocut, captions, critic, dialogue, news, prep, render, sound, styles, xcheck
from .plan import Plan
from .timeline import Timeline, norm

FACES = [{"shot": "face", "size": "W"}, {"shot": "face", "size": "P", "move": "push"},
         {"shot": "face", "size": "H"}, {"shot": "face", "size": "P", "move": "drift"}]
STOP = news.STOP | {"i", "you", "we", "so", "but", "my", "your", "here", "there", "just", "like", "what", "how",
                    "today", "okay", "ok", "well", "now", "going", "gonna", "want", "about", "have", "has", "do"}


def load_brief(path, cli):
    b = {}
    if path:
        b = yaml.safe_load(Path(path).expanduser().read_text()) or {}
        if not isinstance(b, dict):
            raise SystemExit(f"{path}: a brief is a mapping (see `thd auto --help`)")
    for k, v in cli.items():
        if v:
            b[k] = v
    if isinstance(b.get("points"), str):
        b["points"] = [p.strip() for p in b["points"].split("|") if p.strip()]
    return b


def story(segs, brief):
    """Apply the brief's story choice: keep (in that order) or drop. Unknown ids stop the run."""
    ids = {s["id"]: s for s in segs}
    for key in ("keep", "drop"):
        bad = [i for i in brief.get(key) or [] if i not in ids]
        if bad:
            raise SystemExit(f"brief {key}: no line {', '.join(map(str, bad))} (lines are {segs[0]['id']}..{segs[-1]['id']}; "
                             "see autocut.txt)")
    if brief.get("keep"):
        return [ids[i] for i in brief["keep"]]
    drop = set(brief.get("drop") or [])
    return [s for s in segs if s["id"] not in drop]


def auto_title(segs):
    """Up to three telling words from the first line, when no title was given. A stand-in: a brief's
    title is better, and the result says which was used."""
    words = [w.strip(".,!?;:\"'()").upper() for w in segs[0]["text"].split()]
    keep = [w for w in words if norm(w) and norm(w) not in STOP and len(norm(w)) > 2][:3]
    return " ".join(keep) or None


def match_line(segs, text):
    """Index of the line that says most of `text`'s telling words (None when nothing overlaps)."""
    want = {norm(w) for w in str(text).split()} - STOP - {""}
    best, hit = None, 0
    for k, s in enumerate(segs):
        n = len(want & {norm(w) for w in s["text"].split()})
        if n > hit:
            best, hit = k, n
    return best


def place_points(segs, points):
    """[(text, line index)], each point on the line that says it, in spoken order."""
    ids = [s["id"] for s in segs]; out = []
    for p in points or []:
        text, line = (p.get("text"), p.get("line")) if isinstance(p, dict) else (p, None)
        if not text:
            continue
        k = ids.index(line) if line in ids else match_line(segs, text)
        if k is None:
            k = out[-1][1] if out else min(1, len(segs) - 1)
        out.append((str(text), k))
    return sorted(out, key=lambda x: x[1])


def group_shots(segs, fps, min_shot):
    """Start indexes of shots: a new shot at the first line boundary after min_shot seconds."""
    starts, run = [0], 0.0
    for k, s in enumerate(segs):
        if k and run >= min_shot:
            starts.append(k); run = 0.0
        run += s["out"] - s["in"] + s.get("air", 0) / fps
    return starts


def build_plan(out, base, segs, style_name, brief):
    st = styles.STYLES[style_name]; fps = base["fps"]; ids = [s["id"] for s in segs]; n = len(segs)
    docs, notes = {}, []
    title = brief.get("title") or (auto_title(segs) if st["title_kind"] else None)
    if title and st["title_kind"]:
        docs["title"] = {"kind": st["title_kind"], "lines": [f"h:c:{x}" for x in news.wrap(str(title).upper(), 11)[:3]],
                         "appear": 0}
        notes.append("title from the brief" if brief.get("title") else f"title guessed from the first line: {title!r}")
    pts = place_points(segs, brief.get("points")) if st["points_kind"] else []
    if pts:
        kind = st["points_kind"]
        line = (lambda i, t: f"l:{t}") if kind in ("note", "receipt") else (lambda i, t: f"n:{i + 1}:{t}")
        docs["points"] = {"kind": kind, "lines": [line(i, t) for i, (t, _) in enumerate(pts)],
                          "cues": {i: [f"{ids[k]}.in", f"{ids[k]}.out"] for i, (_, k) in enumerate(pts)}}
    E = None
    label = " · ".join(str(x) for x in (brief.get("source"), brief.get("date")) if x)
    if (brief.get("headline") or brief.get("image")) and n > 1:
        if not brief.get("source"):
            raise SystemExit("name the source of the headline or screenshot (source: ... in the brief, or --source)")
        E = max(1, news.evidence_segment(segs, brief.get("headline")))
        ev = ({"kind": "screenshot", "image": str(Path(brief["image"]).expanduser().resolve()), "source": label}
              if brief.get("image") else
              {"kind": "clipping", "source": label, "lines": news.headline_lines(brief["headline"], label)})
        if brief.get("stamp"):
            ev["stamps"] = [{"at": f"{ids[E]}.out-0.1", "text": str(brief["stamp"]).upper()}]
        docs["evidence"] = ev
    point_at = {}
    for i, (_, k) in enumerate(pts):
        point_at.setdefault(k, i)
    shots = [dict({"at": 0, "shot": "face", "size": "P", "snap": True},
                  **({"docs": [{"doc": "title", "slot": "br"}]} if "title" in docs else {}))]
    starts = group_shots(segs, fps, st["min_shot"]); seen_points = False; kf = 0
    for gi, a in enumerate(starts[1:], 1):
        b = starts[gi + 1] if gi + 1 < len(starts) else n
        here = range(a, b); last = gi == len(starts) - 1
        if E is not None and E in here:
            s = {"shot": "doc", "doc": "evidence"}
        elif any(k in point_at for k in here):
            s = {"shot": "split" if seen_points else "doc", "doc": "points"}; seen_points = True
        elif last and len(docs) >= 2 and n > 3:
            s = {"shot": "desk", "docs": [d for d in ("evidence", "points", "title") if d in docs]}
        else:
            s = dict(FACES[kf % len(FACES)]); kf += 1
        shots.append(dict({"at": f"{ids[a]}.pin"}, **s))
    used = set()
    for word in brief.get("emphasis") or []:   # a snap closer on the word, in the face shot that holds it
        k = next((k for k, s in enumerate(segs) if norm(word) in {norm(w) for w in s["text"].split()}), None)
        if k is None:
            notes.append(f"emphasis {word!r}: not said in the kept lines"); continue
        gi = max(i for i, a in enumerate(starts) if a <= k)
        if shots[gi]["shot"] == "face" and gi not in used:
            shots[gi]["punch"] = f"{ids[k]}.w:{word}"; used.add(gi)
    sfx, journey = [], brief.get("journey", st.get("journey", False))
    if journey:   # the travelling camera: plane changes are punctuation, on at most about half the shot changes
        shots[0]["view"] = "descend"
        moves, first_doc = [], next((i for i, x in enumerate(shots) if x["shot"] == "doc"), None)
        for x in shots[1:]:
            if x["shot"] == "doc":
                x["view"] = "lean"
        if first_doc:
            moves.append((first_doc, "dive"))
            back = next((i for i in range(first_doc + 1, len(shots)) if shots[i]["shot"] == "face"), None)
            if back:
                moves.append((back, "fall"))
        if shots[-1]["shot"] == "desk":
            shots[-1]["view"] = "low"; moves.append((len(shots) - 1, "travel"))
        if not moves and len(shots) > 2:   # no papers: one fall into the second half
            moves.append((len(shots) // 2, "fall"))
        for i, via in moves[:max(1, len(shots) // 2)]:
            shots[i]["via"] = via; notes.append(f"{via} at {shots[i]['at']}")
            sfx.append(dict({"at": shots[i]["at"]}, **news.PLANE_SFX[via]))
    plan = {"name": out.name, "work_dir": str(out / "work"), "source": base["source"], "fps": fps, "tail": 0.9,
            "treatment": st["treatment"], "segments": segs, "documents": docs, "shots": shots,
            "mix": {"voice_chain": "full", "voice_lufs": -16, "lufs": -14, "fade_out": ["END-0.30", "END-0.12"]},
            "end": {"burn": ["END-0.34", "END-0.22"]}, "finish": st["finish"]}
    if journey:
        plan["journey"] = dict(news.JOURNEY)
        if sfx:
            plan["sfx"] = sfx
    for k, v in (st.get("plan") or {}).items():
        plan[k] = {**plan.get(k, {}), **v} if isinstance(v, dict) else v
    for k, v in (brief.get("plan") or {}).items():   # anything else a plan can say (face: center, flip: true, ...)
        plan[k] = {**plan.get(k, {}), **v} if isinstance(v, dict) and isinstance(plan.get(k), dict) else v
    if not docs:
        plan.pop("documents")
    return plan, notes


POST_MAX = 280


def post_text(brief, segs, xm):
    """POST.md: the draft text for the post. Written for a person to read and send; this tool never posts."""
    text = str(brief.get("post") or "").strip()
    rows = []
    if not text:
        rows.append("No post text was given. Write one line in your own voice: what this video shows, no calls to action.")
    else:
        n = len(text)
        rows += [text, "", f"({n} characters" + (f": over {POST_MAX}, trim it" if n > POST_MAX else "") + ")"]
        bad = [f"{level}: {said}" for level, _, said in xcheck.asks([norm(w) for w in text.split()])]
        if bad:
            rows.append("Asks for engagement found (X's rewards rules penalise them): " + "; ".join(map(str, bad)))
    rows += ["", "Before posting: read review notes in X_CHECK.md (" + f"{xm['fail']} fail, {xm['warn']} warn" + ")."]
    return "\n".join(rows) + "\n"


def run(recording, out=None, style="auto", brief_path=None, draft=False, jobs=8, **cli):
    t0 = time.time()
    rec = Path(recording).expanduser().resolve()
    if not rec.exists():
        raise SystemExit(f"no such recording: {rec}")
    out = Path(out or rec.with_suffix("").name + "_edit").expanduser().resolve(); out.mkdir(parents=True, exist_ok=True)
    brief = load_brief(brief_path, cli)
    if style and style != "auto":
        brief["style"] = style
    name = styles.pick("", brief) if (brief.get("style") or "auto") != "auto" else None
    segs = autocut.draft(rec, out, styles.STYLES[name]["pause"] if name else 0.33)
    if not segs:
        raise SystemExit("no speech found in the recording")
    segs = json.loads(json.dumps(segs, default=float))   # plain numbers (autocut hands back numpy floats)
    if draft:
        print("\nLines (write a brief from these; see `thd auto --help`):")
        for s in segs:
            print(f"  {s['id']:>2}  {s['out'] - s['in']:4.1f}s  {s['text']}")
        print(f"\nstyles:\n{styles.table()}")
        return 0
    base = yaml.safe_load((out / "plan_draft.yaml").read_text())
    name = name or styles.pick(" ".join(s["text"] for s in segs), brief)
    segs = story(segs, brief)
    plan_d, notes = build_plan(out, base, segs, name, brief)
    path = out / "plan.yaml"
    path.write_text(f"# thd auto: style {name}. Edit and re-run `thd all plan.yaml` to refine.\n"
                    + yaml.safe_dump(plan_d, sort_keys=False, default_flow_style=None, width=120, allow_unicode=True))
    plan = Plan.load(path)
    prep.extract(plan); prep.extract_films(plan); prep.track(plan); prep.align(plan)
    dialogue.build(plan); tl = Timeline(plan); captions.srt(plan, tl, plan.wp("out", "captions.srt"))
    sound.build(plan, tl); render.render(plan, jobs); mp4 = render.assemble(plan)
    audit.holds(plan); audit.qa(plan, mp4, True); xm = xcheck.run(plan); cr = critic.run(plan, mp4)
    deliver = out / "deliver"; deliver.mkdir(exist_ok=True)
    final = deliver / f"{out.name}.mp4"; shutil.copy(mp4, final)
    for src, dst in ((plan.wp("out", "captions.srt"), "captions.srt"), (plan.wp("review", "QA.md"), "QA.md"),
                     (plan.wp("review", "X_CHECK.md"), "X_CHECK.md"), (plan.wp("review", "CRITIC.md"), "CRITIC.md"),
                     (xm.get("preview"), "thumbnail.png")):
        if src and Path(src).exists():
            shutil.copy(src, deliver / dst)
    (deliver / "POST.md").write_text(post_text(brief, segs, xm))
    result = {"video": str(final), "seconds": round(tl.total, 2), "style": name, "lines": len(segs), "shots": len(plan["shots"]),
              "xcheck": {"fail": xm["fail"], "warn": xm["warn"]}, "critic_fail": cr["fail"], "notes": notes,
              "took_seconds": round(time.time() - t0), "plan": str(path), "deliver": str(deliver),
              "posted": False}
    (deliver / "RESULT.json").write_text(json.dumps(result, indent=1))
    print(f"\nauto: {final}  ({tl.total:.1f} s, style {name}, {len(plan['shots'])} shots, "
          f"pre-posting check {xm['fail']} fail / {xm['warn']} warn, {time.time() - t0:.0f} s)")
    for x in notes:
        print(f"  note: {x}")
    return 1 if xm["fail"] else 0
