# Art direction: the house style

Treat every video as a show. It has a set, a camera operator, a graphics
package and a sound designer, and they all serve one performer. This file
holds the taste. The other references hold the mechanics.

## Contents
Principles · House DNA · Treatments (sets) · Sequence library ·
Editing craft · Director's pass

## Principles

1. **Every frame photographs a real object.** Paper, ink, glass, light: things
   with weight that cast shadows, catch light and wear. Nothing floats as a
   flat vector in a void. This is what "analogue" means here.
2. **The camera is a character.** It leans in when the idea sharpens, steps
   back when it opens up, and snaps on the punchline. Movement carries meaning;
   it is never decoration.
3. **Type is performed, not placed.** Words arrive the way they are spoken.
   They rise on the syllable, land with weight, and relocate when they become
   the point.
4. **Contrast is the engine.** Contrast in scale (huge and tiny), tempo (rapid
   and still), tone (dark board and ivory page) and sound (dense and silent).
   Uniform anything is boring.
5. **Evidence over decoration.** Every element proves or explains something.
   If it only decorates, delete it.
6. **Use one accent, like a scalpel.** Vermilion marks the single thing to look
   at, never more than about 10% of the frame.
7. **Restraint is the luxury.** Leave air. Hold on the human moment. An empty
   frame with one perfect element beats a full one.
8. **The human is the hero.** Skin stays natural and the performance comes
   first. The edit amplifies him and never buries him.

## House DNA (identical in every video)

Viewers should recognise the channel within a second, whatever the topic.
These things never change:
- **Captions:** Avenir Next Condensed Heavy, uppercase, off-white with a soft
  shadow, and the active word in vermilion. See graphics-and-type.md.
- **Accent:** vermilion #E2452B.
- **Finish:** the `look.Finish` "medium" preset (grain, halation, weave,
  vignette) over everything.
- **Signature devices:** real paper on a real desk, keyed to his words: at
  least one document per video, chosen by what the subject would actually
  produce, plus the vermilion marker or a stamp. Receipts are for money:
  costs, prices, usage. A songwriting video gets a lyric page, a gear test a
  spec card, a take a clipping, a how-to a blueprint (table below). These are
  the channel's handwriting; the receipt was one word of it.
- **Core sound kit:** paper that sounds like what it is: slaps, flutter, tape,
  pen or marker on paper, typewriter keys, thermal printer, stamp thud, plus
  whoosh, sub hit and shutter for emphasis. Same family every time; the
  engine picks each paper's sound (treatments.py SOUNDS).
- **The ending ritual:** "the human out" from the sequence library. This is a
  default. Skip the callback stamp when his last human moment is the stronger
  final beat.

## Treatments (sets): pick one per video by topic

A treatment is the set and its materials. The house DNA rides on top of it.
Keep one treatment per video; a second one is only for a deliberate section
change.

### In the engine (`treatment:` in the plan)

| treatment | desk surface | papers | subjects |
|---|---|---|---|
| evidence | charcoal board | receipt, spec card, printout | money, costs, usage, verdicts with numbers |
| studio | walnut desk | lyric notebook page, sticky note, music staff | songwriting, music, creative process, personal |
| workshop | green cutting mat | spec card, blueprint, index card | gear, builds, how-to, product tests |
| newsroom | kraft paper | newsprint clipping, index card, sticky | opinions, industry takes, claims, reactions |
| lab | indigo bookcloth | tractor-feed printout, card, blueprint | AI, software, prompts, tech explainers |
| pinboard | cork | index card, sticky, clipping | plans, ideas, lists, research, comparisons |
| classroom | chalkboard slate | index card, blueprint, sticky | teaching, definitions, language, maths |

Choosing papers inside a treatment:
- One hero paper per idea, written in his words (or his numbers). A paper
  never adds a claim he did not make; clippings never carry a real outlet's
  name.
- The paper writes, types or prints itself as he says it (`follow`, or a cue
  per line). Seeing the idea arrive on paper is the device; captions step
  aside while it does.
- Red marks carry the turn: strike a line on "but", tick a box on "works",
  circle the line that is the point. One marker circle per video is a beat;
  three is wallpaper.
