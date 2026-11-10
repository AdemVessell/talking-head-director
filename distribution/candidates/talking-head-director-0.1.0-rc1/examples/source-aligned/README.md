# Source-aligned edit

Cut one video by a segment list. The story is the order of `segments`.
This is not `thd auto`. The only example in this folder is `talk/`: two
spoken lines, played in the opposite order from the source, with captions
and the preview gate. It has no waveform, no colour track, no diagram, and
no label cards.

## Required input

`plan.yaml` next to the files it names:

- `source`: the video to cut.
- `words`: a JSON list of `{w, s, e}` in source seconds. This CLI does not
  run speech recognition.
- `segments`: the story, in edit order. Each has `id`, `src_in`, `src_out`.
  `room: true` holds the previous picture and uses that span as room tone.
- `preview_segments`: the ids rendered by `preview`. `full` will not run
  until `approve` has been run for this segment list.

Optional, and omitted means absent:

- `waveform`: two or more windows of the same source audio, drawn at one
  scale. Fewer than two windows draws nothing.
- `track`: a colour centroid and a ring. No `track` key means no scan.
- `diagram`: a labelled illustration, drawn only when `diagram.cues` is set.
  The card says it is not to scale. Title, subtitle, and row labels come
  from the plan.
- `card` and `sub` on a segment: a paper label instead of captions.
- `limiter`: one gain, then a true-peak limiter only after a named source time.
- `gain_db`, `tail`, `tail_room_src`.

The compositor always draws a workshop mat, one print of the current frame,
and tape. It does not find a face or apply the styles from `thd styles`.

## Run

```bash
python3 examples/source-aligned/talk/make_fixture.py
python3 scripts/aligned/render.py examples/source-aligned/talk/plan.yaml preview 3
python3 scripts/aligned/render.py examples/source-aligned/talk/plan.yaml approve
python3 scripts/aligned/render.py examples/source-aligned/talk/plan.yaml full 3
```

Workers default to 3. If `scripts/thd` is not executable, run `bash scripts/thd`.

A shell script named espeak-ng that calls ffmpeg flite is not espeak-ng.
The fixture refuses that stand-in. The spoken lines are synthetic. The
picture is not a face, and the render is not proof of a real edit.
