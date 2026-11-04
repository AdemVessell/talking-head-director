# Edit engine: one plan file per video

Run it as `scripts/thd COMMAND ...` from any folder or agent. `thd doctor`
checks a machine; `thd selftest` proves the whole pipeline in about a
minute, so run it before and after any engine change. News shorts for X:
`thd news` drafts a news-shaped plan and `thd xcheck` (also the last step of
`thd all`) checks it before posting; see [news-kit.md](news-kit.md).
`scripts/edit_engine.py` turns a plan (YAML or JSON) into a finished vertical
edit: story cut, a camera over physical paper on a desk surface (in the
house look, a perspective journey camera with plane changes: [journeys.md](journeys.md)),
documents that write, type or print themselves on his words, word-timed
captions, designed sound, and a QA report. Worked examples, copy the method,
never the facts:

- `examples/hologram-diorama/`: the house look (2026-11-04). A colour
  journey with two Blender diorama scenes (`shot: scene`), their scripts
  and word times beside the plan.
- `examples/songwriting-journey/plan.yaml`: the house look over papers.
  Views, plane changes and pulses on the songwriting edit.
- `examples/songwriting-studio/plan.yaml`: the same edit on the flat
  camera. Studio treatment, shot templates, a lyric page that writes itself
  as he says it, autocut draft, automatic sound. 45 s from a 77-line plan
  (the hand-placed RØDE plan needed 155 lines for 27 s).
- `examples/rode-holder-test/plan.yaml`: product test with a measured result,
  hand-placed layouts and beats (the long way), 23.976 fps download.
- `examples/grok-topup-v2/plan.yaml`: money receipts and a 3D film wall, the
  first approved cut.

## Contents
Workflow · Plan anatomy · Treatments and surfaces · Documents · Shots ·
Hand-placed layouts and beats · Time expressions · Captions · Sound · QA ·
Speed · Gotchas

## Workflow (one new recording)

1. `edit_engine.py autocut RECORDING --out DIR`: transcribes (once, cached as
   `transcript.json`) and drafts `plan_draft.yaml`: fillers, stutters, exact
   repeats and long pauses out; every in/out in the quiet before the first
   sound and after the last consonant (sibilants included). `autocut.txt`
   shows the transcript with each removal marked. It never reorders or drops
   a sentence: that is the edit.
2. Choose the story on the draft (pacing-and-hook.md): hook, stakes,
   evidence, caveat, verdict, ending. Drop weak lines, trim "you know"
   openers, keep his hedges and his sung or performed moments whole.
3. Pick the treatment from the subject and write the documents (his words,
   never new claims) and one line per shot (below).
4. `edit_engine.py prep PLAN`: extracts the source ranges you use, films,
   face tracks and a forced alignment of every line.
5. `edit_engine.py inspect PLAN`: sound regions (voice or hiss) and word
   timings around every cut. A `!` line means a cut sits inside sound: move
   it into a gap. After moving cuts, `edit_engine.py align PLAN` (seconds,
   not a full prep).
6. `edit_engine.py edit PLAN`: EDL, edit-time words, dialogue track, SRT.
7. `edit_engine.py holds PLAN`: a frame strip for every silent stretch on his
   face. **Look at every one** (burps, swallows, glances; held sung notes
   show up here too and are fine).
8. `edit_engine.py stills PLAN --at 0,1.5,4,...`: check each shot's
   composition on `stills_sheet.jpg` (about 0.3 s a frame). Frame 0 is the
   thumbnail.
9. `edit_engine.py all PLAN`: sound, render, assemble, holds, audit
   (`work/review/QA.md`, with an ASR diff of the finished audio).
10. Watch it at normal speed with sound. Say plainly what you could not check.

## Plan anatomy

