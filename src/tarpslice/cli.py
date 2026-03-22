"""Interactive CLI entry point.

This module handles all user prompts, input validation, and orchestration.
"""

from __future__ import annotations

import os
import webbrowser
from pathlib import Path

from PIL import Image

from tarpslice.constants import DEFAULT_OVERLAP_MM, PAPER_SIZES_MM
from tarpslice.models.settings import PaperSize, PrintSettings
from tarpslice.services.pdf_generator import PdfGenerator
from tarpslice.services.preview_generator import PreviewGenerator
from tarpslice.services.slicer import ImageSlicer
from tarpslice.utils.files import ensure_output_path, validate_image_path

VERSION = "v1.0.0"
GITHUB_URL = "https://github.com/YzrSaid/tarpslice-cli"

BANNER = r"""
 _____                 ____  _ _             ____ _     ___
|_   _|_ _ _ __ _ __  / ___|| (_) ___ ___   / ___| |   |_ _|
  | |/ _` | '__| '_ \ \___ \| | |/ __/ _ \ | |   | |    | |
  | | (_| | |  | |_) | ___) | | | (_|  __/ | |___| |___ | |
  |_|\__,_|_|  | .__/ |____/|_|_|\___\___|  \____|_____|___|
               |_|
"""


def _clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _show_banner() -> None:
    _clear_screen()
    print(BANNER)
    print(f"  Developer: Mohammad Aldrin Said")
    print(f"  Version:   {VERSION}")
    print("=" * 56)


def run() -> None:
    """Run the interactive CLI application."""
    while True:
        _show_banner()
        print("\n  [1] Start")
        print("  [2] What is TarpSlice?")
        print("  [3] View Source Code / About the Developer")
        print("  [4] Exit")

        choice = input("\n  Select an option: ").strip()

        if choice == "1":
            _start_workflow()
        elif choice == "2":
            _show_what_is_tarpslice()
        elif choice == "3":
            _show_about()
        elif choice == "4":
            _show_banner()
            print("\n  Thank you for using TarpSlice CLI! Goodbye.\n")
            break
        else:
            input("\n  Invalid option. Press Enter to try again...")


def _show_what_is_tarpslice() -> None:
    _show_banner()
    print("\n  What is TarpSlice?")
    print("  " + "-" * 40)
    print("  TarpSlice CLI is a command-line tool that splits any image")
    print("  into a grid of printable pages (tarpapel / poster tiles).")
    print("  You can then print each page on standard paper and assemble")
    print("  them together to create a large poster or tarpaulin.")
    print()
    print("  Features:")
    print("  - Supports A4, Letter, Legal, and Long Bond paper sizes")
    print("  - Portrait or Landscape orientation")
    print("  - Configurable rows, columns, and margins")
    print("  - Optional cut guides and tile labels")
    print("  - Multiple image fit modes (fit, stretch, cover)")
    print("  - Outputs a ready-to-print PDF and a preview image")
    input("\n  Press Enter to go back...")


def _show_about() -> None:
    _show_banner()
    print("\n  About the Developer")
    print("  " + "-" * 40)
    print("  Mohammad Aldrin Said")
    print(f"  GitHub: {GITHUB_URL}")
    print()
    print("  [1] Open GitHub repository in browser")
    print("  [2] Go back")

    choice = input("\n  Select an option: ").strip()
    if choice == "1":
        webbrowser.open(GITHUB_URL)
        input("\n  Opening browser... Press Enter to go back...")


def _start_workflow() -> None:
    """Main tarpapel creation workflow with go-back support."""
    while True:
        try:
            settings = _prompt_settings_wizard()
            if settings is None:
                return  # User went back to main menu

            _show_banner()
            print("\n  Generating PDF and preview... Please wait.\n")
            _generate_outputs(settings)

            print("\n  Done!")
            print(f"  Output saved to: {settings.output_pdf_path}")
            print("  Print tip: use 100%% scale / actual size.")

        except KeyboardInterrupt:
            print("\n\n  Cancelled by user.")
        except Exception as exc:
            print(f"\n  Error: {exc}")

        print()
        again = input("  Create another tarpapel? [Y/n]: ").strip().lower()
        if again in ("n", "no"):
            return


# ---------------------------------------------------------------------------
# Step-by-step wizard with go-back
# ---------------------------------------------------------------------------

_BACK = "__BACK__"


