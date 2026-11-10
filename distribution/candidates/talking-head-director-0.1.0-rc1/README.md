# Talking-head edit engine (public port, work in progress)

One command turns a raw talking-head recording into a finished vertical short: fillers and dead
air cut, shot changes, word-timed captions, papers that write themselves on the speaker's own
words, designed sound, then a loudness, sync and pre-posting check.

    scripts/thd doctor                      check this machine
    scripts/thd selftest                    the whole pipeline on a synthetic clip
    scripts/thd styles                      the looks
    scripts/thd auto RECORDING              hands-free edit -> RECORDING_edit/deliver/
    scripts/thd auto RECORDING --draft      list the lines, to write a brief from
    scripts/thd auto RECORDING --brief brief.yaml

`thd auto --help` and `scripts/thd_engine/auto.py` describe the brief. The tool never posts.

Needs Python 3.9+, the packages in requirements.txt, and ffmpeg. Runs on macOS and Linux, CPU only.
Linux install is isolated: `docs/INSTALL-linux-cpu.md` and `scripts/install-linux-cpu.sh`.
The edit itself: `docs/WORKFLOW.md`. Rights and third-party notices: `NOTICES.md`.

Status: distribution candidate 0.1.0-rc1, not a release. See NOTES.md and DISTRIBUTION.txt.
Owner-written code is MIT, copyright Adem Vessell (LICENSE). Third-party terms stay in NOTICES.md.
The intended download, once the public repository exists, is recorded in DISTRIBUTION.txt.
That URL is not live yet.
