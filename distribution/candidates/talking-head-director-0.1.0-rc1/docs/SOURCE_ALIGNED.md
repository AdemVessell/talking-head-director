# Source-aligned workflow

`thd auto` drafts a vertical edit from one recording. Some cuts are not that
draft. They are a story cut written against the source clock: named segments,
exact words, evidence audio taken from the source without a separate gain per
passage, then a picture built from those times.

That path lives in `scripts/aligned/` and is exercised by
`examples/source-aligned/`. Read that README before treating `thd auto` as the
whole method.

The example is synthetic. It does not show how a real recording will look or
sound. A waveform comparison is only as honest as the two windows of the same
file. A diagram in this path is an illustration and says so. A colour tracker
follows a mark in the picture; it does not know what the mark is.

Preview is a gate. Full render checks `work/PREVIEW_APPROVED` against the
segment list. Watching the preview is a person's job. The synthetic test
approves only after it has checked that a preview file exists, and it says so.

Worker default for the engine and for this renderer is 3. A default of 8 has
run out of memory on a small machine.

`bash scripts/thd` is the invocation when the executable bit is missing.
The bit is set in this candidate. Either form runs the same file.

Selftest speech is a stand-in voice. If `espeak-ng` on the machine is a shell
script that calls ffmpeg's flite voice, doctor says so. That stand-in is not
espeak-ng and it is not a production voice.
