# Linux CPU install

This is an isolated install. It does not need the author's computer, private
repositories, or private Drive, and it does not install into the system Python.

Proven in one clean environment on this candidate (see the private repo's
evidence log). That run is not a claim that every recipient machine will
succeed. `scripts/thd doctor` is the check on the machine you are actually on.

## System packages

Debian or Ubuntu names:

- `ffmpeg` (must include `ffprobe`, `libx264`, `prores_ks`, `aac`, `drawtext`)
- `python3` and `python3-venv` (3.9 or newer; 3.12 was used in the clean run)
- `libsndfile1` (the `soundfile` package loads it)
- `espeak-ng` (only for `thd selftest`'s synthetic voice)

macOS can keep using its own Python and `say`. The open fonts in `assets/fonts`
are what this candidate draws with. System fonts are a fallback, not a requirement.

## Virtualenv

From this directory:

```bash
bash scripts/install-linux-cpu.sh
export THD_PYTHON="$PWD/.venv/bin/python"
scripts/thd doctor
```

`install-linux-cpu.sh` installs `torch==2.8.0` and `torchaudio==2.8.0` from
`https://download.pytorch.org/whl/cpu`, then the other pins under a constraint
of `torch==2.8.0+cpu` and `torchaudio==2.8.0+cpu`. `stable-ts` depends on both
with no upper bound. On 2026-11-10 a resolve without that constraint replaced
the CPU wheel with `torch 2.15.0+cu132`. The script stops if the installed
torch version does not start with `2.8.0`.

The first `prep`, `autocut`, or `selftest` downloads the Whisper `medium.en`
weights (about 1.5 GB) into the Whisper cache. That download is the model
weights, not a paid API.

## What doctor is telling you

- FAIL means an edit cannot finish on this machine.
- WARN on the Whisper line means the weights are not cached yet. The first run
  needs a network.
- The sound line counts library files and synthesised stand-ins. Synthesised
  cues are how this package ships. They have not been approved by ear.
- PASS on this agent's machine is evidence about that machine only.

## Self-test

```bash
THD_PYTHON="$PWD/.venv/bin/python" scripts/thd selftest --jobs 2
```

The voice is `espeak-ng` at 150 words per minute, with 0.65 s pauses, over an
ffmpeg test pattern. It is not a sped-up or mirrored recording of a person.
Expect several minutes on a small CPU, longer while the Whisper weights download.
