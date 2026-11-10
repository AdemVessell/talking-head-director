# Notices

This file records what is in the candidate and what is not decided.
It is not a license grant. It is not legal advice.

## Engine source

No license has been chosen for the talking-head director source
(scripts, docs written for this package, examples of plans the engine writes).
The copyright holder has not approved MIT, Apache, GPL, or any other grant.
Until they do, recipients have no license from this candidate to copy,
modify, or ship the source. Shipping this archive inside a private review
repository does not change that.

`NOTES.md` still says "Licence and author name" are open. That remains open.

## Fonts

Bundled, unmodified, with the license file named in `assets/fonts/README.md`.
SHA256 of each file matches that README (checked while building this candidate).
Upstream stated there: google/fonts commit `5bb28733cec313b63fbd415b574b5ae35c8aa8b8`.
The two Libre Baskerville files are renamed from the variable-font filenames,
as that README says.

| File | License file | Reserved font names in the license |
|---|---|---|
| AbrilFatface-Regular.ttf | OFL | "Abril", "Abril Fatface" |
| Anton-Regular.ttf | OFL | none named in the copyright line |
| BarlowCondensed-Bold.ttf, ExtraBold | OFL | none named in the copyright line |
| CourierPrime-Bold.ttf | OFL | none named in the copyright line |
| FrederickatheGreat-Regular.ttf | OFL | "Fredericka the Great" |
| GFSDidot-Regular.ttf | OFL | GFS Didot |
| IBMPlexMono-Regular.ttf, Bold | OFL | "Plex" |
| LibreBaskerville variable files | OFL | Libre Baskerville |
| PatrickHand-Regular.ttf | OFL | none named in the copyright line |
| PermanentMarker-Regular.ttf | Apache-2.0 | copyright in the font name table: Font Diner, Inc., 2010. Sidecar: `licenses/permanentmarker-COPYRIGHT.txt`. The Apache file itself is the standard text with an unfilled "Copyright [yyyy]" appendix. |
| SpecialElite-Regular.ttf | Apache-2.0 | copyright in the font name table: Brian J. Bonislawsky DBA Astigmatic (AOETI), 2010. Sidecar: `licenses/specialelite-COPYRIGHT.txt`. Same unfilled appendix in the Apache text. |
| ZillaSlab-Bold.ttf | OFL | none named in the copyright line |

OFL 1.1 allows bundling these files with the license text. It does not allow
selling a font by itself, and it reserves the names above: a modified font
cannot use a reserved name. These files were not modified, except the two
Libre Baskerville renames already disclosed. They are not the macOS faces the
look was designed on (Didot, Futura, Avenir, Georgia, Menlo, Marker Felt, and
the others). Those Apple faces are not in this archive and are not licensed
for redistribution here.

## Sound

Apple Final Cut Pro sound effects are not included. The filenames the kit
looks for are in `scripts/thd_engine/sound.py`. If a file is absent, the engine
synthesises a stand-in. Nobody has signed off on those stand-ins by ear
(`NOTES.md`). Paper foley is synthesised in code. Do not add a paid sound API.

## Whisper weights

Not bundled. First prep downloads OpenAI Whisper `medium.en` through the
`openai-whisper` package. That is a network fetch of model weights, not a call
to a paid API. Confirm the weight license from the upstream Whisper project
before a public release. This candidate does not restate that license from memory.

## Python packages

Pins are in `requirements.txt`. Declared metadata from the clean Linux
environment (Python 3.12, the installer above). This is the `License` field
and license classifiers, not a copy of each full license:

| Package | Version seen | Declared license |
|---|---|---|
| numpy | 2.0.2 | BSD (classifier). The long license text also names lapack-lite as BSD-3-Clause and libquadmath as LGPL-2.1-or-later. |
| opencv-contrib-python | 4.13.0.92 | Apache 2.0 |
| Pillow | 11.3.0 | MIT-CMU |
| soundfile | 0.13.1 | BSD-3-Clause |
| PyYAML | 6.0.3 | MIT |
| stable-ts | 2.19.1 | MIT |
| openai-whisper | 20250625 | MIT |
| torch | 2.8.0+cpu | BSD-3-Clause |
| torchaudio | 2.8.0+cpu | BSD classifier; the License field itself was empty |

`mediapipe` is commented out and not installed. `stable-ts` depends on
`torchaudio` with no upper bound. The Linux installer pins `torchaudio==2.8.0`
from the CPU wheel index so the resolve cannot replace `torch==2.8.0+cpu`
with a newer CUDA build. That pin is part of the install procedure, not a
new grant. The full license texts stay in the wheels. They are not copied
into this archive.

opencv-contrib-python is a separate distribution from opencv-python. Read its
own license file. Some contrib algorithms have patent histories. This candidate
does not clear those.

## FFmpeg

Used as an external program on PATH. It is not bundled. The build on the clean
machine was the Ubuntu package, configured `--enable-gpl`. Linking or shipping
ffmpeg binaries is a separate decision. This candidate does not ship ffmpeg.

## espeak-ng

Used only to speak the selftest lines when macOS `say` is absent. Not bundled.
GPL software, invoked as a program. The selftest voice is synthetic. It is not
a recording of a person, and it is not sped up or mirrored from one.

## Test media that was left out

`_test_outputs/sheet_real.jpg` shows a real presenter. It is not in this
archive. The other contact sheets and the two test MP4s were also left out.
`thd selftest` builds its own synthetic clip.

## Style frames from the private development tree

Not part of the public port and not added here. They contain a real person's
face from a presenter plate.
