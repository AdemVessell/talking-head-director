# Graphics, devices, type and captions

## Contents
Identity: Receipts · Real before generated · Make it explain · Type system ·
Captions · Motion · Alignment · Image prompts

## Identity proposal: "Receipts" (a proposal; show Adem, don't assume)

Adem's videos are first-hand tests: he spends, measures, reports. Give that an
ownable visual language of evidence. Every claim gets a receipt. This is the
weathered-editorial direction with a job to do. Reuse these devices across
videos so the channel is recognisable, using 3-5 per video, not all at once.

1. **RECEIPT**: a thermal strip prints down from the top edge (10-14 frames,
   slight feed jitter, printer SFX). Monospace line items; the key number large.
   It tears off on the cut (rip SFX). Use it for hard numbers: prices, minutes,
   counts.
2. **STAMP**: a verdict word ("TESTED", "BURNED", "~5 MIN", "NOPE") slams in at
   1.15x to 1.0x over 2-3 frames, with uneven ink, -8 to +8 degrees, a thud and
   a camera shake.
3. **MARKER**: a circle, underline or arrow draws on in 8-12 frames over his
   face or the evidence. Use the accent colour, a wobbly path, animated on twos.
4. **CLIPPING**: evidence (his own screenshot, a quote, a chart built from
   verified numbers) arrives as a printed clipping, halftoned or photocopied,
   torn and taped, sliding in over 8 frames with paper foley. Then the camera
   pushes into it.
5. **REDACTION**: a black bar wipes across a word, for a joke or "the part they
   don't say".
6. **LEDGER**: a running tally in a corner (for example "$45.00 to $0.00") that
   updates on each beat.

## Real before generated

1. Real material Adem owns or can capture: his screen recordings and
   screenshots (billing pages, the product UI, usage graphs), his receipts, his
   hands doing the thing, his own films and 3D work. When the script names a
   thing, ask him for it. When he names his own work, cut to the real thing on
   the noun: one large moving insert when the detail matters, or prints that
   arrive one per word when accumulation is the point (the "3D / animation /
   things" wall in Claude's v2). Find the source's shot changes first and keep
   each playing clip inside one shot.
2. Diagrams and charts built in code from verified numbers.
3. Generated images (OpenAI) for metaphor and atmosphere only. Always
   print-treat them (`look.halftone`, `look.xerox`, `look.misregister`) so they
   read as material, never as AI stock. Avoid centred objects on seamless white,
   gloss, and generic robots, clocks, coins or brains.
Label illustrations when they could be mistaken for evidence.

## Make it explain

Each insert answers "what noun or number is he saying right now?" Then animate
the relationship instead of posing the object: a counter drains while a clock
runs; two receipts sit side by side at the same scale so the difference is
visible; a strip of credit burns down as he talks. If a graphic only names the
topic, cut it or make it do something.

## Type system

| Role | Face | File (PIL index) |
|---|---|---|
| Display serif: hero words, numbers | Didot Regular/Bold, or Bodoni 72 Book/Bold | Supplemental/Didot.ttc (0, 2), Supplemental/Bodoni 72.ttc (0, 2) |
| Display grotesk: punchier videos | Helvetica Neue Condensed Black; Futura Condensed ExtraBold | HelveticaNeue.ttc (9); Supplemental/Futura.ttc (4) |
| Captions | Avenir Next Condensed Heavy (Bold for long lines) | Avenir Next Condensed.ttc (8; 0) |
| Labels, receipts, data | Courier New Bold, American Typewriter Condensed, Menlo | Supplemental/Courier New Bold.ttf; Supplemental/AmericanTypewriter.ttc (5) |
| Hand notes, MARKER labels | Noteworthy Bold, Marker Felt Wide (sparingly) | Noteworthy.ttc (1); MarkerFelt.ttc (1) |

Use one display face per video. Keep a scale range of 8x or more: hero numbers
280-420 px tall, filling 70-90% of the width; headlines 90-140 px; captions
64-84 px; labels 28-36 px (never smaller). Tight tracking on display (-1 to -3%),
open tracking on all-caps mono labels (+8 to +12%). Colours: ink #15120F, paper
#E9E1D3, charcoal #22201D, accent vermilion #E2452B (10% of the frame or less).
Highlighter #F2D43D appears only behind text as a marker stroke.

## Captions

- One caption system per video. Verbatim, word-timed, 1-4 words per card,
  18 characters or fewer per line, one line preferred. Break at punctuation and
  pauses. Keep numbers with their units and names whole.
- Avenir Next Condensed Heavy, 64-84 px, uppercase. Over footage or dark
  stages use off-white #F4EFE6 with a soft dark shadow (blur 6-10 px, ~60%). On
  light paper stages use ink with a paper-coloured halo:
  `CardRenderer(light_stage=True)`. White captions vanish on ivory. B's serif
  pill was an implementation choice, not a requirement.
- On the active word's onset, use the accent colour or a 1.06x pop over 3
  frames. Numbers, names and the claim verb take the accent. Show numbers as
  digits.
- Place captions centred, between y 1150 and 1450 (below the chin, above the
  platform UI), never over the mouth or eyes. Layout is stable within a card;
  words don't reflow as they light up.
- Keep a negation or qualifier on the same card as what it modifies: "NOT
  GROK'S FAULT," never "NOW, THAT'S NOT" | "GROK'S FAULT," (a muted viewer
  reads the second card as the opposite claim).
