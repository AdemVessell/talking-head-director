# Owner decisions

The MIT grant and the repository name below were approved. Nothing has been
published. Private repositories stay private.

## Decided

- Owner-written code is MIT, copyright Adem Vessell. Third-party terms stay
  as written in each package.
- The intended public repository is `AdemVessell/bot-video-engines`, one
  repository, two release assets on tag `rc1`. It is not created by this
  branch. Existing private repositories stay private.

## Still blocking a publish

1. The empty public repository does not exist yet. The parent creates it.
   This branch does not.
2. A person still has to watch the full selftest and Viz renders with sound.
   The checks here measured levels and used a video model. They are not that
   listening session. `PUBLISHED` stays `no` until that review and the
   repository both exist.
3. Confirm the version labels `0.1.0-rc1` and starter `1.0.0` are the ones
   to upload. The intended asset names match those labels.

## Still true, and not a reason to drop the packages

- Apple system fonts and Final Cut Pro sounds are not included. Open fonts
  and synthesised cues are what ships. A person still has to listen.
- The measured selftest mix was about -15.7 LUFS (the target band is -14 ±1)
  with true peak -1.4 dBTP. That is a warning, not a silent retune.
- Whisper `medium.en` downloads on first use, about 1.5 GB. It is not bundled.
- `opencv-contrib-python` stays at the port's pin. Its Apache license does
  not clear every contrib patent question.
- The Blender kit, private notes, real-presenter stills, and private skill
  wrappers stay out.
- Remotion is not MIT. three.js is MIT. The two Viz fonts are SIL OFL 1.1,
  and IBM Plex reserves the name "Plex".
- The parent getting-started skill does not rebuild a missing starter. It
  waits until the release exists.
