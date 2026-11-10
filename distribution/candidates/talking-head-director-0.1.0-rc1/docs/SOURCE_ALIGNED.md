# Source-aligned workflow

`scripts/aligned/render.py` cuts one source video by a segment list.
The list can be any spans of that file, in any order. Nothing in the
command requires a comparison, a diagram, or a tracked mark.

## Supported

- Any segment list. Edit order is the story. Source order is not.
- Captions from a words file mapped through those segments. Words outside a
  segment are dropped. Words are not invented here.
- A preview of the named preview segments, then `approve`, then `full`.
  `full` exits if the approval file is missing or the segment list changed.
- One gain for the whole soundtrack. A limiter runs only when the plan names
  the source time it may start.
- Optional waveform comparison, optional colour tracking, optional diagram.
  Each is absent unless its key is in the plan. A diagram's words come from
  the plan, and the card says it is not to scale.
- Workshop mat, paper, and tape from the engine. Worker default is 3.

## Not supported

- Speech recognition. Bring `{w, s, e}` times. `thd auto` is the other path,
  and it expects a presenter and a brief.
- A face, a shot ladder, or the house styles. A frame with no face is valid.
- A claim that a synthetic run shows a real recording.
- Treating a waveform, a colour blob, or a diagram as a measurement.
  A waveform is drawn only for two or more windows of the same file.
- The author's recordings or a particular product test.

`examples/source-aligned/talk/` is the example: speech, reordered, captions,
preview gate, and none of the optional overlays.

`bash scripts/thd` is the launcher when the executable bit is missing.
If `espeak-ng` is a shell script that calls ffmpeg flite, doctor says it is
a selftest stand-in, not espeak-ng. The fixture refuses to use that stand-in.
