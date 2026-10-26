"""Design tokens that match the AlphaDesk web app.

Keeping these in one module means PPTX, DOCX and matplotlib charts all
pick colour, type and spacing from the same source — a single swap moves
every surface together.
"""
from __future__ import annotations

from pptx.dml.color import RGBColor


# ---------------------------------------------------------------------------
# Colour palette — mirrors frontend/src/styles/tokens.css
# ---------------------------------------------------------------------------

# Expressed as (r, g, b) tuples; use HEX() for matplotlib strings and
# RGBColor() for python-pptx / python-docx.
NEUTRAL_900 = (15, 23, 42)       # fg
NEUTRAL_600 = (71, 85, 105)      # fg-muted
NEUTRAL_400 = (148, 163, 184)    # fg-subtle
NEUTRAL_200 = (226, 232, 240)    # hairline
NEUTRAL_100 = (241, 245, 249)    # surface-sunken
NEUTRAL_050 = (248, 250, 252)    # surface-raised
WHITE       = (255, 255, 255)    # surface

ACCENT      = (15, 118, 110)     # teal-700
ACCENT_SOFT = (204, 224, 221)

POS         = (21, 128, 61)      # green-700
POS_BG      = (220, 237, 227)
NEG         = (153, 27, 27)      # red-800
NEG_BG      = (246, 220, 220)
WARN        = (161, 98, 7)       # amber-700


def HEX(rgb: tuple[int, int, int]) -> str:
    """Return '#rrggbb' for a matplotlib colour string."""
    return "#%02x%02x%02x" % rgb


def pptx_rgb(rgb: tuple[int, int, int]) -> RGBColor:
    return RGBColor(*rgb)


# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

FONT_SANS = "Inter"      # falls back to viewer's system font if missing
FONT_SANS_FALLBACK = "Helvetica"
FONT_MONO = "Menlo"

# Scale matches the web app: 12 / 13 / 14 / 16 / 20 / 24 / 32.
FS_HERO    = 32
FS_H1      = 24
FS_H2      = 20
FS_BODY    = 14
FS_SMALL   = 12
FS_LABEL   = 11

# ---------------------------------------------------------------------------
# Spacing (inches). PPTX slides are 13.33 x 7.5".
# ---------------------------------------------------------------------------

MARGIN_X = 0.6
MARGIN_Y = 0.5
GUTTER   = 0.3