```yaml
name: my-edit
work_dir: ~/Movies/thd-work/my-edit
source: /path/to/recording.mov
fps: 30                       # 23.976 for 24000/1001 sources
tail: 1.0                     # seconds after the last line
treatment: studio             # evidence studio workshop newsroom lab pinboard classroom
presenter: {eye: 0.30, res: 1.7, grade: {...}}   # defaults for every presenter print
face: center                  # optional: no face detection (screen recordings, no frontal face);
                              #   or {x: 0.5, eye: 0.42, width: 0.3} as fractions of the source frame
segments:                     # the story, in edit order (source seconds)
  - {id: A, in: 0.64, out: 2.04, air: 4, text: "verbatim words", display: "display form"}
documents: {lyric: {kind: note, lines: [...], cues: {...}, marker: {...}}}
journey: {focal: 1.15, dark: 0.35, fog: 0.9, dof: 0.8, pulse: 0.12, pulses: ["B.w:bones"]}   # the house look
shots: [{at: 0, shot: face, size: P, view: descend}, {at: "B.pin", shot: doc, doc: lyric, via: dive, view: lean}, ...]
films: {name: {video: path | self, from: 1.4, to: 9.8}}
labels: {mywork: {text: MY OWN 3D WORK}}
captions: {groups: [...], hide: [...]}       # optional; automatic by default
sfx: [{kit, at, db, align}]                  # on top of the automatic sound
mix: {voice_chain: full | light, voice_lufs: -16, lufs: -14, fade_out: [t0, t1]}
end: {burn: [t0, t1]}
finish: medium
```

`air` is frames of breathing room after a line (`fill: post` shows this
take's silent post-roll, `pre` the next take's pre-roll).

## Treatments and surfaces

Same camera, light, grain, captions and accent in every video; the desk
surface, the papers and their sounds follow the subject (treatments.py):

| treatment | surface | papers (first = default) | subjects |
|---|---|---|---|
| evidence | charcoal | receipt card printout | money, costs, usage, verdicts with numbers |
| studio | walnut | note sticky staff | songwriting, music, creative process, personal |
| workshop | mat (green cutting mat) | card blueprint index | gear, builds, how-to, product tests |
| newsroom | kraft | clipping index sticky | opinions, industry takes, claims |
| lab | linen (indigo bookcloth) | printout card blueprint | AI, software, prompts, tech |
| pinboard | cork | index sticky clipping | plans, ideas, lists, research |
| classroom | slate (chalkboard) | index blueprint sticky | teaching, definitions, language |

A layout or shot may override `surface:`; mixing papers across treatments is
fine when the story needs it (a receipt in the studio if he talks about what
the session cost). Surfaces are generated once per machine
(`~/.cache/thd_engine`).

## Documents

```yaml
documents:
  lyric:
    kind: note                      # receipt card note sticky clipping blueprint printout index staff screenshot
    lines: ["h:being lost", "l:losing your purpose", "x:it's in my bones", "done:demo", "n:1:take a phrase"]
    cues: {1: ["D.w:losing", "D.we:purpose,"]}   # line 1 writes from "losing" to the end of "purpose,"
    follow: true                    # or: every text line writes itself while he says it
    marks: {2: "E.w:but"}           # the red accent of line 2 (strike, tick, bar fill) lands on "but"
    marker: {lines: [4, 5], at: "L.w:rhetorical", dur: 0.5}   # vermilion circle, drawn on twos
    slap: "F3.w:bones-0.08"         # arrival: slap | drop: [t0, t1, px] | appear; tape_at
    stamps: [{text: TESTED, at: "H.pout+0.18", line: 3}]
    reveal: type                    # override the kind's reveal: ink type write draw print
```

Line specs: `l:` `c:` `r:` text · `h:` / `h:c:` headline · `D:r:` big value ·
`x:` struck through · `q:` quote · `check:` / `done:` box / ticked box ·
`n:3:` numbered step · `bar:LABEL:VALUE:FRACTION` measurement bar ·
`box:A|B|C` boxes and arrows · `rule` `rule2` `gap` · `WAVE:t0:t1` real
waveform of source seconds (one shared scale per plan). A line that is too
long shrinks to fit and says so.

