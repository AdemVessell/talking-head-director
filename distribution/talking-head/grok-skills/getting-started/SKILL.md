---
name: talking-head-director-getting-started
description: Install the talking-head edit engine from its versioned archive into an isolated directory, then run doctor. Use when setting up the engine on a machine that does not already have it. The archive URL in this skill is PLACEHOLDER_RELEASE_URL and is not a working download.
---

# Getting started

The engine is not on the author's computer, and it is not in this skill.
This skill does not contain the engine's files. Fetch one versioned archive,
check its SHA256, and install that tree. Do not search a private repository,
a private Drive, or a Mac path.

## The archive is not published yet

`PLACEHOLDER_RELEASE_URL` is not a working download. Do not invent a URL.
Do not guess a filename. If the release URL in `RELEASE_URL` still contains
`PLACEHOLDER`, stop and say the package has not been published. The bootstrap
script does the same thing and exits without fetching.

When the copyright holder replaces that placeholder with a real URL, the
archive must be `talking-head-director-0.1.0-rc1.tar.gz` and its SHA256 must
be exactly:

600a299878fdbdd1385c31ae56786515bb19a922eb23ce4d7244e0deb44dcfe5

A different hash means a different file. Do not install it.

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
