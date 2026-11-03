# The analog / weathered-editorial look

Adem's words: "more detail, more analogue and spice"; "weathered, analog,
retro-future, real"; and earlier "plain CGI" as the failure. Below, those words
are turned into specific layers.

## What "detail" means

Detail does not mean more objects. It means texture at three scales on every
surface, plus believable light:
- **Macro:** layering. Paper on paper, a photo on paper, tape and clips, and
  shadows from one consistent light (top-left, soft, 8-14 px offset, 25-35%).
- **Meso:** material. Paper fibres, halftone dots, ink spread, toner speckle,
  creases, a torn edge with fibres.
- **Micro:** film grain over everything.

The webcam's noise reduction makes skin waxy. Fine grain restores perceived
detail there. A flat cream rectangle is the opposite of detail.

## Layer order per frame

1. **Camera:** `look.grade_webcam(crop, face)`. It corrects tungsten, relights
   the face (+0.25 stop on the face, -0.5 stop on the room), applies an S-curve
   with a highlight shoulder and saturation 0.92, and sharpens lightly. Grade
   before any upscale, at source resolution. Pass the face from
   `Track.at(t)` in the coordinates of the image you grade.
2. **Stage and graphics:** real paper scans or generated textures first,
   `look.paper()` as the fallback. Print-treat photos and cutouts
   (`halftone` with a 6-9 px cell at output size, `xerox`, `misregister` by
   1-2 px). Physical layers cast shadows from the one light.
3. **Finish over the whole composed frame:**
   `look.Finish(W, H, preset).apply(frame, frame_index)`. It adds halation,
   bloom, gate weave, radial chromatic aberration, vignette and
   luminance-weighted grain. "medium" is the default. Before changing strength,
   show Adem subtle, medium and heavy on a real frame side by side; don't
   guess. Heavy reads as noise on close face shots.

On this Mac the finish takes ~0.1 s per 1080x1920 frame and the grade ~0.1 s per
1620x1080 frame, so a 4-minute piece adds ~25 min of CPU: grade once into a
prepared source, proof on short ranges, and build one
`Finish` per render and reuse it, because its grain bank is precomputed.

## Stages and palette

- Two stage materials, alternated by section rather than mixed in one frame:
  - **Ivory journal:** paper #E9E1D3, ink #15120F, for explanation.
  - **Charcoal evidence board:** #22201D with paper elements pinned on it, for
    tests, receipts and verdicts. It also makes the face pop.
- Accent vermilion #E2452B. Highlighter #F2D43D only for marker highlights.
- Footage stays natural: skin is the one thing never stylised hard. Only
  persona beats break this, on purpose.

## Spice (one or two per video)

- A light leak or flash frame (2-4 frames of warm overexposure) at a section
  change.
- A scanner-bar wipe: a bright line sweeps across and reveals the next shot.
- Photocopy generation loss on a repeated image to show something degrading,
  such as credits burning.
- Film burn to black on the final beat, instead of a fade.
- A frame stutter (hold 2-3 frames, then jump) on a comedic stop.
- Stop-motion paper on twos for collage sequences.

## Avoid (seen in earlier cuts)

- A permanent decorative header, footer or frame on every shot.
- Flat, untextured panels; 1-2 px hairlines; labels under 28 px.
- Generated objects centred on seamless white (the "product shot" look); bronze
  machinery; props that don't explain anything.
- Thresholded noise used as texture (it reads as camouflage blotches); grain
  that lifts the blacks; distress that covers type or numbers.
