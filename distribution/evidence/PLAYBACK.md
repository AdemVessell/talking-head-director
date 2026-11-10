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

The original camera keys are unchanged. The paper cards were the problem:
their bottoms went through the stage, the nearest centers sat off the stage
disc, and they filled the foreground so the frame cut them. A sampled path
of that original layout kept the camera origin 1.43 from the nearest card
and the nearest corner 3.44 in front of the near plane (0.02), so the lens
was not inside those boxes. The picture still read as a cut through paper.

The cards now stand on the stage in a receding row to the right of the three
shapes (`src/stageLayout.ts`). `qa/camera-clearance.mjs` on the final layout:
minimum distance from the camera and its near plane to a card 2.385, minimum
corner depth 2.367, no card below the stage or off the disc, at least 6 cards
inside the frame during the travel, and a 0.103 gap from the hero shapes.
Required clearance is 0.5.

The new Draft is 4.0 s, 540x676. QA PASS, -14.6 LUFS, true peak -1.9 dBTP.
Stills at 1.0 s and 1.5 s show the row standing on the stage beside the
cylinder, not sliced open. The parent still needs to watch this file. I did
not hear it.

## What this does not clear

Publishing still waits on a person watching both files with sound, and on
the empty repository `AdemVessell/bot-video-engines`. The intended tag is
`rc1`. `PUBLISHED` is `no`.