- When hero type says the same words, hide the caption: the hero type is the
  caption. Never make the viewer read a paraphrase headline and a verbatim
  caption at once. Hide the stretch, not just the phrases: a one- or two-word
  card left between two hidden lines (an orange "IT") reads as a glitch.
- A card never runs across a sentence end: "OPPOSITE OF THAT?" | "YOU KNOW
  IT'S", never "THAT? YOU KNOW IT'S".
- Cards appear on onset (-1 frame) and leave when the next card starts. No
  fades longer than 2 frames.
- Spell-check names and numbers by ear. Captions are the most-read text in the
  video.

## Motion

- Arrivals by material:
  - type: a masked rise from behind a baseline mask, 8-10 frames, staggered
    2-3 frames per word, easeOutCubic with 2-4% overshoot on display type;
  - stamps: slam;
  - receipts: print;
  - paper: slide and settle, 10-12 frames, easeOutBack with about 3% overshoot,
    settling 1-2 degrees of rotation.
- A hold is never dead: give it a 1-3% drift or a +/-0.3 degree paper flutter.
- Elements develop during the explanation, not just at the start: the counter
  ticks, the marker circles the thing he names, the second receipt arrives when
  he says the second number.
- Exits leave as a unit in 4-6 frames (slide, cut or tear), never word by word.
- Animate handmade elements (marker strokes, stop-motion paper) on twos (each
  drawing held for 2 frames) while the camera stays at 30 fps.
- Use different easing per material: the camera uses easeInOutQuad for drifts
  and easeOutExpo for snaps.

## Alignment (a hard requirement)

- Work on a grid of 12 columns over 1080 px with 72 px outer margins and a
  baseline unit of 8 px.
- Numbers in comparisons share a baseline and a cap height. Units and labels
  align to the number's left edge or its optical centre. Arrows are optically
  centred between the items they connect.
- Explanatory or context notes sit next to the thing they explain, joined by a
  leader line or arrow, never floating.
- Check alignment on a still with the grid overlaid before rendering motion.

## Image prompts (when generating)

Ask for material and light, not objects:
"thermal receipt paper strip, crumpled, on a dark worn wooden desk, single hard
desk lamp from the left, deep shadow, visible paper fibres, 35mm black and
white film photograph, Tri-X grain, high contrast". Plan every asset from the
beat sheet first. Generate four per sheet (quadrants) composed for clean
crops, then print-treat them in code.
