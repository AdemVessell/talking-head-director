# Workflow

One person talking to a camera has to feel like a show. Story and rhythm come
first. Layout and texture serve them. A finished layout with the recording's
original rhythm left untouched is the failure this engine exists to avoid.

The engine never posts. `POST.md` is a draft for a person to read. Nothing in
this package uploads, tweets, or sends a file.

## Order of work

1. **Cut the story first.** From the word transcript, find the hook, the stakes,
   the turn, and the ending. Reorder and remove only what the edit needs.
   `thd auto RECORDING --draft` lists the lines and their ids. A brief's `keep`
   list is that decision. No graphic exists to hide a slow cut.
2. **Shoot the edit.** Every line gets a shot. `thd styles` names the starting
   points (desk, journey, timeline, newsdesk, notebook, receipts, workbench,
   pinboard, chalkboard, clean). A style is a desk, papers, caption look, and
   pace. It is not a new set of facts.
3. **Make it explain.** Papers write, type, or print on the presenter's own
   words. Titles and points in a brief must be those words. A headline is
   verbatim and carries its source. A screenshot is a real capture. Do not
   rebuild a post, a chart, or a quote so that it looks real. Label an
   illustration that could be mistaken for evidence. Keep hedges
   ("about five minutes" stays approximate).
4. **Bind it.** One finish over the frame. The open fonts in `assets/fonts`
   are the faces this package draws. They are not the original macOS faces.
5. **Make it sound finished.** The voice is tightened by cutting, never by
   speeding the performance up, and it is not mirrored unless the recording
   itself was mirrored and a brief sets `flip` on purpose. Mix target is
   -14 LUFS. Missing library sounds are synthesised. Do not call a paid sound
   service from this package.
6. **Prove the opening, then the whole.** `thd stills` for the frames you are
   unsure of, then `thd all` or `thd auto`.
7. **Score what was rendered.** `work/review/CRITIC.md` is about the frames,
   not the plan's intent. `thd xcheck` flags calls to action, missing sources,
   and claims. A person posts. The tool does not.

`journey` is a style: the camera descends onto the presenter and changes plane
on some cuts. `newsdesk` uses it. `journey: true` in a brief turns it on for
any style. This package does not include a Blender diorama kit. Do not invent
a scene to fill that slot. A take that does not need an object does not get one.

## Hands-free path

```bash
scripts/thd auto RECORDING --draft
# write brief.yaml from those line ids
scripts/thd auto RECORDING --brief brief.yaml --style desk
```

`brief.yaml` keys are in the `thd auto` help (`scripts/thd_engine/auto.py`).
Unknown line ids stop the run. `keep` reorders. The default cut removes
fillers, immediate repeats, and long pauses, and it does not drop a sentence
on its own.

## Captions

One to four words per card, at most 18 characters on a line, broken at
punctuation and pauses. Numbers stay with their units. The layout does not
reflow while a word lights up. Captions show the words that were aligned.
A brief cannot yet correct a misheard word.

## Definition of done

- The story is the presenter's, including the hedges.
- The performance was not sped up and was not mirrored to manufacture energy.
- No invented screenshot, quote, chart, or incident.
- `thd xcheck` has been read. Starred lines are the editor's to clear.
- You watched the render at normal speed, at phone size, with sound. If you
  could not, say so. Doctor and selftest numbers are necessary and not enough.
- Deliver the review MP4, the SRT, and a short note of what changed and what
  was not checked.

## What is not in this package

The private art-direction notes and the Blender diorama scripts were withheld
on purpose. The looks that ship are the styles `thd styles` prints and the
behaviour in this file. Owner-written code is MIT, copyright Adem Vessell
(`LICENSE`). Third-party terms are in `NOTICES.md`. This package does not
include the author's recordings, private notes, or private font files.
