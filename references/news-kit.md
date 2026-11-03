# News kit: AI, SI and tech news shorts for X

Adem posts only on X: many short talking-head takes on AI/SI news, tech news
and his own views. This kit makes a news short in the house style quickly and
keeps it postable: real sources on the desk, his take as the original part,
and a pre-posting check. The engine and the house style are unchanged
([edit-engine.md](edit-engine.md), [art-direction.md](art-direction.md)).

## Contents
The story shape · One command · Evidence on the desk · Claim stamps ·
The X check · Accuracy rules · Recipes

## The story shape (30-60 s)

1. **Hook, 0-3 s.** The news in one line, in his words, and why it matters.
   The title sticky on the first frame says it in one to three words: the
   first frame is the thumbnail.
2. **Source, 3-10 s.** The evidence lands on the line where he states the
   news: the real screenshot, or the headline quoted verbatim, with its
   source named and its status stamped.
3. **Take.** His opinion, on a wider face. This is the original part, the
   reason to follow him and the part X pays for.
4. **Why it matters.** One concrete consequence or thing to watch.
5. **Verdict.** One line, and end on the cut. No call to action
   ([pacing-and-hook.md](pacing-and-hook.md)).

## One command

```bash
thd news RECORDING --out DIR --title "GPT-6" \
    --headline "the headline, verbatim" --source "The Verge" --date "Nov 3" \
    [--image ~/Desktop/headline.png] [--stamp REPORTED] [--look newsroom|lab]
thd prep DIR/plan.yaml
thd inspect DIR/plan.yaml      # fix every !
thd all DIR/plan.yaml          # ... audit, then the X check
```

`thd` is `scripts/thd` in this skill. `news` runs autocut and writes
`DIR/plan.yaml` with one shot per kept line:
- **First frame:** face P plus the title sticky.
- **Evidence:** a doc shot on the first line that says the headline's words
  (otherwise the second line).
- **Take:** face W.
- **Then:** split (him and the evidence), face P and face W, alternating.
- **Last line:** the desk with every paper.

The voice chain is `full`, which suits his raw recordings; use `light` for
downloads. The plan ends with a film burn.

The draft renders as it stands. The editor's work is the story: reorder,
drop or merge lines, then re-check the shots, because they follow the
segments. The plan's header lists the checklist.

`--look newsroom` gives the kraft desk with clippings; `lab` gives linen and
printouts for model, code and benchmark stories.

## Evidence on the desk

**A real screenshot**: the strongest evidence, and the default for posts.
Capture it with Shift-Cmd-4 and never edit it; crop is the only change.

```yaml
documents:
  evidence:
    kind: screenshot
    image: ~/Desktop/headline.png        # relative paths are read from the plan's folder
    crop: [0, 0.08, 1, 0.55]             # x0 y0 x1 y1 fractions: keep the part that matters
    source: "The Verge · Nov 3"          # typed on the print's bottom border
    marker: {box: [0.04, 0.2, 0.9, 0.5], at: "C.w:six", dur: 0.45}   # circle part of it (image fractions)
    stamps: [{at: "B.out-0.1", text: REPORTED}]                      # lands on the image
```

The print slaps, tapes, pins and stamps like any paper. A doc shot frames the
whole print, and on the marker it pushes into the circled part.

For a post, the source is `"@handle on X · Nov 3"`. **Never rebuild a post or
a headline to look real.** The print is evidence, so the picture must be the
real capture.

**A quoted headline** (a clipping) works when there is no good screenshot:

```yaml
  headline:
    kind: clipping
    source: "The Verge · Nov 3"
    lines: ["h:OpenAI ships", "h:GPT-6 today", "rule", "c:VIA THE VERGE · NOV 3"]
```

The headline is verbatim, split over `h:` lines of about 15 characters (four
at most; longer headlines go in `l:` lines). The `VIA` line names the source.
Never use a masthead or logo. A clipping of his own phrase says `source: own`.

## Claim stamps

| stamp | when |
|---|---|
| CONFIRMED | the company or primary source says so, or he checked it himself |
| REPORTED | a credible outlet reports it; not independently confirmed |
| UNCONFIRMED | a rumour, a leak, one anonymous source |

Stamp the evidence on the line where he states the claim. Each stamp gets the
stamp sound and a camera shake. Say the status out loud too ("reportedly",
"according to").

## The X check

`thd xcheck PLAN` runs as the last step of `thd all`. It writes
`review/X_CHECK.md` and `review/x_feed_preview.png`, which is the first frame
at 390 px wide, roughly a phone feed.

**FAIL**
- A call to action, said or printed: "like and subscribe", "follow for more",
  "let me know in the comments", "repost this", "comment below" and so on. The
  ordinary word "like" never triggers it.
- A screenshot or clipping with no `source:`.

**WARN**
- Spoken words that are neither captioned nor on paper.
- No title on the first frame, or title text under 14 px at feed width.
- The first word later than 0.5 s.
- Captions under 20 px at feed width.
- A file over 512 MB.
- A soft ask ("let me know what you think").

**INFO**
- Claims to verify: every number, $, % and name, with times, as a checklist.
- Length over 140 s.
- One- or two-word captions dropped on purpose between two papers.

**Why** (third-party reporting, Nov 2026; help.x.com refuses automated reads,
so confirm in Creator Studio):
- X's Original Content Rewards replaced Creator Revenue Sharing in
  September 2026.
- Eligibility: Premium, 500 verified followers, and 500k verified Home
  Timeline impressions in 90 days.
- It pays on impressions of original posts from Premium viewers.
- "Original only": reposted or reproduced content does not qualify.
- Accounts that repeatedly ask for likes, reposts, replies or follows are
  removed.
- Under the older program, a post corrected by Community Notes earned
  nothing. Assume that still holds.

## Accuracy rules

- **Headlines verbatim, screenshots unedited** (crop only). Every printed
  claim names its source.
- **Numbers carry their unit and date.** Say "reportedly" when the source is
  reporting.
- **Keep his hedges.** They are what keeps a take honest.
- **Work through the claims list in `X_CHECK.md` before posting.** ASR
  mishears names and numbers, so check each against the source, not the
  transcript.
- **The take is his.** The papers quote sources; they never put words in
  anyone else's mouth.
- **If a claim turns out wrong, correct it in public** in a reply or a new
  post.

## Recipes

- **Breaking news (30 s):** hook, then the screenshot stamped REPORTED, then
  the take, then the verdict. Use the newsroom look.
- **Reacting to a post:** a screenshot of the real post with source
  `"@handle on X · date"`. Circle the line he reacts to with a marker box, and
  let the split shot carry his reaction.
- **Model or benchmark story:** the lab look. The screenshot of the chart is
  the evidence. Print his own numbers on a `printout` (`bar:` lines), each
  with its source.
- **Rumour:** stamp it UNCONFIRMED, say so in the first ten seconds, and end
  on what would confirm it.
