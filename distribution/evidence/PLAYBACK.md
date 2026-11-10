# Playback review of the final candidates

This file records what was actually watched and measured. It is not a
human listening session, and it is not a recipient install.

## Talking-head selftest

File: the render from `thd selftest --jobs 2` after the sticky headline
change (80 to 96). Duration 9.53 s, 1080x1920, AAC 48 kHz mono.

A video model watched a full-length lower-bitrate copy (the 23 MB master is
over that model's 15 MB attachment limit). It read the sticky as "SELF TEST"
and read the captions through "WHOLE IDEA.", including "FIRST," and
"WRITE THE TITLE". It reported a cut to black at the end. That black frame
is the planned end burn, not a dropped picture. An earlier pass of the same
model missed "First, write" in the captions; the SRT contains those words
from 2.950 s to 3.747 s, and the later pass read them.

Feed-size check after the change: title 20 px on the studio plan and 16 px
on the news plan, both at 390 px wide. Before the change the news title was
13.51 px and the check warned.

Loudness, measured with ffmpeg ebur128, not by ear: integrated about -15.5
to -15.7 LUFS, true peak -1.4 dBTP. The audit warns because the band is
-14 ±1. The mix was not retuned.

Sound effects, measured, not heard: `sfx.wav` is 9.53 s, RMS about -35.4 dBFS,
peak about -4.1 dBFS, about 30 onsets above 0.05. The voice is about -17 dBFS
RMS. One video-model pass said it heard only the robotic voice and no
effects. A later pass said it could not hear audio at all. Those reports
disagree, so the synthesizer was left as it is. A person still has to listen.

This clip is a test pattern and espeak-ng. It does not show how a real
recording, a real face, or a real room will cut.

Whisper `medium.en` downloaded 1.42 GB on the first run.

## Viz Draft master

File: the original 4.0 s Draft render, 540x676, before any camera experiment.
QA with a clean library path: PASS, -14.6 LUFS, true peak -1.9 dBTP, decode
clean. A tmux library-path warning on ffmpeg's stderr can make `qa/check.mjs`
report a decode error; that was the environment, not the file.

A video model watched the whole 4 seconds. It read "Three shapes." and
"ONE ROW". It reported the camera passing through the paper cards between
about 0.5 s and 1.75 s. A later camera nudge was rendered and watched; the
model still reported the cards intersecting the camera. The nudge was
reverted. The archive keeps the original camera. The model could not hear
the synthesised bed. ffmpeg measured the loudness above.

## What this does not clear

Publishing still waits on a person watching both files with sound, and on
the empty repository `AdemVessell/bot-video-engines`. The intended tag is
`rc1`. `PUBLISHED` is `no`.
