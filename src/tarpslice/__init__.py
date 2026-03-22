"""
TarpSlice - Tarpapel / Poster PDF Generator.

This is the top-level package for the TarpSlice CLI application.
It exposes a single entry point (``cli.run``) that launches the interactive
terminal wizard.  All internal modules are organized into three sub-packages:

- **models**    – Data classes that carry user settings through the pipeline.
- **services**  – Core business logic (image slicing, PDF rendering, preview).
- **utils**     – Stateless helper functions (unit conversion, file validation).
"""
