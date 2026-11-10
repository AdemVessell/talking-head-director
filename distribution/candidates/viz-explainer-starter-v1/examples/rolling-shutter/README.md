# Rolling-shutter example (optional)
A tiny, original numeric model: rows start exposing one after another (rolling) or all at once (global).
A vertical bar moving sideways becomes slanted under rolling shutter and stays upright under global shutter.
`node model.mjs` writes `rolling.pgm` and `global.pgm` (view or convert with `ffmpeg -i rolling.pgm rolling.png`).
Background reading: Basler product documentation, "Electronic Shutter Types" and "Sensor Readout Time".
Use the output as a texture or as a reference for a scene; the starter does not depend on it.
