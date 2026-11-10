# Owner decisions still open

Nothing in this list has been approved by preparing the candidates.
No license was selected. No public repository name was selected.
No release was published.

## Both packages

1. Choose a license for the owner-written source, or state that it stays
   unlicensed. The candidates do not apply one.
2. Choose the public repository names and the real download URLs that replace
   `PLACEHOLDER_RELEASE_URL`. Until that URL is replaced, the bootstrap scripts
   refuse to fetch.
3. Decide whether these are two public repositories or two release assets of
   one. This review does not create either.
4. Confirm the version labels `0.1.0-rc1` (talking-head) and the existing
   starter `1.0.0` (Viz). They are labels for these archives, not a promise
   that the numbers are final.

## Talking-head director

5. The engine source has no license. `NOTICES.md` says so. A public git push
   of that source would be a publication. That is not done here.
6. Apple system fonts and Final Cut Pro sounds are not in the candidate.
   Say whether the open-font look and the synthesised sound are acceptable
   to ship, after someone has listened to the synthesised kit (`NOTES.md`
   item 2: nobody has).
7. The Apache sidecars for Permanent Marker and Special Elite now repeat the
   copyright strings stored in the font files. Confirm that is the notice
   you want next to the Apache boilerplate.
8. Whisper `medium.en` is downloaded on first use and is not bundled. Decide
   whether a public doc should vendor the weight license text.
9. `opencv-contrib-python` may carry patent questions beyond its package
   license. Decide whether the public pin stays on contrib or moves to
   `opencv-python` (not done here; the port pins contrib).
10. The Blender diorama kit and the private reference notes stay out. Decide
    whether a later public doc, written without personal paths, should cover
    dioramas. This candidate tells editors not to invent a scene.
11. `sheet_real.jpg` and the private style-frame JPEGs show a real presenter.
    They are not in the archive. Decide if any still of that person is ever
    public.
12. The port's Mac selftest (81 s and 90 s) and the 58 s real-recording run
    are claims in `NOTES.md`. They were not re-run here. The Linux evidence
    is separate and does not confirm those Mac numbers.
13. Known look notes in `NOTES.md` (sticky title size, caption contrast on the
    descend, closed eyes on a thumbnail) are unfixed. Shipping with them is
    a decision.

## VizExplainer starter

14. The starter README says "Starter code and generated assets: yours."
    There is no SPDX license file for that code. "Yours" is not treated here
    as an approved open-source grant. Choose the actual license or remove
    that sentence before a public copy.
15. Remotion is not MIT. The free tier is individuals, for-profit organisations
    with up to 3 employees, and non-profits, plus evaluation that is not yet
    commercial. Other for-profit companies need a Company License. Remotion 5.0
    is noted by upstream as a further change. Decide that the public README
    keeps pointing at `LICENSES/REMOTION-LICENSE.md` and that you accept that
    term for the way you will offer the starter.
16. three.js is MIT, as `LICENSES/THREE-LICENSE.txt` states. React and
    TypeScript licenses follow their own packages (installed by `npm ci`, not
    bundled). Do not summarise the whole starter as MIT.
17. Bodoni Moda and IBM Plex Mono are SIL OFL 1.1 and are bundled with their
    license texts. IBM Plex reserves the name "Plex". The files are unmodified.
    Confirm you want those two faces redistributed in the public zip.
18. The original draft setup skill tells a bot to rebuild a minimal project
    when no zip is attached. The parent getting-started skill for this
    candidate does not. It stops when the URL is still the placeholder.
    Decide which instruction a public bot should follow. This candidate's
    parent skill stops.
