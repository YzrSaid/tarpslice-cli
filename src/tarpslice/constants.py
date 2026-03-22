"""
Application-wide constants.

All physical dimensions are stored in **millimeters** so the values stay
human-readable throughout the codebase.  Conversion to PDF points (or pixels)
happens at the last possible moment inside the services layer.

Constants defined here:
    PAPER_SIZES_MM            – Supported paper formats and their dimensions.
    SUPPORTED_IMAGE_EXTENSIONS – File extensions accepted as input images.
    DEFAULT_MARGIN_MM         – Fallback page margin when none is selected.
    DEFAULT_OVERLAP_MM        – Extra overlap between neighboring tiles to
                                make physical assembly easier.
    DEFAULT_DPI               – Dots-per-inch used for raster operations.
"""

from __future__ import annotations

# Standard paper sizes in millimeters: (width_mm, height_mm)
# Dimensions follow the portrait orientation by convention.
PAPER_SIZES_MM: dict[str, tuple[float, float]] = {
    "A4": (210.0, 297.0),
    "LETTER": (215.9, 279.4),
    "LEGAL": (215.9, 355.6),
    "LONG_BOND": (215.9, 330.2),
}

# Accepted source-image file types (case-insensitive check at validation time).
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

# Sensible defaults used when the user does not override a value.
DEFAULT_MARGIN_MM = 8.0       # Blank border around each printed sheet.
DEFAULT_OVERLAP_MM = 5.0      # Extra bleed shared between adjacent tiles.
DEFAULT_DPI = 300             # Print-quality resolution target.
