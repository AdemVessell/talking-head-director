# Dioramas: animated scene shots from Blender (house look)

Status: house style since 2026-11-04, with colour journeys ([journeys.md](journeys.md)). The worked
example is `examples/hologram-diorama/`: the plan and both scene scripts. Its renders are in
`Arkhē Claude Lab/TALKING_HEAD_NEXT/`: `hologram-diorama-colour` (the house look) and
`hologram-diorama` (the mono original).

This is the Sam's POV format: animated diorama scenes carry the lines while his voice runs over
them, and his own footage carries the payoff. A scene is a full-frame clip rendered in Blender,
keyed to his words, and placed in the plan as `shot: scene`. Captions, the finish, sound and
plane changes (`via:`) all work on it like any other shot.

## When a video gets a scene

- **The thing the story turns on:** an object he took apart, a mechanism, a place, a chain of
  cause and effect. One or two scenes in a short, each about 4-7 s, entered and left by plane
  changes.
- **His footage carries the payoff.** The scene explains; his own shot proves it.
- **A pure opinion take can do without one.** Never add a generic scene to fill the slot: plain
  CGI fails (SKILL.md, standing taste).
- **Budget the time.** Each topic needs its own scene design (the kit and the grammar carry over;
  the props do not yet), and a 6 s scene renders in about 4-7 minutes at full size.

## Making one

1. **Cut the edit first** (`autocut`, plan, `prep`, `inspect`, `edit`). Scene timing comes from the
   edit, so it has to exist.
2. **Export the scene's word times** relative to the shot start (seconds) as JSON. For example:
   `{"dur": 6.34, "television": 2.64, "broke": 3.72, "layers": 5.94}`, built with
   `Timeline.t("B.w:broke") - Timeline.t("B.pin")`.
3. **Write a scene script** that imports `scripts/diorama/kit.py`. Build the set, then write one
   `frame(t)` that sets every animated value for time t, register it with `K.animate(frame)`, and
   end with `K.render(a, sc)`.
4. **Preview stills first, at half size.** Each takes about 0.4 s:
   `Blender -b --factory-startup -P scene.py -- --times s.json --out preview --stills 0.5,2.9,5.6 --scale 50 --samples 16`
5. **Render and encode:** `scripts/diorama/render_scene.sh scene.py s.json scene.mov 23.976`. The
   frame rate must be the plan's.
6. **In the plan:** `- {at: "B.pin", shot: scene, scene: scenes/scene.mov, via: dive}`.

## The kit (`scripts/diorama/kit.py`)

| Area | What it provides |
| --- | --- |
| Stage | `stage()` (a black floor, then the void), `light()` (SPOT or AREA, aimed), `camera()` with depth of field, `aim(cam, loc, target, focus)` |
| Materials | `mat()` (paper, card, acetate, emissive; `grain` adds paper tooth), `rings()` (a Fresnel lens with a travelling glow), `bars()` (colour bars that can glitch), `hologram`-style translucency in the proof's scene 2 |
| Objects | `box`, `cyl`, `empty`, `text` (macOS fonts, used not redistributed), `tag` (a paper tag on a string), `polyline` (a line that draws itself: cracks, strokes), `dust` (motes) |
| Time | `seg`, `io2`, `io3`, `o3`, `oback`, and `pop(t, t0)`, a stop-motion arrival on twos |

## Art direction (what the first scenes taught)

- **A black void with one pool of light.** Dust motes carry the air. Volumetric haze rendered as
  blotchy noise and washed everything out, so leave it off.
- **Keep paper tooth subtle:** `grain` of 0.01 or less. At 0.06 it reads as stucco. Paper is about
  0.8 albedo and card about 0.26; a beam of about 500 W at 2.6 m and a rim of about 100 W are
  enough. AgX with a medium-high-contrast look rolls the highlights off.
- **One accent.** Vermilion for the thing that matters (a crack, the lens's tag, a fringe).
  Everything else is paper white, card grey, black. Scenes keep their own colour under
  `mono: true`.
- **Compose for 9:16.** Wide objects leave the frame empty, so stack, rise or fan things
  vertically. In the TV, the layers climb toward the camera as a staircase.
- **Tags must face the final camera** and be big enough to read at feed size: text at least
  0.04 m at about 2 m.
- **Key everything to words:** the break on "broke", the fan-out on "various aspects of the
  layers", the lens dropping into its clips on "hung", the grooves lighting on "Fresnel".
- **Moving a parent empty means its start position plus the offset.** Setting an absolute
  location from zero drops the whole group to the origin; that was a real bug in scene 2.
- **Speed on this M1 Max:** half-size previews take about 0.4 s a frame; full size with 32
  samples and motion blur is measured in the proof's NOTE.md.
