"""
Preview image generator.

Creates a single JPEG file that shows all tiles side-by-side on a virtual
canvas, visually mimicking how the printed pages will look when assembled.
This gives the user a quick sanity check before printing.

The preview replicates the same cut guides and scissor marks that the PDF
renderer draws, so the user can verify alignment at a glance.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from tarpslice.models.settings import PrintSettings


def _load_scissor_font(size: int = 14) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a TrueType font that contains the scissor glyph (U+2702).

    Falls back to Pillow's built-in bitmap font if no suitable system font is
    found.
    """
    for font_name in ("seguisym.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()


class PreviewGenerator:
    """Generate a stitched JPEG preview that visually matches the PDF layout."""

    def generate(
        self,
        image: Image.Image,
        layout,
        settings: PrintSettings,
        output_path: str,
    ) -> None:
        """Render all tiles onto a single preview canvas and save as JPEG.

        Args:
            image:       Source PIL image.
            layout:      ``PosterLayout`` from the slicer.
            settings:    User-selected print options.
            output_path: Destination file path for the preview JPEG.
        """

        tiles = layout.tile_regions
        if not tiles:
            raise ValueError("Layout does not contain any tile regions.")

        rows = max(tile.row for tile in tiles) + 1
        cols = max(tile.col for tile in tiles) + 1

        # Fixed preview page dimensions (pixels) for consistent preview sizing.
        base_page_w = 260
        base_page_h = 360

        if settings.orientation == "landscape":
            page_w = base_page_h
            page_h = base_page_w
        else:
            page_w = base_page_w
            page_h = base_page_h

        margin = 18
        printable_w = page_w - (2 * margin)
        printable_h = page_h - (2 * margin)

        # Full canvas holding every tile in its grid position.
        canvas_w = cols * page_w
        canvas_h = rows * page_h

        preview = Image.new("RGB", (canvas_w, canvas_h), "white")
        draw = ImageDraw.Draw(preview)
        font = _load_scissor_font(14)

        for tile in tiles:
            page_x = tile.col * page_w
            page_y = tile.row * page_h

            # Light border representing the physical sheet edge.
            draw.rectangle(
                (page_x, page_y, page_x + page_w - 1, page_y + page_h - 1),
                fill="white",
                outline=(180, 180, 180),
                width=1,
            )

            # Crop and resize the tile to fit the preview's printable area.
            cropped = image.crop(
                (tile.left_px, tile.top_px, tile.right_px, tile.bottom_px)
            ).convert("RGB")

            tile_image = self._fit_tile_to_box(
                cropped=cropped,
                box_w=printable_w,
                box_h=printable_h,
                fit_mode=settings.fit_mode,
            )

            draw_x = page_x + margin
            draw_y = page_y + margin
            preview.paste(tile_image, (draw_x, draw_y))

            # Draw cut guides if enabled (mirrors the PDF output).
            if settings.draw_cut_guides:
                self._draw_cut_guides(
                    preview=preview,
                    draw=draw,
                    font=font,
                    x=page_x + margin,
                    y=page_y + margin,
                    width=printable_w,
                    height=printable_h,
                    page_margin=margin,
                    tile_row=tile.row,
                    tile_col=tile.col,
                    total_rows=rows,
                    total_cols=cols,
                )

        preview.save(output_path, "JPEG", quality=95)

    # ------------------------------------------------------------------
    # Image fitting (mirrors PdfGenerator logic at preview resolution)
    # ------------------------------------------------------------------

    @staticmethod
    def _fit_tile_to_box(
        cropped: Image.Image,
        box_w: int,
        box_h: int,
        fit_mode: str,
    ) -> Image.Image:
        """Resize a cropped tile to fit inside the preview's printable box.

        Supports the same three modes as the PDF renderer: fit, stretch, cover.
        """

        crop_w, crop_h = cropped.size
        crop_ratio = crop_w / crop_h
        box_ratio = box_w / box_h

        if fit_mode == "stretch":
            return cropped.resize((box_w, box_h), Image.LANCZOS)

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

        # Fit (default): letterbox inside the box.
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

    # ------------------------------------------------------------------
    # Cut-guide overlays
    # ------------------------------------------------------------------

    @staticmethod
    def _draw_cut_guides(
        preview: Image.Image,
        draw: ImageDraw.ImageDraw,
        font: ImageFont.ImageFont,
        x: int,
        y: int,
        width: int,
        height: int,
        page_margin: int,
        tile_row: int,
        tile_col: int,
        total_rows: int,
        total_cols: int,
    ) -> None:
        """Draw dashed borders and scissor marks on the preview image."""

        guide_color = (120, 120, 120)
        mark_color = (90, 90, 90)

        # Dashed rectangle (all four edges).
        PreviewGenerator._draw_dashed_line(
            draw, (x, y), (x + width, y), guide_color, dash=7, gap=5
        )
        PreviewGenerator._draw_dashed_line(
            draw, (x, y), (x, y + height), guide_color, dash=7, gap=5
        )
        PreviewGenerator._draw_dashed_line(
            draw, (x + width, y), (x + width, y + height), guide_color, dash=7, gap=5
        )
        PreviewGenerator._draw_dashed_line(
            draw, (x, y + height), (x + width, y + height), guide_color, dash=7, gap=5
        )

        inset = max(4, int(page_margin / 2))

        # Scissor icon on the right seam (between this tile and the next column).
        if tile_col < total_cols - 1:
            PreviewGenerator._paste_rotated_scissor(
                base_image=preview,
                text="✂",
                center=(x + width + (inset // 2), y + (height // 2)),
                font=font,
                fill=mark_color,
                angle=90,
            )

        # Scissor icon on the bottom seam (between this tile and the next row).
        if tile_row < total_rows - 1:
            PreviewGenerator._paste_rotated_scissor(
                base_image=preview,
                text="✂",
                center=(x + (width // 2), y + height + (inset // 2) + 2),
                font=font,
                fill=mark_color,
                angle=0,
            )

    @staticmethod
    def _paste_rotated_scissor(
        base_image: Image.Image,
        text: str,
        center: tuple[int, int],
        font: ImageFont.ImageFont,
        fill: tuple[int, int, int],
        angle: int,
    ) -> None:
        """Render a text glyph, optionally rotate it, and paste onto the canvas.

        Used for placing scissor icons at arbitrary angles along tile seams.
        """

        bbox = font.getbbox(text)
        glyph_w = max(1, bbox[2] - bbox[0])
        glyph_h = max(1, bbox[3] - bbox[1])

        # Draw the glyph on a small transparent canvas with padding.
        pad = 12
        glyph = Image.new("RGBA", (glyph_w + pad * 2,
                          glyph_h + pad * 2), (255, 255, 255, 0))
        glyph_draw = ImageDraw.Draw(glyph)
        glyph_draw.text(
            (pad - bbox[0], pad - bbox[1]),
            text,
            font=font,
            fill=fill + (255,),
        )

        rotated = glyph.rotate(angle, expand=True)

        # Center-paste the rotated glyph onto the preview image.
        cx, cy = center
        px = int(round(cx - rotated.width / 2))
        py = int(round(cy - rotated.height / 2))

        base_image.paste(rotated, (px, py), rotated)

    @staticmethod
    def _draw_dashed_line(
        draw: ImageDraw.ImageDraw,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
        dash: int = 6,
        gap: int = 4,
    ) -> None:
        """Draw a horizontal or vertical dashed line segment.

        Pillow does not natively support dash patterns, so we manually draw
        short solid segments with gaps in between.
        """

        x1, y1 = start
        x2, y2 = end

        if x1 == x2:
            # Vertical line.
            y = y1
            step = dash + gap
            direction = 1 if y2 >= y1 else -1
            while (y <= y2 if direction == 1 else y >= y2):
                y_end = y + (dash * direction)
                y_end = min(y_end, y2) if direction == 1 else max(y_end, y2)
                draw.line((x1, y, x2, y_end), fill=color, width=1)
                y += step * direction

        elif y1 == y2:
            # Horizontal line.
            x = x1
            step = dash + gap
            direction = 1 if x2 >= x1 else -1
            while (x <= x2 if direction == 1 else x >= x2):
                x_end = x + (dash * direction)
                x_end = min(x_end, x2) if direction == 1 else max(x_end, x2)
                draw.line((x, y1, x_end, y2), fill=color, width=1)
                x += step * direction
        else:
            # Diagonal fallback — just draw a solid line.
            draw.line((x1, y1, x2, y2), fill=color, width=1)
