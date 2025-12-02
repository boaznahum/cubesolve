"""Face texture resources for cube visualization."""
from importlib import resources
from pathlib import Path


def get_texture_set_path(set_name: str) -> Path | None:
    """Get the path to a built-in texture set.

    Args:
        set_name: Name of texture set (e.g., 'set1', 'boaz', 'family')

    Returns:
        Path to texture directory, or None if not found
    """
    try:
        # Python 3.9+ style
        with resources.as_file(resources.files(__package__) / set_name) as path:
            if path.exists() and path.is_dir():
                return path
    except (TypeError, FileNotFoundError):
        pass

    # Fallback: try relative to this file
    local_path = Path(__file__).parent / set_name
    if local_path.exists() and local_path.is_dir():
        return local_path

    return None


def list_texture_sets() -> list[str]:
    """List available built-in texture sets.

    Returns:
        List of texture set names
    """
    sets = []
    base_path = Path(__file__).parent
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            # Check if it has face images
            if any((item / f"{face}.png").exists() for face in ['F', 'B', 'R', 'L', 'U', 'D']):
                sets.append(item.name)
    return sorted(sets)
