# Clean-environment evidence

This is one Linux machine (Ubuntu, Python 3.12.3, 4 cores, ffmpeg 6.1.1).
It is not a recipient install. Passing here does not mean another machine will.

## Talking-head director 0.1.0-rc1

Install: `scripts/install-linux-cpu.sh` into a fresh virtualenv.
Result: `torch 2.8.0+cpu`, `cuda_available=False`. A first attempt without the
CPU constraint installed `torch 2.15.0+cu132` and the script rejected it.
Log: `linux-cpu-install.txt`.

Doctor before the Whisper download: 16 pass, 1 warn, 0 fail.
The warn is `medium.en` not cached yet. Log: `linux-cpu-doctor.txt`.
Fonts: 21 of 21 roles resolved to the bundled open files.
Sound: 0 library files, 13 synthesised. Nobody has approved those by ear.

Selftest: PASS in 154 seconds, `--jobs 2`, espeak-ng voice, Whisper `medium.en`.
1080x1920 @ 30 fps, length 9.53 s matching the EDL, AAC, sync +0.00 ms,
ASR matched the plan text. Log: `linux-cpu-selftest.txt`.
The news pre-post check had 0 failures and 1 warning: title text 14 px at
feed width. That warning is the one already written in the port's `NOTES.md`.
The harness treats warnings as non-failing. It is still a warning.

Frames looked at from the synthetic render (test pattern, not a person):
`selftest-1.2s.jpg` (sticky "SELF TEST", caption "TEST OF THE"),
`selftest-4.2s.jpg` (index card "1 write the title"),
`news-sheet.jpg` (synthetic page labelled not a real publication).
The 9.5 s file was not watched through with sound in a player. The selftest
measured an audio track and 0 ms sync. That is not the same as listening.

The first selftest attempt failed before this pass: PyYAML could not dump
`np.float64` segment times. `autocut` now stores plain floats. That fix is
in the candidate, not in the older private `scripts/` tree.

## VizExplainer starter

From the original files, in `/tmp`, not from a published URL:

- `npm ci` from the lockfile
- `npm run typecheck` passed
- `npm run still` wrote a 540x676 PNG (frame 45 is the caption boundary, so
  the caption opacity is 0 there)
- frame 20 shows "Three shapes."; frame 90 shows "ONE ROW"
- `npm run render` wrote `Draft-master.mp4` (4.0 s, 120 frames, H.264 High,
  yuv420p, AAC)
- `qa/check.mjs` PASS: 30 fps, 540x676, -14.6 LUFS, true peak -1.9 dBTP,
  decode clean
- `qa/font-test.sh` PASS: hiding IBM Plex Mono cancels the render

Log: `viz-linux.txt`. Remotion's headless shell was downloaded once during
the still. That download is not bundled in the archive.
