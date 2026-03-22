"""
PDF generation service.

Takes a source image, a ``PosterLayout`` (from the slicer), and the user's
``PrintSettings`` to produce a multi-page PDF file where each page contains
one tile of the poster.

Optional extras drawn on each page:
    - **Cut guides** — dashed border lines with scissor icons so the user knows
      exactly where to trim the paper before assembling tiles.
    - **Tile labels** — a small "Row X, Col Y" footer to help with assembly.

The module uses ReportLab for PDF rendering and Pillow for image manipulation.
"""

from __future__ import annotations

from io import BytesIO

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from tarpslice.models.settings import PrintSettings
from tarpslice.services.slicer import PosterLayout, TileRegion
from tarpslice.utils.conversions import mm_to_points


class PdfGenerator:
    """Render sliced image tiles into a multi-page PDF."""

    def generate(
        self,
        image: Image.Image,
        layout: PosterLayout,
        settings: PrintSettings,
    ) -> None:
        """Create the output PDF file on disk.

        Args:
            image:    Source PIL image (already opened and converted to RGB).
            layout:   Poster layout containing tile crop regions.
            settings: Full set of user-selected print options.
        """

        # Convert millimeters to PDF points (1 pt = 1/72 inch).
        page_width_mm, page_height_mm = self._page_dimensions_mm(settings)
        page_width_pt = mm_to_points(page_width_mm)
        page_height_pt = mm_to_points(page_height_mm)
        margin_pt = mm_to_points(settings.margin_mm)

        pdf = canvas.Canvas(
            settings.output_pdf_path,
            pagesize=(page_width_pt, page_height_pt),
        )
        pdf.setTitle("TarpSlice Output")

        printable_width_pt = page_width_pt - (2 * margin_pt)
        printable_height_pt = page_height_pt - (2 * margin_pt)

        # Render one PDF page per tile in row-major order.
        for tile in layout.tile_regions:
            self._draw_page(
                pdf=pdf,
                image=image,
                tile=tile,
                printable_width_pt=printable_width_pt,
                printable_height_pt=printable_height_pt,
                margin_pt=margin_pt,
                settings=settings,
            )
            pdf.showPage()

        pdf.save()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _page_dimensions_mm(settings: PrintSettings) -> tuple[float, float]:
        """Return (width, height) in mm respecting the selected orientation."""
        if settings.orientation == "portrait":
            return settings.paper.width_mm, settings.paper.height_mm
        return settings.paper.height_mm, settings.paper.width_mm

    def _draw_page(
        self,
        pdf: canvas.Canvas,
        image: Image.Image,
        tile: TileRegion,
        printable_width_pt: float,
        printable_height_pt: float,
        margin_pt: float,
        settings: PrintSettings,
    ) -> None:
        """Render a single tile onto one PDF page."""

        # Crop the source image to this tile's region.
        cropped = image.crop(
            (tile.left_px, tile.top_px, tile.right_px, tile.bottom_px)
        )

        # Resize/fit the cropped tile according to the chosen fit mode.
        render_image = self._render_tile_for_mode(
            cropped=cropped,
            box_w=max(1, int(round(printable_width_pt))),
            box_h=max(1, int(round(printable_height_pt))),
            fit_mode=settings.fit_mode,
        )

        # Write the tile image into the PDF via an in-memory PNG buffer.
        buffer = BytesIO()
        render_image.save(buffer, format="PNG")
        buffer.seek(0)
        reader = ImageReader(buffer)

        pdf.drawImage(
            reader,
            margin_pt,
            margin_pt,
            width=printable_width_pt,
            height=printable_height_pt,
            preserveAspectRatio=False,
        )

        # Optional overlays.
        if settings.draw_cut_guides:
            self._draw_cut_guides(
                pdf=pdf,
                x=margin_pt,
                y=margin_pt,
                width=printable_width_pt,
                height=printable_height_pt,
                page_margin=margin_pt,
                tile_row=tile.row,
                tile_col=tile.col,
                total_rows=settings.rows,
                total_cols=settings.cols,
            )

        if settings.draw_labels:
            label = f"Row {tile.row + 1}, Col {tile.col + 1}"
            pdf.setFont("Helvetica", 8)
            pdf.drawString(margin_pt, margin_pt / 3, label)

    @staticmethod
    def _render_tile_for_mode(
        cropped: Image.Image,
        box_w: int,
        box_h: int,
        fit_mode: str,
    ) -> Image.Image:
        """Resize the cropped tile to fill the printable box.

        Modes:
            fit     – Scale to fit inside the box; aspect ratio preserved; may
                      leave white space on shorter dimension.
            stretch – Force-resize to exact box dimensions (may distort).
            cover   – Scale up and center-crop so the box is fully filled.
        """

        crop_w, crop_h = cropped.size
        crop_ratio = crop_w / crop_h
        box_ratio = box_w / box_h

        # Stretch: simple resize ignoring aspect ratio.
        if fit_mode == "stretch":
            return cropped.resize((box_w, box_h), Image.LANCZOS)

        # Cover: scale up so the shorter dimension fills the box, then center-crop.
        if fit_mode == "cover":
            if crop_ratio > box_ratio:
                scaled_h = box_h
                scaled_w = int(round(scaled_h * crop_ratio))
            else:
                scaled_w = box_w
                scaled_h = int(round(scaled_w / crop_ratio))

            resized = cropped.resize((scaled_w, scaled_h), Image.LANCZOS)
            left = max(0, (scaled_w - box_w) // 2)
            top = max(0, (scaled_h - box_h) // 2)
            return resized.crop((left, top, left + box_w, top + box_h))

        # Fit (default): scale to fit inside the box with letterboxing.
        if crop_ratio > box_ratio:
            draw_w = box_w
            draw_h = int(round(draw_w / crop_ratio))
        else:
            draw_h = box_h
            draw_w = int(round(draw_h * crop_ratio))

        resized = cropped.resize((draw_w, draw_h), Image.LANCZOS)

        canvas_img = Image.new("RGB", (box_w, box_h), "white")
        paste_x = (box_w - draw_w) // 2
        paste_y = (box_h - draw_h) // 2
        canvas_img.paste(resized, (paste_x, paste_y))
        return canvas_img

    @staticmethod
    def _draw_cut_guides(
        pdf: canvas.Canvas,
        x: float,
        y: float,
        width: float,
        height: float,
        page_margin: float,
        tile_row: int,
        tile_col: int,
        total_rows: int,
        total_cols: int,
    ) -> None:
        """Draw dashed border lines and scissor icons around the printable area.

        Scissor marks appear only on edges that border another tile (i.e. not on
        the outermost edges of the poster).
        """

        pdf.saveState()
        pdf.setLineWidth(0.6)
        pdf.setDash(4, 3)

        # Dashed rectangle around the printable region.
        pdf.line(x, y + height, x + width, y + height)   # top
        pdf.line(x, y, x, y + height)                    # left
        pdf.line(x + width, y, x + width, y + height)    # right
        pdf.line(x, y, x + width, y)                     # bottom

        pdf.setDash()
        pdf.setFont("Helvetica", 7)

        inset = max(4, page_margin / 2)

        # Right seam -> vertical cut -> rotate scissor upward.
        if tile_col < total_cols - 1:
            pdf.saveState()
            pdf.translate(x + width + (inset / 2), y + (height / 2))
            pdf.rotate(90)
            pdf.drawCentredString(0, 0, "✂")
            pdf.restoreState()

        # Bottom seam -> horizontal cut.
        if tile_row < total_rows - 1:
            pdf.drawCentredString(
                x + (width / 2),
                y - (inset / 2) - 2,
                "✂",
            )

        pdf.restoreState()