def _prompt_settings_wizard() -> PrintSettings | None:
    """Walk through each setting step. Returns None if user goes back to menu."""

    steps = [
        ("image_path", _step_image_path),
        ("output_pdf_path", _step_output_path),
        ("paper", _step_paper_size),
        ("orientation", _step_orientation),
        ("rows", _step_rows),
        ("cols", _step_cols),
        ("margin_mm", _step_margin),
        ("fit_mode", _step_fit_mode),
        ("draw_cut_guides", _step_cut_guides),
        ("draw_labels", _step_labels),
    ]

    values: dict[str, object] = {}
    i = 0

    while i < len(steps):
        key, step_fn = steps[i]
        result = step_fn(values)

        if result is _BACK:
            if i == 0:
                return None  # Go back to main menu
            i -= 1
            continue

        values[key] = result
        i += 1

    return PrintSettings(
        image_path=str(values["image_path"]),
        output_pdf_path=str(values["output_pdf_path"]),
        paper=values["paper"],
        orientation=values["orientation"],
        rows=values["rows"],
        cols=values["cols"],
        margin_mm=values["margin_mm"],
        overlap_mm=DEFAULT_OVERLAP_MM,
        draw_cut_guides=values["draw_cut_guides"],
        draw_labels=values["draw_labels"],
        fit_mode=values["fit_mode"],
    )


def _step_image_path(_values: dict) -> Path | str:
    _show_banner()
    print("\n  Step 1: Select Image")
    print("  " + "-" * 40)
    print("  Provide the path to the image you want to split into")
    print("  printable poster tiles. Supported formats: PNG, JPG, JPEG, BMP, WEBP.")
    print()
    print("  Type 'back' to return to the main menu.")
    print()

    while True:
        raw = input("  Enter image path: ").strip().strip('"')
        if raw.lower() == "back":
            return _BACK
        try:
            return validate_image_path(raw)
        except Exception as exc:
            print(f"  Invalid image path: {exc}\n")


def _step_output_path(values: dict) -> Path | str:
    _show_banner()
    image_path = values["image_path"]
    default_name = image_path.with_name(f"{image_path.stem}_tiled.pdf")
    print("\n  Step 2: Output PDF Path")
    print("  " + "-" * 40)
    print("  Choose where to save the generated PDF.")
    print(f"  Press Enter to use the default: {default_name}")
    print()
    print("  Type 'back' to go to the previous step.")
    print()

    raw = input("  Output PDF path: ").strip().strip('"')
    if raw.lower() == "back":
        return _BACK
    raw = raw or str(default_name)
    return ensure_output_path(raw)


def _step_paper_size(_values: dict) -> PaperSize | str:
    _show_banner()
    options = list(PAPER_SIZES_MM.items())
    print("\n  Step 3: Select Paper Size")
    print("  " + "-" * 40)
    print("  Choose the paper size that matches your printer.")
    print("  This determines the physical dimensions of each printed page.")
    print()
    for index, (name, dims) in enumerate(options, start=1):
        print(f"  [{index}] {name.title().replace('_', ' ')} - {dims[0]}mm x {dims[1]}mm")
    print(f"  [0] Go back")
    print()

    while True:
        choice = input("  Choice [1]: ").strip() or "1"
        if choice == "0":
            return _BACK
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            name, (width_mm, height_mm) = options[int(choice) - 1]
            return PaperSize(name=name, width_mm=width_mm, height_mm=height_mm)
        print("  Please enter a valid option.\n")


def _step_orientation(_values: dict) -> str:
    _show_banner()
    print("\n  Step 4: Select Orientation")
    print("  " + "-" * 40)
    print("  Portrait  = taller than wide (standard document layout).")
    print("  Landscape = wider than tall (good for wide images).")
    print()
    print("  [1] Portrait")
    print("  [2] Landscape")
    print("  [0] Go back")
    print()

    while True:
        choice = input("  Choice [1]: ").strip() or "1"
        if choice == "0":
            return _BACK
        if choice == "1":
            return "portrait"
        if choice == "2":
            return "landscape"
        print("  Please enter 1 or 2.\n")


def _step_rows(_values: dict) -> int | str:
    _show_banner()
    print("\n  Step 5: Number of Rows")
    print("  " + "-" * 40)
    print("  How many rows of pages should the poster have?")
    print("  For example, 2 rows means the image is split into 2 vertical sections.")
    print("  More rows = taller poster.")
    print()
    print("  Type 'back' to go to the previous step.")
    print()

    while True:
        raw = input("  Enter number of rows [2]: ").strip() or "2"
        if raw.lower() == "back":
            return _BACK
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        print("  Please enter a whole number greater than zero.\n")


def _step_cols(_values: dict) -> int | str:
    _show_banner()
    print("\n  Step 6: Number of Columns")
    print("  " + "-" * 40)
    print("  How many columns of pages should the poster have?")
    print("  For example, 2 columns means the image is split into 2 horizontal sections.")
    print("  More columns = wider poster.")
    print()
    print("  Type 'back' to go to the previous step.")
    print()

    while True:
        raw = input("  Enter number of columns [2]: ").strip() or "2"
        if raw.lower() == "back":
            return _BACK
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        print("  Please enter a whole number greater than zero.\n")


