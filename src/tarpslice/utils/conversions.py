"""
Physical unit conversion helpers.

The application stores all user-facing dimensions in millimeters for
readability, but ReportLab's PDF canvas works in **points** (1 inch = 72 pt).
This module bridges the two systems.
"""

from __future__ import annotations

# Conversion factors.
MM_PER_INCH = 25.4
POINTS_PER_INCH = 72.0


def mm_to_points(mm: float) -> float:
    """Convert a value in millimeters to PDF points.

    Formula: points = (mm / 25.4) * 72
    """

    return (mm / MM_PER_INCH) * POINTS_PER_INCH
