"""Word-timed caption cards for the edit.

plan["captions"]:
  "groups": [[i, j], [i, j, "end-expr"], ...]  word-index ranges (words_edit.json order);
             omit for automatic grouping (caption_cards.build_cards rules)
  "hide":   [["from-expr", "to-expr"], ...]    no captions while hero type or a receipt
             says the same words; words starting inside are left out
  "y", "size", "max_width", "keywords"
A card never ends on a negation ("not", "no", "never", "don't"...): the word moves
to the next card so a muted viewer can't read the opposite claim.
"""
import re
import sys

from .plan import SCRIPTS
from .timeline import norm

sys.path.insert(0, str(SCRIPTS))
from caption_cards import CardRenderer, build_cards  # noqa: E402

NEGATIONS = {"not", "no", "never", "dont", "doesnt", "didnt", "isnt", "arent", "wasnt", "werent", "cant", "cannot",
             "wont", "wouldnt", "shouldnt", "couldnt", "nothing", "nobody", "without"}


def _hidden(t, hide):
    return any(a <= t < b for a, b in hide)


def cards(plan, tl):
    C = plan["captions"]; fps = plan.fps; W = tl.words
    hide = [(tl.t(a), tl.t(b)) for a, b in C.get("hide", [])]
    if C.get("groups"):
        groups = [(g[0], g[1], g[2] if len(g) > 2 else None) for g in C["groups"]]
    else:  # automatic: build cards inside each run of visible words (hidden lines split the runs)
        vis = [i for i, w in enumerate(W) if not _hidden(w["start"], hide)]
        runs, groups = [], []
        for i in vis:
            if runs and i == runs[-1][-1] + 1:
                runs[-1].append(i)
            else:
                runs.append([i])
        hidden = set(range(len(W))) - set(vis)
        # an orphan: two words or fewer, under 0.8 s, with hidden lines on both sides ("IT" between two papers)
        runs = [r for r in runs if not (len(r) <= 2 and W[r[-1]]["end"] - W[r[0]]["start"] < 0.8
                                        and r[0] - 1 in hidden and r[-1] + 1 in hidden)]
        for run in runs:
            ws = [{"w": W[i]["word"], "s": W[i]["start"], "e": max(W[i]["end"], W[i]["start"] + 0.05), "i": i} for i in run]
            for c in build_cards(ws, fps=fps):
                groups.append((c["words"][0]["i"], c["words"][-1]["i"], None))
    groups = [list(g) for g in groups]
    if not C.get("groups"):  # rebalance "NOW LET'S DO A | TEST." into "NOW LET'S DO | A TEST."
        for k in range(len(groups) - 1):
            a, b = groups[k], groups[k + 1]
            while b[0] == a[1] + 1 and (b[1] - b[0] + 1) < (a[1] - a[0] + 1) - 1 and b[1] - b[0] + 1 < 2:
                a[1] -= 1; b[0] -= 1
    for k in range(len(groups) - 1):  # never strand a negation at the end of a card
        i, j, e = groups[k]
        while j > i and norm(W[j]["word"]) in NEGATIONS and groups[k + 1][0] == j + 1:
            groups[k][1] = j - 1; groups[k + 1][0] = j; j -= 1
    out = []
    for k, (i, j, end_expr) in enumerate(groups):
        ws = [{"w": W[n]["word"], "s": W[n]["start"], "e": max(W[n]["end"], W[n]["start"] + 0.05)} for n in range(i, j + 1)]
        start = 0.0 if (k == 0 and ws[0]["s"] < 0.3) else ws[0]["s"] - 1 / fps
        nxt = groups[k + 1][0] if k + 1 < len(groups) else None
        # hold until the next card only when the next word follows closely in time (not across a demo)
        follows = nxt == j + 1 and W[nxt]["start"] - ws[-1]["e"] < 0.6
        if end_expr is not None:
            end = tl.t(end_expr)
        elif follows:
            end = W[nxt]["start"] - 1 / fps
        else:
            end = ws[-1]["e"] + 0.4
            later = [a for a, b in hide if a >= ws[-1]["s"]]  # never hold a card over a hidden line
            if later:
                end = min(end, min(later))
            if nxt is not None:
                end = min(end, W[nxt]["start"] - 1 / fps)
        out.append({"words": ws, "start": start, "end": end, "text": " ".join(w["w"] for w in ws)})
    return out


def renderer(plan):
    C = plan["captions"]
    return CardRenderer(width=plan.W, height=plan.H, y=C["y"], size=C["size"], max_width=C["max_width"], fps=plan.fps)


def band_renderer(plan, scale=1.0):
    """Renderer drawing into a band around the caption line (two lines + shadow); returns (renderer, band top)."""
    C = plan["captions"]; size = max(8, int(round(C["size"] * scale))); half = int(size * 2.4)
    cy = int(round(C["y"] * scale)); y0 = max(0, cy - half)
    return CardRenderer(width=int(round(plan.W * scale)), height=2 * half, y=cy - y0, size=size,
                        max_width=C["max_width"] * scale, fps=plan.fps), y0


def srt(plan, tl, path):
    """Complete captions for upload: every spoken word, including lines hidden on screen."""
    ws = [{"w": w["word"], "s": w["start"], "e": max(w["end"], w["start"] + 0.05)} for w in tl.words]
    from caption_cards import to_srt
    path.write_text(to_srt(build_cards(ws, fps=plan.fps)))
