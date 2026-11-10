"""Talking-head edit engine: one plan file per video drives the whole edit.

plan (JSON/YAML) -> prep (ranges, audio, face tracks, forced alignment)
-> dialogue edit (EDL, room tone, edit-time words) -> materials (board,
receipts, tape, stamps) -> stage (rostrum camera over physical layers)
-> captions -> sound (voice chain + SFX kit) -> render -> assemble -> audit.

Every cue is a time expression keyed to words ("A.w:lasted-2f"), so a
re-cut moves picture, graphics and sound together. See docs/WORKFLOW.md.
"""
