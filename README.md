# TarpSlice CLI

A command-line tool that splits any image into a grid of printable pages, producing a ready-to-print multi-page PDF. Print the pages on standard paper, trim along the cut guides, and assemble them into a large poster or tarpaulin (tarpapel).

```
 _____                 ____  _ _             ____ _     ___
|_   _|_ _ _ __ _ __  / ___|| (_) ___ ___   / ___| |   |_ _|
  | |/ _` | '__| '_ \ \___ \| | |/ __/ _ \ | |   | |    | |
  | | (_| | |  | |_) | ___) | | | (_|  __/ | |___| |___ | |
  |_|\__,_|_|  | .__/ |____/|_|_|\___\___|  \____|_____|___|
               |_|
```

**Developer:** Mohammad Aldrin Said
**Version:** 1.0.0
**License:** MIT

---

## Features

- **Multiple paper sizes** — A4, Letter, Legal, Long Bond
- **Orientation** — Portrait or Landscape
- **Flexible grid** — Configure any number of rows and columns
- **Image fit modes** — Fit (preserve ratio), Stretch, or Cover
- **Cut guides** — Dashed lines with scissor icons for precise trimming
- **Tile labels** — "Row X, Col Y" printed on each page for easy assembly
- **Preview image** — Generates a JPEG overview of the assembled poster
- **Interactive wizard** — Step-by-step prompts with go-back support
- **Repeat workflow** — Create multiple tarpapels without restarting

---

## Installation

### Option 1: Download the Executable (Recommended for end users)

1. Go to the [Releases](https://github.com/YzrSaid/tarpslice-cli/releases) page.
2. Download `tarpslice.exe`.
3. Double-click the `.exe` or run it from a terminal:

```bash
.\tarpslice.exe
```

No Python installation required.

### Option 2: Clone and Run from Source (For developers)

**Prerequisites:**
- Python 3.11 or higher
- pip

```bash
# 1. Clone the repository
git clone https://github.com/YzrSaid/tarpslice-cli.git
cd tarpslice-cli

# 2. (Optional) Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install the package in editable mode
pip install -e .

# 5. Run the application
python -m tarpslice
```

---

## Usage

When launched, the tool displays a main menu:

```
[1] Start
[2] What is TarpSlice?
[3] View Source Code / About the Developer
[4] Exit
```

Selecting **Start** walks you through a 10-step wizard:

| Step | Setting         | Description                                                         |
|------|-----------------|---------------------------------------------------------------------|
| 1    | Image path      | Path to the source image (PNG, JPG, JPEG, BMP, WEBP)               |
| 2    | Output PDF path | Where to save the generated PDF (defaults to `<image>_tiled.pdf`)   |
| 3    | Paper size      | A4, Letter, Legal, or Long Bond                                    |
| 4    | Orientation     | Portrait or Landscape                                               |
| 5    | Rows            | Number of vertical tile divisions                                   |
| 6    | Columns         | Number of horizontal tile divisions                                 |
| 7    | Margin          | Blank border on each page (0.25 - 1.00 inch)                       |
| 8    | Fit mode        | Fit (keep ratio), Stretch, or Cover                                 |
| 9    | Cut guides      | Dashed lines + scissor icons for trimming                           |
| 10   | Tile labels     | "Row X, Col Y" text on each page                                   |

Each step supports **go back** to revise previous choices. After generation, you can create another tarpapel without restarting.

### Output

The tool generates two files:
- **`<name>_tiled.pdf`** — Multi-page PDF ready for printing at 100% scale.
- **`<name>_tiled_preview.jpg`** — JPEG overview showing the assembled poster.

> **Print tip:** Always print at **100% scale / actual size** to ensure tiles align correctly.

---

## Project Structure

```
tarpslice-cli/
├── dist/
│   └── tarpslice.exe            # Compiled standalone executable
├── src/
│   └── tarpslice/               # Main application package
│       ├── __init__.py           # Package docstring and metadata
│       ├── __main__.py           # Entry point for `python -m tarpslice`
│       ├── cli.py                # Interactive CLI wizard and main menu
│       ├── constants.py          # Paper sizes, supported formats, defaults
│       ├── models/
│       │   ├── __init__.py       # Sub-package docstring
│       │   └── settings.py       # PaperSize and PrintSettings dataclasses
│       ├── services/
│       │   ├── __init__.py       # Sub-package docstring
│       │   ├── slicer.py         # Image slicing / tile layout engine
│       │   ├── pdf_generator.py  # Multi-page PDF renderer (ReportLab)
│       │   └── preview_generator.py  # JPEG preview assembler (Pillow)
│       └── utils/
│           ├── __init__.py       # Sub-package docstring
│           ├── conversions.py    # mm-to-points unit conversion
│           └── files.py          # Path validation and normalization
├── .gitignore
├── pyproject.toml                # Build configuration and dependencies
├── requirements.txt              # Pinned dependency versions
├── tarpslice.spec                # PyInstaller build spec
└── README.md
```

---

## Building the Executable

To compile the project into a standalone `.exe`:

```bash
pip install pyinstaller
python -m PyInstaller --onefile --console --name tarpslice --paths src src/tarpslice/__main__.py
```

The output will be at `dist/tarpslice.exe`.

---

## Dependencies

| Package      | Version | Purpose                        |
|--------------|---------|--------------------------------|
| Pillow       | 11.1.0  | Image loading and manipulation |
| ReportLab    | 4.2.5   | PDF generation                 |
| PyInstaller  | *       | Executable packaging (dev)     |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## Acknowledgments

Built with [Pillow](https://python-pillow.org/) and [ReportLab](https://www.reportlab.com/).
