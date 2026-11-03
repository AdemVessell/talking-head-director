# Style frames: visual targets, not templates

Rendered by `scripts/style_frames.py` from a real presenter plate. The copy
($20, three tools, 3H 12M) is illustrative only. Copy the materials, scale
contrast, light and finish; never copy a layout verbatim.

| Frame | Set | Shot | What it demonstrates |
|---|---|---|---|
| 01 | EVIDENCE BOARD | C, 4:5 print window | Hook frame. The camera as a physical print with tape and a shadow, a RECEIPT with the numbers, a STAMP that stays off the face, word-timed caption with the active word and the number in vermilion, one warm light pool. |
| 02 | FIELD JOURNAL | H, small torn window | An explanation drawn in ink on a 12-column grid: headline in columns 1-6, camera in columns 7-12. A MARKER circle with a hand note, a halftoned and misregistered taped clipping, ink captions on the light stage (`light_stage=True`). |
| 03 | SIGNAL | X, full bleed | "The turn". A monitor window with barrel distortion, scanlines and chroma bleed, a ticker in the set's amber, timecode, and a tally in the house vermilion. |
| 04 | REVEAL | cutaway | A hero number at about 400 px with an 8x+ type scale range, the MARKER underline, the ledger line, and air. No caption, because the hero type is the caption. |

All four frames use `look.grade_webcam` on the face and `look.Finish` over the
whole frame (subtle on the journal, medium elsewhere).
