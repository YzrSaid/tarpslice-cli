"""
Image slicing / layout engine.

This module is responsible for computing the **tile grid** — the set of crop
rectangles that map regions of the source image onto individual printed pages.

Workflow:
    1. The poster canvas size is calculated as (cols * page_width, rows * page_height).
    2. The source image is virtually fitted inside that canvas (aspect-ratio aware).
    3. Each tile's poster-space rectangle is converted back to source-pixel
       coordinates so the image can be cropped without intermediate resizing.
    4. An optional overlap is added between neighboring tiles to compensate for
       imprecise cutting during physical assembly.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from PIL import Image


@dataclass(frozen=True)
class TileRegion:
    """A single tile's crop rectangle in **source-image pixel** coordinates.

    Attributes:
        row / col:                Grid position (zero-indexed).
        left_px / top_px:         Top-left corner of the crop box.
        right_px / bottom_px:     Bottom-right corner of the crop box.
    """

    row: int
    col: int
    left_px: int
    top_px: int
    right_px: int
    bottom_px: int


@dataclass(frozen=True)
class PosterLayout:
    """Container for the full poster grid and its tile regions.

    Attributes:
        poster_width_px / poster_height_px: Virtual poster dimensions.
        tile_regions: Ordered list of ``TileRegion`` objects (row-major).
    """

    poster_width_px: int
    poster_height_px: int
    tile_regions: list[TileRegion]


class ImageSlicer:
    """Compute tile crop regions for a source image.

    The source image is conceptually resized to a final poster size based on the
    printable area of each page multiplied by rows and columns.  Each tile maps
    back to a crop in source pixels so the original image data is preserved.
    """

    def build_layout(
        self,
        image: Image.Image,
        rows: int,
        cols: int,
        printable_width_px: int,
        printable_height_px: int,
        overlap_px: int,
    ) -> PosterLayout:
        """Build the complete poster layout for the given image and grid size.

        Args:
            image:               Source PIL image.
            rows:                Number of rows in the tile grid.
            cols:                Number of columns in the tile grid.
            printable_width_px:  Printable width of one page (virtual pixels).
            printable_height_px: Printable height of one page (virtual pixels).
            overlap_px:          Extra overlap between neighboring tiles.

        Returns:
            A ``PosterLayout`` containing all tile crop regions.
        """

        if rows <= 0 or cols <= 0:
            raise ValueError("Rows and columns must both be greater than zero.")

        # Total final poster dimensions based on the page grid.
        poster_width_px = cols * printable_width_px
        poster_height_px = rows * printable_height_px

        # Fit the source image into the poster area while preserving aspect ratio.
        source_width, source_height = image.size
        source_ratio = source_width / source_height
        poster_ratio = poster_width_px / poster_height_px

        if source_ratio > poster_ratio:
            # Image is wider than the poster — constrain by width.
            fitted_width = poster_width_px
            fitted_height = int(round(fitted_width / source_ratio))
        else:
            # Image is taller than the poster — constrain by height.
            fitted_height = poster_height_px
            fitted_width = int(round(fitted_height * source_ratio))

        # Center the fitted image within the poster area.
        offset_x = (poster_width_px - fitted_width) // 2
        offset_y = (poster_height_px - fitted_height) // 2

        tile_regions: list[TileRegion] = []

        for row in range(rows):
            for col in range(cols):
                # Determine the tile boundaries in poster-pixel space.
                tile_left = col * printable_width_px
                tile_top = row * printable_height_px
                tile_right = tile_left + printable_width_px
                tile_bottom = tile_top + printable_height_px

                # Expand edges by overlap_px for neighboring tiles.
                if col > 0:
                    tile_left -= overlap_px
                if row > 0:
                    tile_top -= overlap_px
                if col < cols - 1:
                    tile_right += overlap_px
                if row < rows - 1:
                    tile_bottom += overlap_px

                # Convert poster-space coordinates to source-image pixel space.
                crop_left = self._map_range(tile_left, offset_x, fitted_width, source_width)
                crop_top = self._map_range(tile_top, offset_y, fitted_height, source_height)
                crop_right = self._map_range(tile_right, offset_x, fitted_width, source_width)
                crop_bottom = self._map_range(tile_bottom, offset_y, fitted_height, source_height)

                # Clamp to the source image bounds to avoid out-of-range crops.
                crop_left = max(0, min(source_width, crop_left))
                crop_top = max(0, min(source_height, crop_top))
                crop_right = max(0, min(source_width, crop_right))
                crop_bottom = max(0, min(source_height, crop_bottom))

                tile_regions.append(
                    TileRegion(
                        row=row,
                        col=col,
                        left_px=crop_left,
                        top_px=crop_top,
                        right_px=max(crop_left + 1, crop_right),
                        bottom_px=max(crop_top + 1, crop_bottom),
                    )
                )

        return PosterLayout(
            poster_width_px=poster_width_px,
            poster_height_px=poster_height_px,
            tile_regions=tile_regions,
        )

    @staticmethod
    def _map_range(value: int, offset: int, fitted_length: int, source_length: int) -> int:
        """Map a coordinate from poster space to source-image space.

        The formula normalizes ``value`` relative to the fitted region inside the
        poster, then scales it to the source image's pixel dimensions.
        """

        relative = (value - offset) / fitted_length
        return int(round(relative * source_length))
