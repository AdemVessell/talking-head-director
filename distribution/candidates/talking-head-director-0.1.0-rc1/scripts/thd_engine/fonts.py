"""Fonts by role, so the engine draws the same on any machine.

Every face the engine uses is a role with an ordered list of candidates. The open-licensed
file comes first (bundled in assets/fonts with its licence), then the
macOS system font the look was designed on, then a common Linux system font. The first file
that exists wins; `thd doctor` prints which one each role resolved to.

  fonts.resolve("caption_heavy") -> (path, face index)
  fonts.load("caption_heavy", 80) -> PIL ImageFont

THD_FONTS=/some/dir adds a folder of your own files, searched first by file name.
THD_FONTS_PREFER=system puts the system fonts ahead of the open files (the original Mac look).
"""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLED = HERE.parent.parent / "assets" / "fonts"
SUP, SYS = "/System/Library/Fonts/Supplemental/", "/System/Library/Fonts/"
DEJAVU = "/usr/share/fonts/truetype/dejavu/"

# role: [open file (in assets/fonts), (macOS path, index), (Linux path, index)]
ROLES = {
    "caption_heavy": ["BarlowCondensed-ExtraBold.ttf", (SYS + "Avenir Next Condensed.ttc", 8)],
    "caption_bold": ["BarlowCondensed-Bold.ttf", (SYS + "Avenir Next Condensed.ttc", 0)],
    "courier": ["CourierPrime-Bold.ttf", (SUP + "Courier New Bold.ttf", 0), (DEJAVU + "DejaVuSansMono-Bold.ttf", 0)],
    "typewriter": ["SpecialElite-Regular.ttf", (SUP + "AmericanTypewriter.ttc", 0)],
    "typewriter_bold": ["SpecialElite-Regular.ttf", (SUP + "AmericanTypewriter.ttc", 2)],
    "typewriter_cond": ["SpecialElite-Regular.ttf", (SUP + "AmericanTypewriter.ttc", 5)],
    "rockwell": ["ZillaSlab-Bold.ttf", (SUP + "Rockwell.ttc", 2)],
    "hand": ["PatrickHand-Regular.ttf", (SUP + "Bradley Hand Bold.ttf", 0)],
    "hand_bold": ["PatrickHand-Regular.ttf", (SYS + "Noteworthy.ttc", 1)],
    "marker": ["PermanentMarker-Regular.ttf", (SYS + "MarkerFelt.ttc", 1)],
    "didot": ["AbrilFatface-Regular.ttf", (SUP + "Didot.ttc", 2)],
    "didot_r": ["GFSDidot-Regular.ttf", (SUP + "Didot.ttc", 0)],
    "georgia": ["LibreBaskerville-Variable.ttf", (SUP + "Georgia.ttf", 0)],
    "georgia_italic": ["LibreBaskerville-Italic-Variable.ttf", (SUP + "Georgia Italic.ttf", 0)],
    "georgia_bold": ["LibreBaskerville-Variable.ttf", (SUP + "Georgia Bold.ttf", 0)],
    "menlo": ["IBMPlexMono-Regular.ttf", (SYS + "Menlo.ttc", 0), (DEJAVU + "DejaVuSansMono.ttf", 0)],
    "menlo_bold": ["IBMPlexMono-Bold.ttf", (SYS + "Menlo.ttc", 1), (DEJAVU + "DejaVuSansMono-Bold.ttf", 0)],
    "futura": ["Anton-Regular.ttf", (SUP + "Futura.ttc", 4)],
    "black": ["Anton-Regular.ttf", (SYS + "HelveticaNeue.ttc", 9)],
    "chalk": ["FrederickatheGreat-Regular.ttf", (SUP + "Chalkduster.ttf", 0)],
    "sans_bold": ["BarlowCondensed-Bold.ttf", (SUP + "Arial Bold.ttf", 0), (DEJAVU + "DejaVuSans-Bold.ttf", 0)],
}
# aliases kept for the document kinds and the style frames
ALIASES = {"mono": "courier", "type": "typewriter_cond", "cond": "caption_heavy"}

WEIGHTS = {"georgia_bold": 700}   # weight for roles served by a variable font file
_cache = {}


def _candidates(role):
    role = ALIASES.get(role, role)
    if role not in ROLES:
        raise KeyError(f"unknown font role {role!r}; one of {sorted(ROLES)}")
    open_file, *system = ROLES[role]
    own = [Path(os.environ["THD_FONTS"]).expanduser() / open_file] if os.environ.get("THD_FONTS") else []
    opens = [(str(p), 0) for p in own + [BUNDLED / open_file]]
    system = [(p, i) for p, i in system]
    return system + opens if os.environ.get("THD_FONTS_PREFER") == "system" else opens + system


def resolve(role):
    """(path, face index) of the first candidate that exists."""
    if role not in _cache:
        for p, i in _candidates(role):
            if Path(p).exists():
                _cache[role] = (p, i); break
        else:
            raise SystemExit(f"font role {role!r}: none of its files exist "
                             f"({', '.join(Path(p).name for p, _ in _candidates(role))}). assets/fonts is incomplete (see assets/fonts/README.md)")
    return _cache[role]


def load(role, size):
    from PIL import ImageFont
    p, i = resolve(role)
    f = ImageFont.truetype(p, int(size), index=i)
    w = WEIGHTS.get(ALIASES.get(role, role))
    if w and Path(p).name.endswith("-Variable.ttf"):   # a variable file: pick the weight this role means
        f.set_variation_by_axes([w])
    return f


class _Table(dict):
    """FONTS[name] -> (path, index), resolved on first use (drop-in for the old literal tables)."""

    def __missing__(self, name):
        self[name] = resolve(name)
        return self[name]

    def __contains__(self, name):
        return ALIASES.get(name, name) in ROLES


TABLE = _Table()


def report():
    """[(role, 'open' | 'system' | None, file name)] for the doctor."""
    rows = []
    for role in sorted(ROLES):
        hit = next(((p, i) for p, i in _candidates(role) if Path(p).exists()), None)
        if hit is None:
            rows.append((role, None, ROLES[role][0]))
        else:
            mine = Path(hit[0]).parent in (BUNDLED, Path(os.environ.get("THD_FONTS", "/nonexistent")).expanduser())
            rows.append((role, "open" if mine else "system", Path(hit[0]).name))
    return rows


def open_files():
    return sorted({ROLES[r][0] for r in ROLES})
