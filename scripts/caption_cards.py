#!/usr/bin/env python3
"""Word timings -> caption cards, plus a PIL renderer with a stable layout.

Rules (see references/graphics-and-type.md): 1-4 words per card, <= 18 chars
per line, break at sentence punctuation, commas and pauses, keep numbers with
units and capitalised names together, cards start one frame before the first
word and stay until the next card. Layout never reflows while words light up.

CLI:
  caption_cards.py WORDS.json --out cards.json [--srt captions.srt]
                   [--text TRANSCRIPT.json|.txt] [--preview FRAME.png --at 3.2,7.5]
WORDS.json: a list of {word|text, start, end}, or a dict holding such a list
under "words" (edit time). --text adds punctuation when the words have none.

Module:
  from caption_cards import build_cards, CardRenderer
  cards = build_cards(words)
  rend = CardRenderer(width=1080, height=1920, y=1300)
  layer = rend.render(cards, t)      # RGBA PIL image, paste over the frame
"""
import argparse, json, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/System/Library/Fonts/Avenir Next Condensed.ttc"
HEAVY, BOLD = 8, 0
UNITS = {"minutes", "minute", "min", "seconds", "hours", "users", "dollars", "bucks", "percent", "%", "k", "million", "billion"}
JOINERS = {"and", "but", "so", "because", "then", "which", "that", "or"}
NUM = re.compile(r"^[$£€]?\d[\d,.]*[kKmM%]?$")
NUMWORDS = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
            "fifteen", "twenty", "thirty", "forty", "fifty", "hundred", "thousand", "million", "billion"}


def _isnum(tok):
    t = _norm(tok)
    return bool(NUM.match(t)) or t in NUMWORDS


def _norm(s):
    return re.sub(r"[^a-z0-9$%]", "", s.lower())


def load_words(path):
    d = json.loads(Path(path).read_text())
    if isinstance(d, dict):
        d = d.get("words") or next(v for v in d.values() if isinstance(v, list))
    out = []
    for w in d:
        t = str(w.get("word") or w.get("text") or "").strip()
        if t:
            out.append({"w": t, "s": float(w["start"]), "e": float(w["end"])})
    return repair_timings(out)


def repair_timings(words, min_dur=0.05):
    """ASR gives some words zero length (e.g. 'my' 5.42-5.98, 'perspective' 5.98-5.98).
    Re-split each such word together with its predecessor in proportion to
    character count. A heuristic: it makes highlights plausible, not exact."""
    i = 0
    while i < len(words):
        if words[i]["e"] - words[i]["s"] < min_dur:
            j = i
            while j + 1 < len(words) and words[j + 1]["e"] - words[j + 1]["s"] < min_dur:
                j += 1
            a = max(0, i - 1)
            span_s, span_e = words[a]["s"], max(words[j]["e"], words[a]["e"])
            if j + 1 < len(words):
                span_e = max(span_e, min(words[j + 1]["s"], span_s + 0.12 * (j - a + 1) + span_e - span_s))
            weights = [len(_norm(w["w"])) + 2 for w in words[a:j + 1]]
            tot = float(sum(weights)); t = span_s
            for w, wt in zip(words[a:j + 1], weights):
                w["s"] = t; t += (span_e - span_s) * wt / tot; w["e"] = t
            i = j + 1
        else:
            i += 1
    return words