- Short papers (sticky, card) for rules and tips; pages (note, printout,
  blueprint) for anything that builds over several lines.

The prose sets below are the fuller art direction. EVIDENCE BOARD is the
`evidence` treatment. FIELD JOURNAL is closest to `studio` and `classroom`
(lines and blueprints write on; stroke-by-stroke diagrams are not built yet).
SIGNAL has no engine treatment yet: use `newsroom` for timely takes. NIGHT
LAB's paper side is `lab`; its light table and glows are not built yet.

### EVIDENCE BOARD: tests, money, receipts, product claims, "I tried X"
- **Stage:** a charcoal board or dark worn desk (#1E1C1A to #2A2724), lit by
  one warm pool of light from the top-left with falloff. Paper is pinned and
  taped to it.
- **Camera window:** a print with a 16-24 px off-white border or a torn edge,
  tilted 0-2 degrees.
- **Materials:**
  - thermal paper #F3F1EA printed in faded grey #5B5853;
  - halftone clippings;
  - tape with soft shadows.
- **Type:** Courier New Bold or American Typewriter Condensed on receipts;
  Didot for hero numbers.
- **Transitions:**
  - paper swap: the next element slides over the old one in 8 frames;
  - flash bulb (2 white frames and a shutter) at section changes.
- **Sound:** thermal printer, stamp thud, paper, a low room hum.
- **Finish:** medium, with halation on the light pool.

### FIELD JOURNAL: explainers, how X works, history, comparisons
- **Stage:** ivory paper #E9E1D3 with a faint ruled grid at 2-3% opacity.
  Pencil #6E6A63 and ink #15120F carry the drawing; vermilion is the only
  colour.
- **Diagrams:** draw on stroke by stroke, on twos. Labels are typewritten.
  Photos are halftoned and taped. Use cross-sections that assemble as he
  explains.
- **Camera window:** a torn-paper window or a photo-corner mount.
- **Transitions:**
  - page slide: the new page slides over with a moving shadow;
  - ink bleed: a blot spreads to fill the frame in about 10 frames.
- **Sound:** pencil scratch, page slide, soft typewriter.
- **Finish:** subtle to medium. Paper texture is strongest in this set.

### SIGNAL: timely takes, industry and platform news, "what's happening"
- **Stage:** a dark studio wall. His window sits in a worn monitor bezel with
  2-3 px scanlines at about 6% opacity, slight barrel distortion and chroma
  bleed on the window only. A ticker strip carries the key claim. A real edit
  timecode in monospace sits in a corner.
- **Colour:** cool shadows and warm skin. Phosphor amber #FFB347 is this set's
  secondary tone for data; vermilion stays the house accent (the tally light).
- **Transitions:**
  - channel flip: 3 frames of noise and roll plus a horizontal hold slip;
  - signal drop: the picture collapses to a line, for the ending.
- **Sound:** a faint CRT whine, static bursts on flips, relay clicks.
- **Avoid:** imitating real networks' logos or packaging, and claiming
  "breaking" news that isn't.

### NIGHT LAB: AI and tech deep dives, building, retro-future experiments
- **Stage:** near-black #0E0F10 with practical glows. A light table holds
  backlit negatives and blueprints (cool white #DDE7EE), oscilloscope traces
  carry data, and drawings sit on top as 3 px lines with a soft glow.
- **Transitions:**
  - fluorescent flicker on (4 frames);
  - a light-bar scan.
- **Sound:** hum, fluorescent tick, soft synth pad (if there's music), relay
  clicks.
- **Finish:** medium grain and heavier halation, because the glows are the
  point.

### COMEDY KIT (works inside any treatment)
- freeze verdict;
- alter-ego line;
- scale gag;
- redaction;
- record scratch into silence.

See shot-grammar.md "Persona beats". One or two per video lands; five is a
different genre.

## Sequence library

These are tested shapes with frame timings at 30 fps. Adapt them; don't stamp
them out identically every time. A device or move that repeats on a formula
becomes the new template, which is the failure this whole skill exists to
prevent.

1. **THE RECEIPT DROP** (a hard number):
   - Cut to C, 2 frames before the stressed syllable.
   - The receipt prints down from the top edge over 0-12 frames, with
     +/-1 px jitter and the printer sound.
   - On the number's onset the number rises on the receipt over 8 frames, with
     a sub hit.
   - 6 frames later the STAMP slams with a 6-frame shake.
   - The receipt flutters during the hold.
   - On the next cut it tears off upward over 5 frames, with a rip.
2. **THE REVEAL** (the big number or claim):
   - 8 frames of black or charcoal, with room tone only or a riser ending on
     the reveal.
   - Hero type rises over 8-10 frames with 3% overshoot and a sub hit.
   - Hold at least 1.2 s with a 2% drift (reading time).
   - A 5-frame unit exit, then back to H on his interpretation.
3. **THE PROOF PUSH** (evidence):
   - The clipping slides in over 8 frames (easeOutBack) with a paper sound.
   - The camera pushes into it from 1.0 to 1.18 across the sentence.
   - The MARKER circles the key phrase on its spoken word, over 10 frames on
     twos.
   - Cut to C on the interpretation ("...and that's the problem").
4. **THE COMPARISON** (A vs B):
   - A arrives with its number large.
   - B arrives on B's number at identical scale and baseline.
   - On the verdict word the worse one turns vermilion, and a ledger line
     states the difference.
   - Run the alignment check before rendering.
5. **THE TURN** (opinion or twist):
   - Pull back to W (or shrink the window) for the setup.
   - 4-6 frames of air.
   - A 6-frame snap zoom to X on the opinion's key word, with blur and a
     whoosh.
   - Hold X no more than 1.5 s, then return to H.
6. **THE ASIDE** (comedy):
   - Either a freeze of 12-20 frames, with xerox, a marker arrow, a Noteworthy
     label and a shutter sound;
   - or one alter-ego line.
   - Return on a hard cut with no transition.
7. **THE RE-HOOK** (every 30-45 s):
   - Change the window state or set.
   - A monospace section kicker slides in over 8 frames.
   - A flash bulb.
   - The line itself is a question or an escalation.
8. **THE HUMAN OUT** (ending):
   - The last line at H with a slow 3% push. Let a smile or shrug breathe
     for 0.8-1.5 s only if you checked it frame by frame and with sound;
     otherwise end on the word.
   - Hard cut to the callback: the opening receipt or exhibit returns and gets
     its final STAMP, 1.5-2.5 s.
   - Black on the thud, plus 6 frames.

## Editing craft

- **Cut on thought, not on breath.** The cut belongs where the idea changes,
  just before the first stressed word of the new idea.
- **J-cuts and L-cuts.**
  - Into a cutaway, start its sound 3-6 frames before its picture.
  - Out of one, let the picture linger 4-8 frames into his next line when that
    line comments on it.
- **Reaction holds, verified.** 6-12 frames on his face after a punchline beat
  any graphic, but only a reaction you checked frame by frame and with sound.
  A silent look-down can be a burp, swallow, yawn, sniff or a glance at
  something off-camera (the 2026-11-03 demo held a burp as a "wry reaction";
  Adem caught it). Default: end the line on the word.
- **The 3-and-1.** Three quick cuts, then a hold. Never metronomic: vary the
  holds (1.1, 0.7, 1.6, 3.2 s...).
- **The picture never waits for the voice.** If a graphic is late, move it
  earlier; never slow the speech.
- **The 10-second question.** Every 10 s, ask "what is new on screen?" If the
  answer is nothing, add a cut or a move.
- **Kill your darlings.** A beautiful graphic that slows the story goes.

## Director's pass (before rendering a section)

1. What is the one idea here, and can a muted viewer get it from frame 1?
2. Where does the eye go in each frame? There should be one focal point.
3. What changes every ~2 s?
4. Which element is decoration? Delete it.
5. Is there one moment of stillness and one of surprise?
6. Is it physically believable: one light, real shadows, real materials?
7. Is the geometry clean: grid, baselines, optical centring?
8. Does it sound finished with your eyes closed?
