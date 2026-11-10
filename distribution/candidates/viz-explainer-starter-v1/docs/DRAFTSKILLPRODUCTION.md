Produce a story-driven animated explainer with a VizExplainer project.

1. Idea to beats: write the single claim the viewer should leave with, then 3–6 beats, each one visible action that proves one step. Put beats and on-screen text (seconds) in src/timeline.json. Text hold >= max(1.2 s, 0.3 s/word + 0.5 s). One short line per caption.
2. References: if the user gives references, list what to borrow (light, palette, camera grammar) and what never to copy (their images, characters, logos, fonts). Use original shapes only.
3. World: in src/scene.ts build real objects that perform the explanation (things move, assemble, cast shadows) instead of labels on flat diagrams. Keep update(t) a pure function of time. Palette and type live in src/tokens.ts.
4. Camera: one continuous camera via the Track keys (time, position, look-at). Few keys, ease into a final hold. Avoid passing through objects; check near/mid/far depth.
5. Look checks: render stills at each beat boundary (`npx remotion still ... --frame=N --gl=swangle`), assemble a contact sheet with ffmpeg hstack, and look at it. Fix framing, cropping, unreadable text, and anything that reads as a fake (paint wipes, floating bars) before rendering motion.
6. Sound: offline synthesized only (scripts/make-sound.mjs): bed + one cue per beat. No voice or music APIs unless the user asks and approves cost.
7. Render: `bash scripts/render.sh Draft` to review, then `bash scripts/render.sh Main`. It produces a master (H.264 High, yuv420p, faststart) and a 720-wide Constrained Baseline copy when wider than 720, and fits audio on the final encode to -14 LUFS ±1, true peak <= -1 dBTP.
8. QA: `node qa/check.mjs out/<id>-master.mp4 <WxH>` (strict decode, fps 30, size, pix_fmt, loudness) and `bash qa/font-test.sh` (missing font must fail). Report the QA line, file paths, and honest limits.
9. If renders crash with OOM, lower concurrency/size/shadow-map size. Report times in the user's zone. Never publish or send without explicit approval.