def attach_punct(words, text):
    """Copy display forms ('$40', 'Grok's') and punctuation from a transcript
    text onto bare ASR words. Global alignment on letters and digits, so words
    removed by the edit (skipped segments) don't break the sync."""
    import difflib
    alnum = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    toks = text.split()
    sm = difflib.SequenceMatcher(a=[alnum(w["w"]) for w in words], b=[alnum(t) for t in toks], autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            words[blk.a + k]["w"] = toks[blk.b + k]
    return words


def build_cards(words, max_chars=18, max_words=4, pause=0.28, fps=30.0):
    cards, cur = [], []

    def flush():
        if cur:
            cards.append({"words": list(cur)})
            cur.clear()

    for i, w in enumerate(words):
        if cur:
            prev = cur[-1]
            text_len = len(" ".join(x["w"] for x in cur + [w]))
            gap = w["s"] - prev["e"]
            bare, pbare = _norm(w["w"]), _norm(prev["w"])
            keep_together = (_isnum(prev["w"]) and bare in UNITS) or \
                            (prev["w"][:1].isupper() and w["w"][:1].isupper() and not re.search(r"[.!?]$", prev["w"]))
            hard = re.search(r"[.!?]$", prev["w"]) or gap > pause
            # a joiner opens a clause ("the opposite of | that we..."), unless it ends the sentence ("of that?")
            soft = len(cur) >= 2 and (re.search(r"[,;:]$", prev["w"]) or (bare in JOINERS and not re.search(r"[.!?]$", w["w"])))
            if keep_together and not hard and text_len > max_chars and len(cur) >= 2:
                carry = cur.pop(); flush(); cur.append(carry)  # "lasted about | five minutes"
            else:
                # don't strand a sentence's last word alone: allow a little extra length
                ends = bool(re.search(r"[.!?]$", w["w"])) and len(cur) < max_words and text_len <= max_chars + 8
                too_long = text_len > max_chars and not ends
                if not keep_together and (hard or soft or too_long or len(cur) >= max_words):
                    flush()
        cur.append(w)
    flush()
    # merge cards too short to read (< min_card s) into a neighbour
    min_card = 0.4
    k = 0
    while k < len(cards):
        c = cards[k]
        dur = (cards[k + 1]["words"][0]["s"] if k + 1 < len(cards) else c["words"][-1]["e"] + 0.4) - c["words"][0]["s"]
        if dur < min_card and len(cards) > 1:  # never across a sentence end: a short card beats a mixed one
            ends = bool(re.search(r"[.!?]$", c["words"][-1]["w"]))
            prev_ends = k > 0 and bool(re.search(r"[.!?]$", cards[k - 1]["words"][-1]["w"]))
            fits_prev = k > 0 and len(cards[k - 1]["words"]) + len(c["words"]) <= max_words + 1
            fits_next = k + 1 < len(cards) and len(cards[k + 1]["words"]) + len(c["words"]) <= max_words + 1
            if ends and fits_prev and not prev_ends:
                cards[k - 1]["words"] += c["words"]; cards.pop(k); k -= 1; continue
            if not ends and fits_next:
                cards[k + 1]["words"] = c["words"] + cards[k + 1]["words"]; cards.pop(k); continue
            if fits_prev and not prev_ends:
                cards[k - 1]["words"] += c["words"]; cards.pop(k); k -= 1; continue
        k += 1
    for k, c in enumerate(cards):
        c["start"] = max(0.0, c["words"][0]["s"] - 1 / fps)
        nxt = cards[k + 1]["words"][0]["s"] - 1 / fps if k + 1 < len(cards) else None
        last = c["words"][-1]["e"]
        c["end"] = min(nxt, last + 0.6) if nxt is not None else last + 0.4
        if nxt is not None and nxt - last < 0.6:
            c["end"] = nxt
        c["text"] = " ".join(x["w"] for x in c["words"])
    return cards


def to_srt(cards):
    def ts(t):
        ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    return "\n".join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{re.sub(r'[,;:]$', '', c['text'])}\n"
                     for i, c in enumerate(cards, 1))


