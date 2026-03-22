"""
Data models that describe user-selected print settings.

Both ``PaperSize`` and ``PrintSettings`` are **frozen** dataclasses — once
created they cannot be mutated.  This guarantees that the settings collected
during the CLI wizard are passed unchanged through the generation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaperSize:
    """Physical paper dimensions in millimeters (portrait orientation).

    Attributes:
        name:      Human-readable label, e.g. "A4" or "LETTER".
        width_mm:  Sheet width in millimeters.
        height_mm: Sheet height in millimeters.
    """

    name: str
    width_mm: float
    height_mm: float


@dataclass(frozen=True)
class PrintSettings:
    """Complete snapshot of every option the user selected in the wizard.

    Attributes:
        image_path:      Absolute path to the source image.
        output_pdf_path: Absolute path for the generated PDF.
        paper:           Selected paper size (see ``PaperSize``).
        orientation:     "portrait" or "landscape".
        rows:            Number of tile rows in the poster grid.
        cols:            Number of tile columns in the poster grid.
        margin_mm:       Blank border reserved on all four sides of each sheet.
        overlap_mm:      Extra bleed shared between adjacent tiles for assembly.
        draw_cut_guides: If True, dashed cut lines and scissor icons are drawn.
        draw_labels:     If True, "Row X, Col Y" labels appear on each page.
        fit_mode:        How the image fills each tile — "fit", "stretch", or
                         "cover".
    """

    image_path: str
    output_pdf_path: str
    paper: PaperSize
    orientation: str
    rows: int
    cols: int
    margin_mm: float
    overlap_mm: float
    draw_cut_guides: bool
    draw_labels: bool

    fit_mode: str = "fit"   # "fit" | "stretch" | "cover"
