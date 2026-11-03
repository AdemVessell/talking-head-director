"""Treatments: the house style dressed for a subject. The camera, paper, light, grain and
captions stay the same; the surface, the documents and their sounds change with what the
video is about. Receipts are for money. Pick the treatment from the subject, then the
documents inside it (documents.py), keyed to his words.

  treatment  surface   documents (first = default)   subjects
  evidence   charcoal  receipt card printout         costs, money, usage, verdicts, numbers
  studio     walnut    note sticky staff             songwriting, music, creative process, personal
  workshop   mat       card blueprint index          gear, builds, how-to, product tests
  newsroom   kraft     clipping index sticky         opinions, industry takes, claims, reactions
  lab        linen     printout card blueprint       AI, software, prompts, tech explainers
  pinboard   cork      index sticky clipping         plans, ideas, lists, research, comparisons
  classroom  slate     index blueprint sticky        teaching, definitions, language, maths

A plan sets `treatment:`; a layout may still override `surface:` and `light:`, and a
document its `kind:`. Mixing is allowed when the story needs it (a receipt can land in the
studio if he talks about what the session cost) but each video has one home surface.
"""
TREATMENTS = {
    "evidence": dict(surface="charcoal", kinds=["receipt", "card", "printout"], light=[200, 200, 1000, 0.55, 1.2]),
    "studio": dict(surface="walnut", kinds=["note", "sticky", "staff"], light=[280, 260, 950, 0.5, 1.22]),
    "workshop": dict(surface="mat", kinds=["card", "blueprint", "index"], light=[220, 180, 1100, 0.6, 1.18]),
    "newsroom": dict(surface="kraft", kinds=["clipping", "index", "sticky"], light=[240, 220, 1000, 0.55, 1.15]),
    "lab": dict(surface="linen", kinds=["printout", "card", "blueprint"], light=[200, 220, 1000, 0.6, 1.25]),
    "pinboard": dict(surface="cork", kinds=["index", "sticky", "clipping"], light=[240, 200, 1050, 0.55, 1.15]),
    "classroom": dict(surface="slate", kinds=["index", "blueprint", "sticky"], light=[220, 220, 1000, 0.6, 1.25]),
}

# What each document sounds like (sound.py kit names): arriving, revealing a line, a red mark.
SOUNDS = {
    "receipt": dict(enter="flutter", land="paper_slap", reveal="printer", pop="tick", mark="pencil"),
    "card": dict(enter="paper_slap", reveal="typewriter", mark="pencil"),
    "note": dict(enter="paper_slap", reveal="pencil", mark="marker"),
    "sticky": dict(enter="paper_slap", reveal="marker", mark="marker"),
    "clipping": dict(enter="paper_slap", reveal=None, mark="marker"),
    "blueprint": dict(enter="paper_slap", reveal="pencil", mark="marker"),
    "printout": dict(enter="flutter", land="paper_slap", reveal="printer", mark="pencil"),
    "index": dict(enter="paper_slap", reveal="typewriter", mark="pencil"),
    "staff": dict(enter="paper_slap", reveal="pencil", mark="pencil"),
    "screenshot": dict(enter="paper_slap", reveal=None, mark="marker"),
}


def get(plan):
    name = plan.get("treatment", "evidence")
    if name not in TREATMENTS:
        raise SystemExit(f"unknown treatment {name!r}; one of {sorted(TREATMENTS)}")
    return dict(TREATMENTS[name], name=name)


def surface(plan, lay=None):
    return (lay or {}).get("surface") or plan.get("surface") or get(plan)["surface"]


def light(plan, lay=None):
    return (lay or {}).get("light") or get(plan)["light"]


def default_kind(plan):
    return get(plan)["kinds"][0]


def surfaces_used(plan):
    used = {surface(plan)}
    for lay in plan.get("layouts", {}).values():
        used.add(surface(plan, lay))
    return sorted(used)
