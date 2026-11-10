"""Map source-time words through the EDL and group them into caption cards.

Words are evidence: they come from an alignment file or from the fixture's own
record of what was synthesised. This module does not invent wording.
Optional `replacements` in the plan rewrite a token the alignment got wrong.
"""
import json
from pathlib import Path


def map_words(edl, src_words):
    out = []
    for s in edl.segments:
        if s["room"]:
            continue
        for w in src_words:
            if w["e"] > s["src_in"] and w["s"] < s["src_out"] - 0.02:
                a = max(w["s"], s["src_in"])
                b = min(w["e"], s["src_out"])
                out.append({"w": w["w"], "s": round(s["edit_in"] + a - s["src_in"], 3),
                            "e": round(s["edit_in"] + b - s["src_in"], 3), "seg": s["id"],
                            "src_s": w["s"], "src_e": w["e"]})
    for rep in edl.plan.get("replacements") or []:
        fixed = []
        for w in out:
            if w["w"] == rep["from"]:
                fixed.append({**w, "w": rep["to"]})
            else:
                fixed.append(w)
        out = fixed
    return out


def groups(words, plan):
    """Caption cards. `caption_groups: auto` packs 1-4 words. A list of phrases must match the words."""
    spec = plan.get("caption_groups", "auto")
    if spec == "auto":
        cards, cur = [], []
        for w in words:
            cur.append(w)
            end = w["w"].rstrip().endswith((".", "?", "!")) or len(cur) >= 4
            if end:
                cards.append(cur)
                cur = []
        if cur:
            cards.append(cur)
    else:
        flat = [tok for phrase in spec for tok in phrase]
        have = [w["w"] for w in words]
        if flat != have:
            raise SystemExit(f"caption_groups do not match the mapped words:\n  plan {flat}\n  edit {have}")
        cards, k = [], 0
        for phrase in spec:
            cards.append(words[k:k + len(phrase)])
            k += len(phrase)
    caps = []
    for ws in cards:
        caps.append({"start": max(0.0, ws[0]["s"] - 0.04), "end": ws[-1]["e"] + 0.25,
                     "seg": ws[0]["seg"], "words": ws})
    for i in range(len(caps) - 1):
        caps[i]["end"] = min(caps[i]["end"], caps[i + 1]["start"])
    ends = {s["id"]: s["edit_out"] for s in edl_segments(plan, words)}
    for c in caps:
        if c["seg"] in ends:
            c["end"] = min(c["end"], ends[c["seg"]])
    return caps


def edl_segments(plan, words):
    return []  # segment ends are applied by the caller when it has the EDL


def write_srt(caps, path, ends):
    for c in caps:
        if c.get("seg") in ends:
            c["end"] = min(c["end"], ends[c["seg"]])

    def ts(t):
        ms = int(round(max(0, t) * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    lines = []
    for i, c in enumerate(caps, 1):
        lines.append(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{' '.join(w['w'] for w in c['words'])}\n")
    Path(path).write_text("\n".join(lines))


def load_src_words(path):
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        data = [w for sid in data for w in data[sid]]
    return [{"w": w["w"], "s": float(w["s"]), "e": float(w["e"])} for w in data]
