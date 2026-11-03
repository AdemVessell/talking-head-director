# Shot grammar for one fixed camera

One static webcam has to feel directed. With one angle, variety comes from
shot SIZE, the WINDOW the camera sits in, POSITION, MOVEMENT, and what REPLACES
the face. Decide these per line, from the beat sheet, never per layout.

## Contents
Size ladder · Windows · Cutting between sizes · Moves inside a shot ·
Cutaways · Persona beats · Composition and safe zones · Source constraints

## The size ladder

Measure size as face width / output width (`face_track.py` gives the face
width; `Track.crop(zoom=...)` keeps the eye line fixed across sizes, so cuts
between sizes feel like one operator's choices; pass `face_frac` straight from this
table, e.g. `Track.crop(t, face_frac=0.67, aspect=4/5)`). Each step is about 1.35x, the
classic punch ratio.

| Code | Name | Face width | Use |
|---|---|---|---|
| W | wide band | ~35% | setup, context, room for a graphic beside or below |
| H | home | ~50% | the default talking shot (Adem's approved "wider framing") |
| C | close | ~67% | a claim, a number, a question to the viewer, emotion |
| X | extreme | ~95% | punchline, outrage, the one line that matters; 1-2 s |
| XX | gag | >120% (eyes or mouth) | comedy only, under 1 s, at most twice a video |

For the current Mac recordings (1620x1080 landscape, face ~575 px wide):
W = whole source frame in a 1080x720 band; H = ~1180x1080 crop in a
~1080x990 window; C = 864x1080 crop in a 4:5 1080x1350 window; X = 607x1080
crop, full-bleed 9:16 (1.78x upscale); XX = ~480x850 crop (2.25x, soft, needs
grain). Grade before upscaling (see analog-look.md).

## Windows, not slots

When the source cannot give a medium shot full-bleed, the camera becomes a
window on a designed stage. The window's size, aspect, position, tilt and edge
(clean, torn paper, print border, tape) are part of the shot, and they change.

- Full-bleed 9:16: X, or C/H when a future source allows it.
- 4:5 window with type room above and captions below: C.
- ~1:1 window: H, the resting shot.
- Full-width band with a graphic panel: W. This is the old split; it is one
  shot type among many, never the house layout.
- Print or polaroid window, 40-55% width, 1-3 degrees tilt, tape, over a
  full-screen graphic: "presenter as evidence".
- Corner window, 25-30% width: picture-in-picture while a graphic needs the
  stage but his reaction still matters.

Change the window at least every ~3 lines. Animate between states (8-12
frames, ease-out with a small overshoot) or hard-cut on a word; use both.

## Cutting between sizes

- Every jump cut (removed words or pause) changes size or window, or is covered
  by a cutaway. A same-size jump cut reads as a glitch.
- Cut 2-3 frames before the stressed syllable you are emphasising, so the eye
  lands as the word does.
- Punch in on claims, numbers, turns, questions and jokes; pull back out for
  explanation. Rhythm, not randomness: H C H W H X H is a sentence; C X C X is
  shouting.
- Return to the face after a cutaway on the interpretation line ("...and that's
  the problem"). The return is itself a beat.

## Moves inside a shot (living holds)

- Drift: any hold over ~1.5 s gets a slow push (1.00 to 1.04) or pull; alternate.
- Snap zoom: 5-7 frames, about 1.25x, with motion blur (4-6 subframes), for
  punchlines; at most ~3 a minute.
- Impact shake: 6-8 frames, 6-10 px decaying, +/-0.3 degrees, on stamps and
  number slams. Shake the camera group, never the captions.
- Whip between sections: 6-8 frames, heavy directional blur, whoosh starting
  3 frames early.
- Render the camera 6-8% oversize so moves never reveal an edge.

## Cutaways (the face is replaced)

When the subject of a sentence is a thing (product, number, document, place,
screen), show the thing full-frame while his voice continues, 1.2-3.5 s.
Moving, not still: a slow push into a screenshot, a counter running, a receipt
printing, hands doing the thing. Roughly one line in three to five is a
cutaway in an explainer; never more than ~6 s away from his face at a time.

## Persona beats (no matting required)

- Freeze-frame verdict: freeze 12-20 frames, xerox treatment, marker arrow and
  a hand-lettered label ("me, $5 poorer"), shutter SFX.
- Alter-ego line: hard cut to X with a different grade (photocopy mono or deep
  red), a pitch-shifted line, a label, then straight back.
- Faux documentary: letterbox bars slide in, cooler grade, a lower-third
  caption, for mock-serious beats.
- Scale gag: shrink his window to a tiny polaroid on a line that diminishes him.
- Degradation: run an image through repeated photocopy generations while a
  number drains.
Full-body cutouts and relights only when a test shot passes at normal speed
on difficult edges (hair, cap brim, beard, shoulders). Otherwise use the above.

## Composition and safe zones

- Eyes on the upper-third line of the window (0.33-0.38 of its height). In
  close sizes the cap may touch the window top; never leave a gap above the head.
- Keep the face and all text inside the central 4:5 zone (y 285-1635 of 1920)
  where possible; captions and key text between y 240 and 1500; nothing
  important in the right 140 px between y 900 and 1700 (platform buttons).
- Never mirror the picture (he dislikes it) unless a gag needs a fake reverse
  angle; then flag it.

## Source constraints and recording advice

The current webcam framing (face ~35% of a landscape frame) makes any
full-bleed vertical crop an extreme close-up, which is why windows are needed.
Its noise reduction also makes skin waxy and soft. If Adem asks how to record
better, offer, briefly: sit back so the face is ~20-25% of frame width; record
4K if possible (an iPhone through Continuity Camera); one soft key light from
the side, background darker than the face; record 5 s of silent room tone
first. Better source footage beats any finish.
