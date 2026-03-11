"""Version information for the cube application, read from resource file."""

import importlib.resources as pkg_resources

import cube.resources as res


def get_version() -> str:
    """Read the application version from the resources/version.txt file."""
    return pkg_resources.read_text(res, "version.txt").strip()
