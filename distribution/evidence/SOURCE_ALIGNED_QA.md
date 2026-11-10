# Source-aligned synthetic QA

The example is `examples/source-aligned/talk/`. Speech only. No waveform,
no colour track, no diagram, no label cards. Not a real recording.

Gate: `full` before `approve` printed "preview gate: full render is blocked
until this cut is approved." and exited 1.

Preview: 40 frames, 1.668 s, 13.1 s to render, 3 workers.
Approve printed `approved a7d114aa56b7`.
Full: 83 frames, 3.462 s, 20.8 s to render, 3 workers.

Captions in `full.srt`, in story order. The later source line is first:

```
Start with this.
Detail comes next.
```

Those are the fixture's own words. Frames at the start, the middle, and the
end show the workshop mat, one print, tape, and that caption. The active
word is vermilion. No waveform, ring, diagram, or second card is in the frame.

`thd` in this candidate is executable. If a copy loses that bit, use
`bash scripts/thd`. Engine and this renderer default to 3 workers.

This machine's `espeak-ng` is the real 1.51 binary. A shell script that calls
ffmpeg flite is not espeak-ng. Doctor warns on that stand-in. The fixture
refuses it. The spoken lines are synthetic. The picture is not a face.

This run does not prove a real-face edit. Sound on this talk render was not
listened to here.

Viz archive was not rebuilt. Its hash remains
`8751468f201fb96738de47818060783170aac14bfd6f66a3eb37eae81c4468ba`.
