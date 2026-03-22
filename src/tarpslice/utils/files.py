"""
File and path helper utilities.

Provides validation and normalization for the two user-supplied paths:

- **Source image path** — must exist, be a regular file, and have a supported
  image extension.
- **Output PDF path** — normalized to ``.pdf``, with parent directories created
  automatically if they do not exist.
"""

from __future__ import annotations

from pathlib import Path

from tarpslice.constants import SUPPORTED_IMAGE_EXTENSIONS


def validate_image_path(path_str: str) -> Path:
    """Validate that the given string points to a supported image file.

    Args:
        path_str: Raw path string entered by the user.

    Returns:
        Resolved ``Path`` object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError:        If the path is not a file or the extension is
                           unsupported.
    """

    path = Path(path_str).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        raise ValueError(f"Unsupported image type '{path.suffix}'. Allowed: {allowed}")

    return path


def ensure_output_path(path_str: str) -> Path:
    """Normalize the output PDF path and create parent directories if needed.

    Args:
        path_str: Raw path string entered by the user.

    Returns:
        Resolved ``Path`` with a ``.pdf`` suffix and existing parent directory.
    """

    path = Path(path_str).expanduser().resolve()

    if path.suffix.lower() != ".pdf":
        path = path.with_suffix(".pdf")

    path.parent.mkdir(parents=True, exist_ok=True)
    return path
