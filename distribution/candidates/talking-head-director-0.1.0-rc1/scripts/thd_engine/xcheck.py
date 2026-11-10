"""X pre-posting check: `thd xcheck PLAN`, also the last step of `thd all`. Writes review/X_CHECK.md
and review/x_feed_preview.png (the first frame at phone-feed width).

Why (third-party reporting, Nov 2026; help.x.com refuses automated reads, so confirm in Creator
Studio): X's Original Content Rewards pays only for original posts, and accounts that keep asking
for likes, reposts, replies or follows are reportedly removed. Under the older program a post
corrected by Community Notes earned nothing, so every number and name is listed to check.

  FAIL  a call to action, spoken or printed; a screenshot or clipping that names no source
  WARN  spoken words neither captioned nor on paper; no title on the first frame, or title text
        under 14 px at feed width; the first word later than 0.5 s; captions under 20 px at feed
        width; a file over 512 MB; a soft ask ("let me know what you think")
  INFO  claims to verify (numbers, $, %, names) with their times; length over 140 s; one- or
        two-word captions dropped on purpose between two papers
"""
import re, subprocess

import numpy as np
from PIL import Image

from . import captions, materials, render
from .timeline import norm

FEED_W = 390  # a phone feed is about this many points wide
CTA = [  # over normalised words ("don't" -> "dont"): asks for engagement, never plain "like"
    r"\b(hit|smash|tap|press|leave|drop) (that |the |a )?(like|follow|repost|retweet|subscribe)\b",
    r"\bgive (it|this|me|us) a (like|follow|repost|retweet|share)\b",
    r"\blike (and|or) (subscribe|follow|share|repost|retweet|comment|reply)\b",
    r"\b(share|repost|retweet) (and|or) (follow|subscribe|like)\b",
    r"\blike this (post|video|tweet|clip) if\b", r"\b(please|go) like this\b",
    r"\b(please |go )?(repost|retweet) this\b",
    r"\bshare this (post|video|clip|tweet)\b",
    r"\bshare (this|it) with (a friend|someone|your|everyone)\b",
    r"\bfollow (me|us) for\b", r"\bfollow for (more|part)\b",
    r"\b(make sure|be sure|dont forget|remember) (to|you) (like|follow|subscribe|repost|retweet|share|comment)\b",
    r"\bsubscribe (to|for) (me|my|the|more)\b",
    r"\b(comment|reply|let me know|tell me|sound off) (down )?below\b",
    r"\b(let me know|tell me|sound off) (down )?in the (comments|replies)\b",
    r"\bdrop (a|your) (comment|reply|thoughts)\b",
    r"\bturn on (post |the )?notifications\b", r"\bhit the bell\b",
    r"\blink in (my |the )?(bio|description)\b",
]
SOFT = [r"\b(let me know|tell me) what you think\b"]
OWN = {"own", "his words", "own words", "his own words", "my words"}
PLAIN = {"I", "I'm", "I'll", "I've", "I'd", "AI", "OK", "Okay"}


def asks(tokens):
    """[(level, first word index, phrase)] for every call to action in a run of words."""
    s = " ".join(tokens); starts, pos, out = [], 0, []
    for tk in tokens:
        starts.append(pos); pos += len(tk) + 1
    for level, pats in (("FAIL", CTA), ("WARN", SOFT)):
        for p in pats:
            for m in re.finditer(p, s):
                out.append((level, max(k for k, st in enumerate(starts) if st <= m.start()), m.group(0)))
    return out


