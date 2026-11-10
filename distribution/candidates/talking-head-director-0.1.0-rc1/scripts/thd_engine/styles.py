"""Styles: named starting points for `thd auto`. A style picks the desk, the papers, the caption
look, the finish and the pace, so one word chooses an edit. Every style keeps the same rules:
the presenter's own words, cuts in the quiet, captions on every spoken word, nothing invented.

  thd styles            list them
  thd auto REC --style timeline

A style is data. To add one, add a row here; anything a plan can say can go in `plan`.
"""
import re

X_BLUE = [29, 155, 240]

STYLES = {
    "desk": dict(
        about="The classic: a warm desk, a title note, the points written out as they are said.",
        good_for="most takes, how-tos, opinions",
        treatment="lab", title_kind="sticky", points_kind="index", finish="medium", pause=0.35, min_shot=2.6),
    "journey": dict(
        about="A camera that travels: it descends onto the presenter, dives into the papers, falls back to the take.",
        good_for="stories with a turn, explainers, anything that should feel like a short film",
        treatment="lab", title_kind="sticky", points_kind="index", finish="medium", pause=0.35, min_shot=2.8, journey=True),
    "timeline": dict(
        about="Made for a dark phone feed: matte black, white type with a blue word, quick cuts.",
        good_for="hot takes, replies to a post, anything posted to X",
        treatment="timeline", title_kind="sticky", points_kind="index", finish="subtle", pause=0.28, min_shot=2.2,
        plan={"captions": {"size": 86, "accent": X_BLUE, "fill": [247, 249, 249]}}),
    "newsdesk": dict(
        about="A kraft news desk: the headline or screenshot pinned with its source, then the take.",
        good_for="news, reactions to a headline or a post (give --headline/--image and --source)",
        treatment="newsroom", title_kind="sticky", points_kind="index", finish="medium", pause=0.33, min_shot=2.6,
        journey=True),
    "notebook": dict(
        about="A walnut desk and a lined notebook page written by hand as the points are said.",
        good_for="personal stories, creative process, lessons learned",
        treatment="studio", title_kind="sticky", points_kind="note", finish="medium", pause=0.38, min_shot=3.0),
    "receipts": dict(
        about="A charcoal desk and a till receipt that prints each number as it is said.",
        good_for="money, costs, prices, usage, anything with numbers",
        treatment="evidence", title_kind="sticky", points_kind="receipt", finish="medium", pause=0.33, min_shot=2.6),
    "workbench": dict(
        about="A green cutting mat with spec cards: the look of a build or a product test.",
        good_for="gear, builds, product tests, tutorials",
        treatment="workshop", title_kind="sticky", points_kind="card", finish="medium", pause=0.35, min_shot=2.8),
    "pinboard": dict(
        about="A cork board of index cards and sticky notes.",
        good_for="lists, plans, comparisons, research roundups",
        treatment="pinboard", title_kind="sticky", points_kind="index", finish="medium", pause=0.35, min_shot=2.6),
    "chalkboard": dict(
        about="A slate board: steps and definitions on cards.",
        good_for="teaching, definitions, explainers",
        treatment="classroom", title_kind="sticky", points_kind="index", finish="subtle", pause=0.38, min_shot=3.0),
    "clean": dict(
        about="Nearly nothing: the presenter, captions, a light finish. The cut does the work.",
        good_for="confident delivery, personal messages, when papers would distract",
        treatment="lab", title_kind=None, points_kind=None, finish="subtle", pause=0.3, min_shot=2.4),
}
DEFAULT = "desk"

_HINTS = [  # first match wins; counted on the transcript
    ("receipts", r"\$\d|\b(dollars?|bucks|price|pricing|cost|costs|paid|pay|fee|subscription|refund|budget|revenue)\b", 3),
    ("workbench", r"\b(build|built|install|setup|set up|mic|microphone|camera|lens|keyboard|tested|review|unboxing|tool)\b", 4),
    ("chalkboard", r"\b(means|definition|defined|step one|first step|here's how|how to|explain|lesson|learn)\b", 3),
    ("notebook", r"\b(i felt|my story|i learned|years ago|when i was|songwriting|wrote|journal|grateful)\b", 2),
    ("pinboard", r"\b(three things|five things|top \w+|list|compare|versus|pros and cons|options)\b", 2),
]


def pick(text, brief=None):
    """A style for this recording: the brief's choice, news when there is a headline or screenshot,
    else the first subject whose words show up often enough, else the default."""
    brief = brief or {}
    want = str(brief.get("style") or "auto").lower()
    if want != "auto":
        if want not in STYLES:
            raise SystemExit(f"unknown style {want!r}; one of {', '.join(STYLES)} (or auto)")
        return want
    if brief.get("headline") or brief.get("image"):
        return "newsdesk"
    low = str(text).lower()
    for name, pat, need in _HINTS:
        if len(re.findall(pat, low)) >= need:
            return name
    return DEFAULT


def table():
    w = max(map(len, STYLES))
    return "\n".join(f"  {k:{w}s}  {v['about']}\n  {'':{w}s}  for: {v['good_for']}" for k, v in STYLES.items())
