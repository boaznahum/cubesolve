"""View setup utilities for applying application state to renderer.

This module provides utilities for setting up view transformations
based on ApplicationAndViewState values. It bridges the application
layer (state) with the presentation layer (renderer).

Dependency direction: presentation -> application (correct)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.application.state import ApplicationAndViewState
    from cube.presentation.gui.protocols.Renderer import Renderer


class ViewSetup:
    """Utility class for applying view state to renderer.

    All methods are static - no instance needed.
    """

    @staticmethod
    def prepare_objects_view(vs: ApplicationAndViewState, renderer: Renderer) -> None:
        """Set up the model-view transformation for drawing objects.

        Applies offset translation and rotations based on view state.
        Call restore_objects_view() when done drawing.

        Args:
            vs: Application view state containing rotation and offset values
            renderer: Renderer to use for view transformations
        """
        view = renderer.view

        view.push_matrix()
        view.load_identity()

        o = vs.offset
        view.translate(float(o[0]), float(o[1]), float(o[2]))

        # Apply initial rotation (base orientation)
        view.rotate(math.degrees(vs.alpha_x_0), 1, 0, 0)
        view.rotate(math.degrees(vs.alpha_y_0), 0, 1, 0)
        view.rotate(math.degrees(vs.alpha_z_0), 0, 0, 1)

        # Apply user-controlled rotation (from mouse drag)
        view.rotate(math.degrees(vs.alpha_x), 1, 0, 0)
        view.rotate(math.degrees(vs.alpha_y), 0, 1, 0)
        view.rotate(math.degrees(vs.alpha_z), 0, 0, 1)

    @staticmethod
    def restore_objects_view(renderer: Renderer) -> None:
        """Undo prepare_objects_view - restore previous matrix state.

        Args:
            renderer: Renderer to use for view transformations
        """
        renderer.view.pop_matrix()

    @staticmethod
    def set_projection(vs: ApplicationAndViewState, width: int, height: int,
                       renderer: Renderer) -> None:
        """Set up the projection matrix for the viewport.

        Args:
            vs: Application view state containing fov_y value
            width: Viewport width in pixels
            height: Viewport height in pixels
            renderer: Renderer to use for view transformations
        """
        renderer.view.set_projection(
            width, height,
            fov_y=float(vs.fov_y),
            near=1.0,
            far=1000.0
        )
