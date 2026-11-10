# Source-aligned synthetic QA

Not a real recording. Not a substitute for watching one.

Gate: `full` before `approve` exited with "preview gate: full render is blocked".
Preview then ran (52 frames, 2.17 s, 3 workers) and was approved.
Full then ran (129 frames, 5.38 s, 3 workers).

Captions in `full.srt`, in story order after the two evidence passages:

```
This is a synthetic
check.
```

Those are the fixture's own words, not a person's.

Same-source waveform peaks from the extracted audio: louder passage 0.358,
quieter passage 0.132, ratio 2.71. The card uses one amplitude scale for both.

A preview frame shows the cutting mat, the "LOUDER PASSAGE" card, the
same-scale waveform label, and a ring on the red mark.
A full frame shows the diagram labelled "simplified illustration · not to scale"
and the caption "THIS IS A SYNTHETIC" clear of the card.

`thd` in this candidate is executable. If a copy loses that bit, use
`bash scripts/thd`. Engine and this renderer default to 3 workers.

This machine's `espeak-ng` is the real 1.51 binary. A shell script that calls
ffmpeg flite is not espeak-ng. Doctor warns on that stand-in. The fixture
refuses it. The spoken line is synthetic.

Viz archive was not rebuilt. Its hash remains
`8751468f201fb96738de47818060783170aac14bfd6f66a3eb37eae81c4468ba`.