def _step_margin(_values: dict) -> float | str:
    _show_banner()
    inch_to_mm = 25.4
    options = [
        ("0.25 inch", 0.25 * inch_to_mm),
        ("0.50 inch", 0.50 * inch_to_mm),
        ("0.75 inch", 0.75 * inch_to_mm),
        ("1.00 inch", 1.00 * inch_to_mm),
    ]

    print("\n  Step 7: Select Margin")
    print("  " + "-" * 40)
    print("  The margin is the blank border around each printed page.")
    print("  A smaller margin gives you more printable area per page.")
    print("  Most printers need at least 0.25 inch margin.")
    print()
    for index, (label, value_mm) in enumerate(options, start=1):
        print(f"  [{index}] {label} ({value_mm:.2f} mm)")
    print("  [0] Go back")
    print()

    while True:
        choice = input("  Choice [1]: ").strip() or "1"
        if choice == "0":
            return _BACK
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1][1]
        print("  Please enter a valid option.\n")


def _step_fit_mode(_values: dict) -> str:
    _show_banner()
    print("\n  Step 8: Image Fit Mode")
    print("  " + "-" * 40)
    print("  Determines how the image fills each tile:")
    print("  - Fit:     Keeps the original aspect ratio; may leave white space.")
    print("  - Stretch: Stretches the image to fill the tile (may distort).")
    print("  - Cover:   Crops the image to fill the tile with no white space.")
    print()
    print("  [1] Fit and keep ratio")
    print("  [2] Fit and stretch")
    print("  [3] Cover page")
    print("  [0] Go back")
    print()

    while True:
        choice = input("  Choice [1]: ").strip() or "1"
        if choice == "0":
            return _BACK
        if choice == "1":
            return "fit"
        if choice == "2":
            return "stretch"
        if choice == "3":
            return "cover"
        print("  Please enter 1, 2, or 3.\n")


def _step_cut_guides(_values: dict) -> bool | str:
    _show_banner()
    print("\n  Step 9: Cut Guides")
    print("  " + "-" * 40)
    print("  Cut guides are dashed lines and scissor icons printed along")
    print("  the edges of each tile. They show you exactly where to cut")
    print("  and trim each page so the tiles align perfectly when assembled.")
    print()
    print("  Type 'back' to go to the previous step.")
    print()

    while True:
        raw = input("  Add cut guides? [Y/n]: ").strip().lower()
        if raw == "back":
            return _BACK
        if not raw or raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  Please answer with y, n, or 'back'.\n")


def _step_labels(_values: dict) -> bool | str:
    _show_banner()
    print("\n  Step 10: Tile Labels")
    print("  " + "-" * 40)
    print("  Tile labels print a small 'Row X, Col Y' text at the bottom")
    print("  of each page. This helps you identify which tile goes where")
    print("  when assembling the poster.")
    print()
    print("  Type 'back' to go to the previous step.")
    print()

    while True:
        raw = input("  Add tile labels? [Y/n]: ").strip().lower()
        if raw == "back":
            return _BACK
        if not raw or raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  Please answer with y, n, or 'back'.\n")


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def _generate_outputs(settings: PrintSettings) -> None:
    image = Image.open(settings.image_path).convert("RGB")

    page_width_mm, page_height_mm = _resolved_page_dimensions_mm(settings)
    printable_width_mm = page_width_mm - (2 * settings.margin_mm)
    printable_height_mm = page_height_mm - (2 * settings.margin_mm)

    if printable_width_mm <= 0 or printable_height_mm <= 0:
        raise ValueError("Margins are too large for the selected paper size.")

    printable_width_px = int(round(printable_width_mm * 10))
    printable_height_px = int(round(printable_height_mm * 10))
    overlap_px = int(round(settings.overlap_mm * 10))

    slicer = ImageSlicer()
    layout = slicer.build_layout(
        image=image,
        rows=settings.rows,
        cols=settings.cols,
        printable_width_px=printable_width_px,
        printable_height_px=printable_height_px,
        overlap_px=overlap_px,
    )

    pdf_generator = PdfGenerator()
    pdf_generator.generate(image=image, layout=layout, settings=settings)

    preview_path = str(Path(settings.output_pdf_path).with_name(
        f"{Path(settings.output_pdf_path).stem}_preview.jpg"
    ))

    preview_generator = PreviewGenerator()
    preview_generator.generate(
        image=image,
        layout=layout,
        settings=settings,
        output_path=preview_path,
    )

    print(f"  Preview saved to: {preview_path}")


def _resolved_page_dimensions_mm(settings: PrintSettings) -> tuple[float, float]:
    if settings.orientation == "portrait":
        return settings.paper.width_mm, settings.paper.height_mm
    return settings.paper.height_mm, settings.paper.width_mm
