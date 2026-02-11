"""Scramble seed resources for the F button.

Seed file is loaded as a Python resource so it works when the package
is installed via pip. File is named F.txt.

Format: Plain text file with a single integer seed on the first non-comment line.
Lines starting with # are treated as comments and ignored.
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path


def load_scramble_seed() -> int:
    """Load scramble seed from F.txt resource file.

    Returns:
        Integer seed value

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or doesn't contain valid integer
    """
    filename = "F.txt"

    # Try to load as package resource (works when installed via pip)
    content: str | None = None
    try:
        content = resources.files(__package__).joinpath(filename).read_text()
    except (TypeError, FileNotFoundError):
        pass

    # Fallback: try relative to this file (works during development)
    if content is None:
        local_path = Path(__file__).parent / filename
        if local_path.exists():
            content = local_path.read_text()

    if content is None:
        raise FileNotFoundError(f"Scramble seed file '{filename}' not found")

    # Parse: find first non-empty, non-comment line
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                return int(line)
            except ValueError:
                raise ValueError(f"Invalid seed in '{filename}': '{line}' is not a valid integer")

    raise ValueError(f"Scramble seed file '{filename}' contains no valid seed")
