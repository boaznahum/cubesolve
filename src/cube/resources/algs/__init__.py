"""File algorithm resources for the F1-F5 buttons.

Algorithm files are loaded as Python resources so they work when the package
is installed via pip. Files are named f1.txt through f5.txt.

Format: See Algs.parse_multiline() for format documentation.
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path

from cube.domain.algs.Alg import Alg
from cube.domain.algs.Algs import Algs


def load_file_content(slot: int) -> str:
    """Load raw content from f{slot}.txt resource file.

    Args:
        slot: File number 1-5

    Returns:
        Raw file content as string

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    filename = f"f{slot}.txt"

    # Try to load as package resource (works when installed via pip)
    content: str | None = None
    try:
        content = resources.files(__package__).joinpath(filename).read_text(encoding='utf-8')
    except (TypeError, FileNotFoundError):
        pass

    # Fallback: try relative to this file (works during development)
    if content is None:
        local_path = Path(__file__).parent / filename
        if local_path.exists():
            content = local_path.read_text(encoding='utf-8')

    if content is None:
        raise FileNotFoundError(f"Algorithm file '{filename}' not found")

    return content


def parse_file_content(content: str, filename: str) -> Alg:
    """Parse raw file content into an algorithm.

    Args:
        content: Raw file content
        filename: For error messages

    Returns:
        Parsed Alg object

    Raises:
        ValueError: If file is empty or contains only comments
    """
    try:
        return Algs.parse_multiline(content)
    except ValueError:
        raise ValueError(f"Algorithm file '{filename}' is empty")
