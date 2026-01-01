# answer all the geometric questions of the cube
# see issue #55 https://github.com/boaznahum/cubesolve/issues/55#issue-3765157931

from typing import Mapping

from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.model.cube_layout.cube_layout import CubeLayout
from cube.domain.model.cube_layout._CubeLayout import _CubeLayout
from cube.utils.config_protocol import IServiceProvider


def create_layout(
    read_only: bool,
    faces: Mapping[FaceName, Color],
    sp: IServiceProvider
) -> CubeLayout:
    """Create a CubeLayout from face-color mapping.

    Factory function to create layout instances without exposing
    the private implementation class.

    Args:
        read_only: If True, layout cannot be modified (used for singletons).
        faces: Mapping of each face to its color.
        sp: Service provider for configuration access.

    Returns:
        CubeLayout instance with the given configuration.
    """
    return _CubeLayout(read_only, faces, sp)


__all__ = [
    'CubeLayout',
    'create_layout',
]
