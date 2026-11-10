# bot-video-engines

Two packages for presenter video and short explainers. This repository is the
public source. It has no history from any private repository.

Owner-written code in both packages is MIT, copyright Adem Vessell. Each
package has its own `LICENSE`. Third-party terms stay inside the package
(fonts, Remotion, Python wheels). They are not relicensed as MIT.

| Package | Directory | Release asset |
|---|---|---|
| Talking-head director `0.1.0-rc1` | `talking-head-director/` | `talking-head-director-0.1.0-rc1.tar.gz` |
| VizExplainer starter v1 | `viz-explainer/` | `viz-explainer-starter-v1.tar.gz` |

Intended release, tag `rc1`, once this repository exists:

- https://github.com/AdemVessell/bot-video-engines/releases/download/rc1/talking-head-director-0.1.0-rc1.tar.gz
- https://github.com/AdemVessell/bot-video-engines/releases/download/rc1/viz-explainer-starter-v1.tar.gz

Those URLs are not live until the empty repository is created and the `rc1`
release is uploaded. Check the SHA256 published next to each asset before
installing. A bot must not fetch them while the release is absent.

Nothing in these packages posts, uploads, or requires the author's computer,
private repositories, or private recordings. The talking-head package does
not include the private art notes, the Blender diorama kit, or any recording
of a person. `thd auto` is the presenter path. `scripts/aligned` cuts a video
you supply by a segment list. A waveform, a colour track, and a diagram are
optional keys on that path, not a required structure. The first `prep` downloads the Whisper `medium.en` weights
(about 1.5 GB). That download is model weights, not a paid API.

A synthetic selftest is how the engine checks itself. It is not proof of how
a real recording will look.
