# Journeys: the perspective camera and plane changes (house look)

Status: house style since 2026-11-04. Adem saw the colour and monochrome test cuts and picked
colour journeys with diorama scenes ([dioramas.md](dioramas.md)) as the look new videos start from.
The cuts are in `Arkhē Claude Lab/TALKING_HEAD_NEXT/`: `songwriting-journey` (colour, the
approved songwriting edit re-shot), `songwriting-journey-mono`, and `hologram-diorama-colour`.
`thd news` drafts in this look.

## Why

Adem asked for the immersive travel of our lyric journeys (BDT: the camera as traveller, plane
changes, falling away into other places) and of the 2026 Claude motion wave in the talking-head
work, with the look of Sam's POV (a lit diorama, one red accent, punch-ins on the landing word).
What each source gave:

- **Claude Motion** (Anthropic's launch reel):
  - glides over tilted 3D planes;
  - a pull-back that reveals the shot was a frame;
  - frames that push frames out;
  - the speaker framed beside cards that stack in.
- **The Claude motion-graphics wave:**
  - push-in then pull-back;
  - dives into a subject;
  - every scene made out of the previous one;
  - masked text rises;
  - parallax depth.
- **The BDT journey:**
  - the camera is a traveller;
  - a place changes only through a medium (fall, fold, light, glass).
- **Sam's POV** (a news-explainer Shorts channel):
  - a black stage lit like a diorama;
  - grey world, one red accent;
  - real photos as prints with tags;
  - a punch-in on the landing word;
  - one or two words per caption;
  - a cut every 2-3 s;
  - the speaker as a short still cutaway.

## How it works

`journey:` in a plan swaps the stage for `Stage3D` (`stage3d.py`). Stage3D is a pinhole camera
over the desk plane. Every layer is placed through one plane homography instead of the rostrum
camera's affine. Untilted, the homography is exactly the rostrum camera (tested), so framing,
fits and follows all carry over.

```yaml
journey: {focal: 1.15, dark: 0.35, fog: 0.9, dof: 0.8, pulse: 0.12, pulses: ["B.w:rhetorical"], mono: false}
shots:
  - {at: 0, shot: face, size: P, docs: [{doc: title, slot: br}], snap: true, view: descend}
  - {at: "B.pin", shot: doc, doc: card, via: dive, view: lean}
  - {at: "P.pin", shot: desk, docs: [a, b, c], via: travel, view: low}
sfx: [{kit: whoosh, at: "B.pin", db: -21, pitch: -2}]   # each plane change gets its air
```

**Views (per shot).**

| View | Movement | Use for |
| --- | --- | --- |
| `descend` | Comes down from a high, oblique view and settles in about 1.2 s. Frame 0 is the thumbnail, so it starts close enough to read. | Openings |
| `lean` | A 12° lean with a slow heading drift. | Any paper being read |
| `glide` | Leans in to 22° and drifts. | Short reads, clippings |
| `low` | A low sweeping pass at 44→32°. | Overviews and endings |
| `{tilt, yaw, roll, push}` | Each value, or an `[a, b]` pair, eased across the shot. | Custom moves |

**Plane changes (per shot, `via:`).** The outgoing shot's last frame becomes a card in 3D; the
incoming shot plays live underneath.

| `via:` | What happens |
| --- | --- |
| `fall` (0.55 s) | The old plane hinges at its foot, tips back and falls away into the dark. |
| `dive` (0.6 s) | The camera falls through the old plane, which is gone by mid-move. The next plane rises from the dark. |
| `travel` (0.42 s) | A lateral whip: one plane swings out and the next swings in. |
| `flip` (0.5 s) | The plane turns over; the next shot is on its back. |

`via_dur` sets a length. Each plane change is motion-blurred across a 216° shutter, with 14-28
samples so fast whips blur instead of stepping.

**Light and lens.**
- `dark` deepens the light falloff at the desk's edges, for a lit stage.
- `fog` sinks the far desk into darkness when the camera tilts.
- `dof` blurs by depth from the focus plane, at most 9 px at 1080 wide.
- `pulses` are quick punch-ins that ease back (+12 %, 70 ms in, 160 ms decay).
- `mono: true` turns the stage grey; the presenter print, films and the vermilion ink keep their colour.
  Scene shots ([dioramas.md](dioramas.md)) keep their own palette. Mono is an alternative look, not the
  default.

## Grammar from the first tests

- **Frame 0 is the thumbnail.** `descend` must start close: the face and title still read.
- **Plane changes are punctuation.** Use them on at most about half the shot changes, and keep
  hard cuts between them for contrast. Never start one in the middle of a sung line or the line
  that carries the point.
- **Any paper being read stays near flat** (`lean`, at most 12°). Depth of field must never take
  the words.
- **Pulses go on the word that lands,** about five a minute at most.
- **Check every plane change frame by frame** with `stills` at 0.1-0.15 s spacing before
  rendering. A matrix bug here shows up only inside the move.

## Cost

A journey render costs more than a flat one: perspective warps everywhere, depth of field on
tilted views, and 14-28 shutter samples inside plane changes. Measured 2026-11-04: the 19 s
hologram cut (two scenes, three plane changes) runs `thd all` in 104 s, ASR included, with other
work on the machine.