class CardRenderer:
    def __init__(self, width=1080, height=1920, y=1300, size=78, fill=(244, 239, 230), accent=(226, 69, 43),
                 max_width=900, shadow=0.6, pop=1.06, mode="highlight", font=FONT, index=HEAVY, fps=30.0,
                 shadow_rgb=(10, 8, 6), light_stage=False):
        if light_stage:  # ink on paper: dark text, a paper-coloured halo instead of a dark shadow
            fill, shadow_rgb, shadow = (21, 18, 15), (236, 229, 216), 0.9
        self.shadow_rgb = shadow_rgb
        self.W, self.H, self.y, self.size = width, height, y, size
        self.fill, self.accent, self.max_width, self.shadow = fill, accent, max_width, shadow
        self.pop, self.mode, self.fps = pop, mode, fps
        self.font = ImageFont.truetype(font, size, index=index)
        self.font_pop = ImageFont.truetype(font, int(round(size * pop)), index=index)
        self._layout_cache = {}

    def _display(self, w):
        return re.sub(r"[,;:]$", "", w)

    def layout(self, card):
        key = id(card)
        if key in self._layout_cache:
            return self._layout_cache[key]
        d = ImageDraw.Draw(Image.new("L", (8, 8)))
        words = [self._display(w["w"]).upper() for w in card["words"]]
        sp = d.textlength(" ", font=self.font)
        widths = [d.textlength(w, font=self.font) for w in words]
        lines, cur, cw = [], [], 0.0
        for i, wd in enumerate(widths):  # greedy, then balance two lines
            if cur and cw + sp + wd > self.max_width:
                lines.append(cur); cur, cw = [], 0.0
            cw = cw + (sp if cur else 0) + wd; cur.append(i)
        lines.append(cur)
        if len(lines) == 2 and len(lines[0]) > len(lines[1]) + 1:
            lines = [lines[0][:-1], [lines[0][-1]] + lines[1]]
        lh = int(self.size * 1.08)
        pos = {}
        top = self.y - (len(lines) * lh) // 2
        for li, ln in enumerate(lines):
            total = sum(widths[i] for i in ln) + sp * (len(ln) - 1)
            x = (self.W - total) / 2
            for i in ln:
                pos[i] = (x, top + li * lh, widths[i]); x += widths[i] + sp
        self._layout_cache[key] = (words, pos)
        return words, pos

    def card_at(self, cards, t):
        for c in cards:
            if c["start"] <= t < c["end"]:
                return c
        return None

    def render(self, cards, t, keywords=()):
        layer = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        c = self.card_at(cards, t)
        if not c:
            return layer
        words, pos = self.layout(c)
        active = max([i for i, w in enumerate(c["words"]) if w["s"] - 1 / self.fps <= t] or [0])
        text = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        d = ImageDraw.Draw(text)
        for i, wtxt in enumerate(words):
            if self.mode == "reveal" and i > active:
                continue
            x, y, wd = pos[i]
            hot = _isnum(wtxt) or _norm(wtxt) in {_norm(k) for k in keywords}
            col = self.accent if (i == active or hot) else self.fill
            since = t - (c["words"][i]["s"] - 1 / self.fps)
            if i == active and 0 <= since < 3 / self.fps:  # 3-frame pop, centred on the word
                cx = x + wd / 2
                pw = d.textlength(wtxt, font=self.font_pop)
                d.text((cx - pw / 2, y - (self.font_pop.size - self.size) / 2), wtxt, font=self.font_pop, fill=col + (255,))
            else:
                d.text((x, y), wtxt, font=self.font, fill=col + (255,))
        if self.shadow:
            a = text.split()[3].filter(ImageFilter.GaussianBlur(8))
            sh = Image.new("RGBA", (self.W, self.H), tuple(self.shadow_rgb) + (0,))
            sh.putalpha(a.point(lambda v: int(v * self.shadow)))
            layer.alpha_composite(sh, (0, 4))
        layer.alpha_composite(text)
        return layer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words"); ap.add_argument("--out", required=True); ap.add_argument("--srt")
    ap.add_argument("--text", help="transcript .json (with 'text') or .txt to restore punctuation")
    ap.add_argument("--preview", help="background frame (1080x1920) for a preview sheet")
    ap.add_argument("--at", default="", help="comma-separated times for the preview")
    ap.add_argument("--preview-out")
    a = ap.parse_args()
    words = load_words(a.words)
    if a.text:
        p = Path(a.text)
        txt = json.loads(p.read_text()).get("text", "") if p.suffix == ".json" else p.read_text()
        words = attach_punct(words, txt)
    cards = build_cards(words)
    Path(a.out).write_text(json.dumps(cards, indent=1))
    if a.srt:
        Path(a.srt).write_text(to_srt(cards))
    n = len(cards); avg = sum(len(c["words"]) for c in cards) / max(n, 1)
    print(f"{len(words)} words -> {n} cards, {avg:.1f} words/card; longest card: "
          f"{max((c['text'] for c in cards), key=len)!r}")
    if a.preview:
        bg = Image.open(a.preview).convert("RGBA").resize((1080, 1920))
        r = CardRenderer()
        tiles = []
        for t in [float(x) for x in a.at.split(",") if x]:
            f = bg.copy(); f.alpha_composite(r.render(cards, t))
            ImageDraw.Draw(f).text((20, 20), f"{t:.2f}s", fill=(255, 255, 0, 255), font=ImageFont.truetype(FONT, 40, index=BOLD))
            tiles.append(f.resize((540, 960)))
        sheet = Image.new("RGBA", (540 * len(tiles), 960))
        for i, tl in enumerate(tiles):
            sheet.paste(tl, (540 * i, 0))
        sheet.convert("RGB").save(a.preview_out or "caption-preview.jpg", quality=90)
        print("preview:", a.preview_out or "caption-preview.jpg")


if __name__ == "__main__":
    main()
