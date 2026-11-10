"""Time expressions: every cue in a plan is keyed to the edit, not to seconds.

    12.5              absolute edit time
    END, START        total length, 0
    A.in A.out        segment A's audio in/out in edit time
    A.pin A.pout      segment A's picture in/out (audio plus the air it fills)
    A.w:lasted        start of the first spoken "lasted" in segment A
    A.w:5#2           start of the second "5"
    A.we:minutes      end of "minutes"
    A.w:[covid-19]    brackets protect words containing + or -
    ...+0.12 ...-2f   offsets in seconds or frames, chainable ("A.pout+3f-0.02")

Words match case-insensitively on letters, digits and $ (display forms from
the plan, e.g. "$40", "14").
"""
import json
import re

_OFF = re.compile(r"^(.*?)((?:[+-]\d+(?:\.\d+)?f?)*)$")
_TERM = re.compile(r"[+-]\d+(?:\.\d+)?f?")


def norm(s):
    return re.sub(r"[^a-z0-9$]", "", str(s).lower())


class Timeline:
    def __init__(self, plan, edl=None, words=None):
        self.fps = plan.fps
        self.edl = edl if edl is not None else json.loads(plan.wp("prep", "edl.json").read_text())
        self.words = words if words is not None else json.loads(plan.wp("prep", "words_edit.json").read_text())
        self.total = float(self.edl["total"])
        self.seg = {s["id"]: s for s in self.edl["segments"]}

    # ---- lookup
    def word(self, sid, text, k=1, end=False):
        hits = [w for w in self.words if w["seg"] == sid and norm(w["word"]) == norm(text)]
        if len(hits) < k:
            raise KeyError(f"word {text!r} #{k} not in segment {sid} "
                           f"(has: {' '.join(w['word'] for w in self.words if w['seg'] == sid)})")
        return hits[k - 1]["end" if end else "start"]

    def t(self, expr):
        if expr is None:
            return None
        if isinstance(expr, (int, float)):
            return float(expr)
        s = str(expr).strip()
        m = _OFF.match(s)
        base, offs = m.group(1).strip(), m.group(2)
        val = self._base(base) if base else 0.0
        for term in _TERM.findall(offs):
            val += float(term[:-1]) / self.fps if term.endswith("f") else float(term)
        return val

    def _base(self, b):
        u = b.upper()
        if u == "END":
            return self.total
        if u == "START":
            return 0.0
        try:
            return float(b)
        except ValueError:
            pass
        if "." not in b:
            raise ValueError(f"bad time expression {b!r}")
        sid, anchor = b.split(".", 1)
        if sid not in self.seg:
            raise ValueError(f"unknown segment {sid!r} in {b!r}")
        s = self.seg[sid]
        if anchor in ("in", "out"):
            return s["edit_" + anchor]
        if anchor in ("pin", "pout"):
            return s["p_" + anchor[1:]]
        if anchor.startswith(("w:", "we:")):
            end = anchor.startswith("we:")
            word = anchor.split(":", 1)[1]
            k = 1
            if word.startswith("["):
                word, rest = word[1:].split("]", 1)
                if rest.startswith("#"):
                    k = int(rest[1:])
            elif "#" in word:
                word, kk = word.rsplit("#", 1)
                k = int(kk)
            return self.word(sid, word, k, end)
        raise ValueError(f"bad anchor {anchor!r} in {b!r}")

    def phrase(self, text, after=0.0, slack=2):
        """(start, end) of the first time these words are spoken at or after `after`, allowing up
        to `slack` extra words between them (fillers, repeats); None when it is not said."""
        toks = [x for x in (norm(w) for w in str(text).split()) if x]
        W = self.words
        for i, w in enumerate(W):
            if not toks or w["start"] < after - 1e-3 or norm(w["word"]) != toks[0]:
                continue
            j = last = i; hit = 1
            for tok in toks[1:]:
                for jj in range(j + 1, min(len(W), j + 2 + slack)):
                    if norm(W[jj]["word"]) == tok:
                        j = last = jj; hit += 1
                        break
            if hit >= max(1, -(-len(toks) * 3 // 5)):
                return W[i]["start"], W[last]["end"]
        return None

    def speaking(self, t, pad=0.0):
        """True while a kept word is being spoken at edit time t."""
        return any(w["start"] - pad <= t < w["end"] + pad for w in self.words)
