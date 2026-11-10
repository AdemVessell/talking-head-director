---
name: talking-head-director-getting-started
description: Install the talking-head edit engine from its versioned archive into an isolated directory, then run doctor. The intended GitHub release is not live yet. Do not fetch it.
---

# Getting started

The engine is not on the author's computer, and it is not in this skill.
This skill does not contain the engine's files. Fetch one versioned archive,
check its SHA256, and install that tree. Do not search a private repository,
a private Drive, or a Mac path.

## The archive is not live yet

The intended file, after `AdemVessell/bot-video-engines` exists and tag `rc1`
is published, is:

https://github.com/AdemVessell/bot-video-engines/releases/download/rc1/talking-head-director-0.1.0-rc1.tar.gz

That URL is not a working download today. Do not fetch it. The bootstrap
refuses while `PUBLISHED` is `no`. Owner-written code in the archive is MIT,
copyright Adem Vessell. Third-party terms are not MIT.

When the release exists, the archive name is
`talking-head-director-0.1.0-rc1.tar.gz` and its SHA256 must be exactly:

6f948859719f0e27cb5f010b3023cbbf28ff01eba9906cdc5bc8d9eca3f48ba2

A different hash means a different file. Do not install it. The first prep
downloads Whisper `medium.en` (about 1.5 GB). That is model weights, not a
paid API. A synthetic selftest does not prove a real recording.

## Isolated install

The bootstrap unpacks into `~/.local/share/talking-head-director/0.1.0-rc1`
(or `$THD_HOME/0.1.0-rc1`) and refuses to overwrite an existing directory.

```bash
sh thd-bootstrap.sh
```

On Linux, from the unpacked directory:

```bash
bash scripts/install-linux-cpu.sh
export THD_PYTHON="$PWD/.venv/bin/python"
scripts/thd doctor
```

That creates a virtualenv and installs the pinned packages, with torch from
the CPU wheel index. It does not use the system Python. Read
`docs/INSTALL-linux-cpu.md` in the unpacked tree. `doctor` is the check for
the machine you are on. A pass on someone else's machine is not this machine's
pass.

`scripts/thd selftest --jobs 2` runs the whole pipeline on a synthetic clip.
On Linux the voice is espeak-ng. It is not a person's recording, and it is
not sped up or mirrored. The first run downloads the Whisper `medium.en`
weights (about 1.5 GB). That is a model file, not a paid API.

## After doctor

Read `docs/WORKFLOW.md` in the unpacked engine, then the editing skill.
The engine never posts.
