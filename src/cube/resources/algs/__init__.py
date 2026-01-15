"""File algorithm resources for the F1-F5 buttons.

Algorithm files are loaded as Python resources so they work when the package
is installed via pip. Files are named f1.txt through f5.txt.

Format:
    - Lines starting with # (after stripping whitespace) are comments
    - Empty lines are ignored
    - All other lines are concatenated with spaces and parsed as algorithms
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path

from cube.domain.algs.Alg import Alg
from cube.domain.algs.Algs import Algs


def load_file_alg(slot: int) -> Alg:
    """Load algorithm from f{slot}.txt resource file.

    Args:
        slot: File number 1-5

    Returns:
        Parsed Alg object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or contains only comments
    """
    filename = f"f{slot}.txt"

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
        raise FileNotFoundError(f"Algorithm file '{filename}' not found")

    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)

    if not lines:
        raise ValueError(f"Algorithm file '{filename}' is empty")

    alg_string = " ".join(lines)
    return Algs.parse(alg_string)
