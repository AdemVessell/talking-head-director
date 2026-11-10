# Port notes (2026-11-10)

Copied from the private skill at commit e463662 (scripts + references), then:

- fonts by role (`thd_engine/fonts.py`): open file first, system font as fallback
- every library sound has a synthesised version (`sound.synth`); Apple's library is optional
- selftest speaks with `say` or `espeak-ng`; doctor is platform-neutral
- `thd auto` + `thd styles` (auto.py, styles.py); `timeline` treatment on a new `midnight` surface;
  caption colour, mode and font can be set from a plan
- private references and the Blender diorama kit moved to PRIVATE_DO_NOT_SHIP/ (git-ignored)

Verified on the Mac: doctor 17 pass; selftest PASS (81 s); `auto` with a brief in the timeline
style on the selftest clip (synthesised sounds); `auto` with no brief on a real 58 s recording
(317 s, pre-posting check clean).

Before any release:
1. DONE 2026-11-10: 15 open font files bundled in assets/fonts with licences and hashes (google/fonts at
   5bb28733); all 21 roles resolve to them; selftest PASS (90 s). The marker title is slightly smaller than
   the Mac one (14 px at feed width, on the warning line): enlarge the sticky title.
2. Listen to the synthesised sounds; nobody has heard them.
3. Run on Linux (the cloud computer): install, selftest, time one real edit.
4. DECIDED 2026-11-10 (owner): the colour-journey camera ships. `journey` is a style, `newsdesk` uses it, and
   `journey: true` in a brief turns it on for any style. Verified on the selftest clip (descend, dive, lean).
   The Blender diorama kit stays in PRIVATE_DO_NOT_SHIP (needs Blender; not decided).
   Seen: during the descend a caption word can sit on the print's bottom edge and lose contrast.
5. Write public docs (the old references are written for one person's workflow).
6. Licence and author name.
7. Known look defects: the thumbnail frame can catch closed eyes; the bottom third is empty by design
   (room for the feed's own buttons) and may read as unfinished in some styles.
8. Captions show the transcript as heard; a brief cannot yet correct a misheard word.