Each line is two layers, ink and vermilion accent, so the strike, tick or bar
fill can land on its own word. Ink may overhang its line box (descenders cross
the rule below, as handwriting does); each line texture is cropped to its ink. Reveals by kind: receipt and clipping `ink`
(thermal pop), card and index `type` (one key strike per character, each with
its own keystroke sound), note, sticky and staff `write` (a pen's soft head),
blueprint `draw`, printout `print` (bursts). A cue is `"expr"` (default length
from the text), `[expr, seconds]`, `[expr, "end-expr"]` or
`{at, dur | to, mode}`. `values`/`waves` (receipt era) still work.

Write his words or his numbers, never new claims. Headlines on clippings are
his phrases; a real outlet's headline appears only verbatim, with a
`c:VIA OUTLET · DATE` line and `source:`, never as a masthead or logo. Label
reconstructions. For real evidence use `kind: screenshot`: a real capture
printed with its source (`image:`, `crop:`, `source:`, stamps,
`marker: {box: [...]}`); see [news-kit.md](news-kit.md).

## Shots (the fast way)

One line per shot; each runs to the next. The engine builds the layout and
the camera, and writes what it built to `work/review/shots.yaml`.

| shot | what it does |
|---|---|
| `face` | presenter print is the hero; `size: P` (whole print) W H C X or a number; `docs: [{doc, slot: br bl tr tl low}]` lays papers on the print |
| `doc` | one paper is the hero. A tall page: the camera follows each line as it is written (one zoom per paper, set by its widest line), then pulls back. A short card: close on the text, a move onto each line as it is typed. A marker circle in the shot is framed. `presenter: false` drops the small print |
| `split` | print and one paper together: stacked for wide paper, side by side for a receipt or sticky |
| `desk` | overview of the print and up to four papers, slow pull-out (endings, recaps) |
| `film` | a film print is the hero, the print small in a corner |
| `scene` | a full-frame clip (a Blender diorama, `scene: scenes/x.mov`, `start:`) replaces the desk; captions, finish and plane changes still apply. See [dioramas.md](dioramas.md) |

Any shot: `snap: true` (6-frame snap in), `punch: "C.w:bones"` (14% closer
on the word), `move: push | pull | drift | hold`, `rot`, `board`, `light`,
`surface`, `name`; in a journey plan also `view:` and `via:` ([journeys.md](journeys.md)). A paper with no arrival cue slaps in 0.2 s into its first
shot (receipts and printouts drop). Inside face and split shots every jump
cut between takes switches the framing (13% closer, then back), so no jump
cut lands on a held frame (`jumps: false` to turn it off). Captions are
hidden while a doc shot shows a line being written with his words.

Hand-written `layouts` and `beats` still work and can sit alongside shots.

## Hand-placed layouts and beats (full control)

- Layout: `board: [bx, by]` (surface offset), `light: [x, y, sigma, lo, hi]`,
  `surface`, `presenter` (`center`, `inner`, `rot`, `face_frac`, `eye`,
  `x_offset`, `res`, `border`, `tapes`, `grade`), `films`, `labels`,
  `documents` (or `receipts`): `{left, top, width, rot, tape, tape_index,
  tape_angle, pin: true | 0-2}`.
- Beat: `{name, layout, from, to, camera: [[t, target, ease], ...]}`; targets
  `{center, zoom}`, `{face: W|H|C|X, eye, screen_x}`,
  `{doc: name, line: k, zoom, screen_y}`, `{fit: [names], band: [top, bottom]}`;
  eases `linear io2 io3 o3 oexp`; any target takes `zoom_mul dx dy`.

## Time expressions

`12.5` · `END` · `A.in` `A.out` (audio) · `A.pin` `A.pout` (picture, with its
air) · `A.w:lasted` (word start) · `A.w:5#2` (second "5") · `A.we:minutes`
(word end) · `A.w:[covid-19]` · offsets `+0.12`, `-2f`, chainable. Words match
the `display` form, case-insensitive. Key every cue to a word or a segment
edge: a re-cut then moves everything with its words.

## Captions

Automatic cards by default; `groups` for manual cards; `hide` ranges keep
captions off while a paper says the same words (shots add these, and hide the
few words between two written lines less than 1.5 s apart). A fragment of two
words or fewer stranded between hidden lines is dropped (a lone orange "IT"
between two papers reads as a glitch). A card never ends on a negation and
never runs across a sentence end ("OPPOSITE OF THAT?" | "YOU KNOW IT'S").
`captions.srt` always carries every word.

## Sound

With shots, sound is automatic (`sfx_auto`, `work/review/sfx_auto.json`): a
slap or drop as each paper lands, tape, each line's pen, keys or print head
for exactly as long as the line takes to appear, red marks, the marker
circle, stamps, film prints, punch-ins, the end burn. `sfx` adds on top;
`sfx_mute: [kit]` silences one. Kit: Apple's Final Cut Pro library
(`printer tick sub lfe lfe_big swish swish_short whoosh shutter thud knock
stamp pencil typewriter`) plus `marker paper_slap flutter tape burn`.
`voice_chain: light` for audio that is already produced (downloads) or is the
evidence (a tap test). A library file that is not installed gets a synthetic
stand-in, so the edit still finishes; `thd doctor` lists what is missing.

## QA

`work/review/QA.md`: holds, pauses, first change, loudness, wpm, sync against
the dialogue edit (should be 0 ms), and an ASR transcript of the finished
audio diffed against the plan. A camera that follows typing or writing is
real motion the hold metric does not count: read long holds against the shot
list. Sung lines count as pauses. Numbers are necessary, not sufficient.

`thd critic PLAN` (the last step of `all`, about 10-40 s) builds what a
reviewer scores from the rendered MP4 alone, in `work/review/critic/`:
- `sheet_NN.jpg`: two frames a second.
- `phone_NN.jpg`: the first frame and the middle of every shot at 360 px wide.
- `strip_*.jpg`: consecutive frames through every plane change, the fastest
  move, any held frame and any late hit, with each sound cue marked on its
  frame.

It also measures:
- one frame drawn twice by fresh renderers (they must match: FAIL means
  something is unseeded);
- whether the MP4 still matches the plan;
- held frames inside moves;
- stretches of 1.5 s where the picture holds still;
- stamps, slaps and knocks that miss the frame where the picture jumps.

`work/review/CRITIC.md` holds the rubric (score 1-10, list the worst three,
fix, re-render, until every line is 8+) and the measurements.

## Speed (this Mac, 8 workers)

A 45 s plan: autocut 2 s (transcript cached), prep about 70 s, stills about
0.3 s a frame, `all` about 3.7 min including the ASR check. A full frame
renders in about 140 ms (more while motion blur is on); `render --proof`
renders half size without blur for timing checks. A 4-minute video is about
5x that. Journey plans cost more: the 19 s hologram cut runs `all` in 104 s
with other work on the machine ([journeys.md](journeys.md)).

## Gotchas

- Cut points: a sibilant ("veins", "phrase") is quiet in loudness but loud
  above 4 kHz. Inspect's sound regions include that hiss; trust its `!` lines
  over a loudness dip.
- ASR stretches words across pauses and invents "you know" in hesitations:
  check by ear before trusting either.
- YouTube downloads are 720p: shots cap face enlargement at 2.3x; prefer
  `size: P` and W, and let the papers carry the scale changes.
- Downloads are often already edited: find their own cuts and keep every
  segment inside one source shot.
- A paper's lines are its claims: measure before printing a number, print it
  with its hedge, and say how it was measured on the paper itself.