def stamp(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def claim_runs(words, spoken=True):
    """Runs of words worth checking: numbers, $, % and names. On paper only numbers and inner capitals
    (OpenAI, GPT-6) count, since printed type is often all caps."""
    flags = []
    for i, w in enumerate(words):
        x = w.strip(".,!?;:\"'()“”‘’")
        num = bool(re.search(r"[\d$%]", x))
        inner = len(x) > 1 and any(ch.isupper() for ch in x[1:]) and not x.isupper() and x not in PLAIN
        start = i == 0 or words[i - 1][-1:] in ".?!"
        name = spoken and x[:1].isupper() and not start and x not in PLAIN
        flags.append(bool(x) and (num or inner or name or (spoken and x.isupper() and len(x) > 1 and x not in PLAIN)))
    runs, cur = [], []
    for i, f in enumerate(flags):
        if f:
            cur.append(i)
        elif cur:
            runs.append(cur); cur = []
    return runs + ([cur] if cur else [])


def title_heights(R):
    """[(document, its tallest revealed text line in output px)] for every paper on the first frame."""
    st = R.stage; b = st.beat_at(0.0); _, (_, _, z) = st.cam(0.0); placed = st.lay_docs(b["lay"]); out = []
    for name in b["docs"]:
        doc = st.docs[name]; s = doc.state(0.0, st.lives.get(name, {}), st.fps)
        if s is None:
            continue
        hs = [ink.shape[0] for (L, ink, _), (k, _) in zip(doc.lines, s) if k > 0 and L.get("text") and not L.get("caption")]
        if hs:
            out.append((name, max(hs) * placed[name]["width"] / doc.m["w"] * z))
    return out


def run(plan, R=None):
    R = R or render.Renderer(plan)
    tl, W = R.tl, R.tl.words
    meta = __import__("json").loads(plan.wp("materials", "meta.json").read_text())
    rows, claims = [], []
    add = lambda level, what, detail="": rows.append((level, what, detail))
    feed = FEED_W / plan.W

    # 1. calls to action, said or printed
    found = [(lv, f"said at {stamp(W[k]['start'])}: \"{ph}\"") for lv, k, ph in asks([norm(w["word"]) for w in W])]
    for name, m in meta["docs"].items():
        for L in m["lines"]:
            if L.get("text"):
                found += [(lv, f"printed on {name}: \"{ph}\"") for lv, _, ph in asks([norm(x) for x in L["text"].split()])]
    for name, text in meta.get("labels", {}).items():
        found += [(lv, f"label {name}: \"{ph}\"") for lv, _, ph in asks([norm(x) for x in str(text).split()])]
    hard = [d for lv, d in found if lv == "FAIL"]; soft = [d for lv, d in found if lv == "WARN"]
    add("FAIL" if hard else "PASS", "no calls to action", "; ".join(hard) if hard else "none said or printed")
    if soft:
        add("WARN", "soft ask", "; ".join(soft) + " (a question that is part of his take is fine; a sign-off ask is not)")

    # 2. every spoken word captioned or on paper
    cards = captions.cards(plan, tl)
    shown = {round(w["s"], 3) for c in cards for w in c["words"]}
    hide = [(tl.t(a), tl.t(b)) for a, b in plan["captions"].get("hide", [])]
    on_paper = {i for i, w in enumerate(W) if round(w["start"], 3) not in shown and any(a <= w["start"] < b for a, b in hide)}
    missing = [i for i, w in enumerate(W) if round(w["start"], 3) not in shown and i not in on_paper]
    runs, cur = [], []
    for i in missing:
        if cur and i == cur[-1] + 1:
            cur.append(i)
        else:
            if cur:
                runs.append(cur)
            cur = [i]
    runs += [cur] if cur else []
    orphan = [r for r in runs if len(r) <= 2 and W[r[-1]]["end"] - W[r[0]]["start"] < 0.8 and r[0] - 1 in on_paper
              and r[-1] + 1 in on_paper]
    lost = [r for r in runs if r not in orphan]
    add("WARN" if lost else "PASS", "every word captioned or on paper",
        "; ".join(f"{stamp(W[r[0]]['start'])} \"{' '.join(W[i]['word'] for i in r)}\"" for r in lost) if lost else
        f"{len(W) - len(on_paper) - len(missing)} captioned, {len(on_paper)} on paper, {len(W)} words")
    if orphan:
        add("INFO", "dropped on purpose", "; ".join(" ".join(W[i]["word"] for i in r) for r in orphan) +
            " (a one- or two-word caption stranded between two papers)")
    cap = plan["captions"]["size"] * feed
    add("PASS" if cap >= 20 else "WARN", "caption size at feed width", f"{cap:.0f} px type at {FEED_W} px wide")

    # 3. the first frame: a title, readable in the feed
    titles = title_heights(R)
    if not titles:
        add("WARN", "title on the first frame", "no paper on frame 0: the first frame is the thumbnail, give it a title")
    else:
        name, px = max(titles, key=lambda x: x[1])
        add("PASS" if px * feed >= 14 else "WARN", "title on the first frame",
            f"{name}: text {px * feed:.0f} px tall at {FEED_W} px wide" + ("" if px * feed >= 14 else " (aim for 14+)"))
    video = plan.wp("out", plan.get("name", "edit") + ".mp4"); prev = plan.wp("review", "x_feed_preview.png")
    if video.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-frames:v", "1", "-vf", f"scale={FEED_W}:-2",
                        str(prev)], check=True)
    else:
        im = Image.fromarray(np.asarray(R.frame(0), np.uint8))
        im.resize((FEED_W, int(round(FEED_W * im.height / im.width))), Image.LANCZOS).save(prev)

    # 4. the hook starts at once
    t0 = W[0]["start"] if W else 0.0
    add("PASS" if t0 <= 0.5 else "WARN", "first word", f"spoken at {t0:.2f} s" + ("" if t0 <= 0.5 else " (aim for 0.5 s)"))

    # 5. sources
    bad, unprinted = [], []
    for name, r in materials.docs_of(plan).items():
        if r["kind"] not in ("screenshot", "clipping"):
            continue
        src = str(r.get("source") or "").strip()
        if not src:
            bad.append(name)
        elif r["kind"] == "clipping" and src.lower() not in OWN:
            outlet = src.split("·")[0].strip().lower()
            if not any(outlet and outlet in str(L.get("text", "")).lower() for L in meta["docs"][name]["lines"]):
                unprinted.append(f"{name} ({src})")
    kinds = [n for n, r in materials.docs_of(plan).items() if r["kind"] in ("screenshot", "clipping")]
    add("FAIL" if bad else "PASS", "sources named",
        (", ".join(bad) + ": add source: \"Outlet · date\" (or source: own for his own line)") if bad
        else (", ".join(kinds) if kinds else "no screenshots or clippings"))
    if unprinted:
        add("WARN", "source on the paper", ", ".join(unprinted) + ": print it on the clipping too (a c:OUTLET · DATE line)")

    # 6. claims to verify
    words = [w["word"] for w in W]
    for r in claim_runs(words):
        a, b = max(0, r[0] - 3), min(len(W), r[-1] + 4)
        claims.append(f"{stamp(W[r[0]]['start'])} said \"{' '.join(words[i] for i in r)}\": "
                      f"...{' '.join(words[a:b])}...")
    for name, m in meta["docs"].items():
        if m.get("image"):
            claims.append(f"{name}: the screenshot is a real, unedited capture and its source is right")
        for L in m["lines"]:
            ws = str(L.get("text", "")).split()
            claims += [f"{name} prints \"{' '.join(ws[i] for i in r)}\"" for r in claim_runs(ws, spoken=False)]
    add("INFO", "claims to verify", f"{len(claims)} listed in X_CHECK.md" if claims else "no numbers or names found")

    # 7. the file
    if video.exists():
        mb = video.stat().st_size / 1e6
        add("PASS" if mb <= 512 else "WARN", "file", f"{video.name}, {mb:.1f} MB, {tl.total:.1f} s" +
            ("" if mb <= 512 else " (over 512 MB: check X's current upload limit for your account)"))
    else:
        add("INFO", "file", "not rendered yet: file checks skipped")
    if tl.total > 140:
        add("INFO", "length", f"{tl.total:.0f} s: longer than 2:20, which X allows on Premium accounts")

    n = {k: sum(r[0] == k for r in rows) for k in ("PASS", "WARN", "FAIL")}
    md = [f"# X pre-posting check: {plan.get('name', 'edit')}", "",
          f"{n['PASS']} pass, {n['WARN']} warn, {n['FAIL']} fail. Feed preview: `review/x_feed_preview.png` "
          f"(the first frame at {FEED_W} px wide).", "", "| result | check | detail |", "|---|---|---|"]
    md += [f"| {lv} | {what} | {detail} |" for lv, what, detail in rows]
    md += ["", "## Claims to verify before posting", "",
           "Check each against its source; ASR mishears names and numbers.", ""]
    md += [f"- [ ] {c}" for c in claims] or ["- (none found)"]
    md += ["", "## Why these checks", "",
           "Third-party reporting (Nov 2026; help.x.com refuses automated reads, so confirm in Creator Studio): "
           "X's Original Content Rewards pays only for original posts, and accounts that keep asking for likes, "
           "reposts, replies or follows are reportedly removed. Under the older program a post corrected by "
           "Community Notes earned nothing."]
    plan.wp("review", "X_CHECK.md").write_text("\n".join(md) + "\n")
    print(f"x-check {plan.get('name', 'edit')}")
    for lv, what, detail in rows:
        print(f"  {lv:4s}  {what:32s} {detail}")
    print(f"{n['PASS']} pass, {n['WARN']} warn, {n['FAIL']} fail -> {plan.wp('review', 'X_CHECK.md')}")
    return {"fail": n["FAIL"], "warn": n["WARN"], "rows": rows, "claims": claims, "preview": prev, "titles": titles}
