# Sound

Sound is half of why an edit feels professional. The previous cuts used
locally synthesised taps at -17.8 LUFS; the target is a designed track.

## Voice

Use `scripts/voice_chain.sh IN OUT.wav [-14]`. The chain is:
1. highpass at 80 Hz;
2. FFT denoise;
3. de-ess;
4. EQ: -3 dB at 250 Hz for mud and box, +2.5 dB at 4 kHz for presence, +2 dB
   shelf at 11 kHz for air;
5. 3:1 compression;
6. two-pass loudnorm.

Listen before and after. If the room pumps between words, lower the denoise or
the compression.

The chain compensates its own filter latency (afftdn 25 ms, alimiter 5 ms), so
the voice stays frame-locked to picture. If you add a filter, re-check sync by
cross-correlating the output against the unprocessed edit; it should be ~0 ms.

## Room tone

Take 2-3 s from the quietest real pause, or ask Adem to record 5 s of silence
first. Loop it under the whole edit so jump cuts never drop to digital silence.

## SFX vocabulary

Tie each sound to a visual event at frame accuracy:

| Event | Sound | Placement |
|---|---|---|
| whip, transition | whoosh | starts 3-4 frames early, peaks on the cut |
| paper slide, settle, tear, tape | paper foley | on the motion |
| RECEIPT | thermal printer | under the print |
| STAMP | thud plus a short room reverb | on the slam frame |
| MARKER | soft marker squeak | under the stroke |
| hero number, hook payoff | low sub hit | on the arrival |
| reveal | 0.5-1 s riser | into it |
| comedic stop | record scratch, or true silence | on the stop |
| freeze frame, polaroid | shutter | on the freeze |

Keep SFX peaks 6-10 dB under speech peaks; impacts may touch speech level for
a frame or two. Never bury a key word under a sound unless the sound is the
emphasis. Density is about one every 3-6 s, with clean stretches between.
Reuse owned SFX first; use ElevenLabs sound effects for custom ones after
checking credits and scope.

## Music (optional)

Keep a bed at about -30 LUFS short-term under speech, ducked 6-8 dB while he
talks. Drop it out completely for the key line. Cut section changes on
downbeats.

## Delivery

Normalise the final mix, not only the voice: run `voice_chain.sh` without the
EQ, or a plain two-pass loudnorm, on the mix. Targets: -14 +/-1 LUFS
integrated, true peak -1 dBTP or lower, LRA 8 or less.
