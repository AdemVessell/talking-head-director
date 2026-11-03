# Renderer upgrades this style needs

The current Python/PIL/FFmpeg frame renderer is a good base: full control and
deterministic output. The problem is structure, not FFmpeg. It picks a fixed
composition per time range, crops the presenter at a fixed centre, switches
captions phrase by phrase, and edits graphics on a timeline the dialogue edit
never touched. Add the following inside the project. The scripts in this skill
provide the pieces.

## 1. Words drive everything

beat sheet -> EDL (keep-segments) -> edit-time words -> cues.

- Generate the EDL from the beat sheet (source in/out per kept phrase, with the
  tightening rules) and render the dialogue from it, including crossfades and
  the room-tone bed.
- Map every source word into edit time. Cues reference words, for example
  `{"at": "word:153", "offset_f": -2}` or `{"at": "beat:7.start"}`, never typed
  seconds, so re-cutting moves every graphic with its words.
- Reconcile ASR words with the corrected transcript (display forms such as
  "$40", names, zero-length words). `caption_cards.load_words` and
  `attach_punct` do a heuristic version.

## 2. Camera state per shot

Each beat has a shot spec: size code (W/H/C/X/XX) or an explicit zoom, window
rect, aspect, eye line, x offset, drift (start and end zoom), and a transition
in. Evaluate it per frame:

    x, y, w, h = track.crop(t_src, zoom=z(t), aspect=win_aspect, eye_line=0.36, x_offset=o(t))
    cam = grade_webcam(src[y:y+h, x:x+w], face=track.at(t_src) - (x, y, 0))   # grade at source res
    cam = cv2.resize(cam, window_size, interpolation=cv2.INTER_LANCZOS4)

The track is in source time, so use the frame's source timestamp after the EDL
mapping. Crop about 7% wider than the window for overscan, so shakes and whips
never show an edge.

## 3. Layers, transforms, keyframes

Each element is an RGBA layer with keyframed position, scale, rotation,
opacity, mask and crop, and each property has its own easing. Elements belong
to groups (camera, stage, graphics, captions, finish-exempt overlays) that
transform independently. Shake the camera group, never the captions.

Keep easing functions in one module: easeOutCubic, easeOutBack(s=1.3),
easeOutExpo, easeInOutQuad, and a "twos" wrapper that quantises time to 2-frame
steps for hand-drawn elements.

Masks:
- type rises from behind a baseline clip rect;
- marker strokes draw on via path length;
- receipts print by revealing a crop height;
- ink bleeds use a growing blurred blob as alpha.

## 4. Motion blur and timing

- When a group's velocity exceeds about 25 px/frame (whips, snaps, slams),
  render 4-6 subframes at fractional times and average them. Do this only for
  the moving group, because it is expensive.
- Compute easing in frames from the cue's frame, not in seconds, so on-twos
  and 2-3 frame slams are exact.

## 5. Captions

Use `caption_cards.build_cards` and `CardRenderer`. The layout is computed
once per card and words light up in place, so lines never reflow. The caption
group sits outside the camera shake. Captions are hidden while hero type says
the same words (a cue flag).

## 6. Composition order per frame

1. stage
2. camera window with its shadow
3. graphics
4. captions
5. `Finish.apply()` over the whole frame
6. overlays that must stay clean, if any

## 7. Proof workflow

Every render takes `--from/--to` (seconds or beat ids) and a `--proof` flag:
half resolution and no subframe blur for timing checks, full quality for look
checks. Write a JSON receipt (inputs, versions, cues, durations) next to every
render, as the project already does.
