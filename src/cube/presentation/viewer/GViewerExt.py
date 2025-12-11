import math
from collections.abc import Sequence

import numpy as np

from cube.application.state import ApplicationAndViewState
from cube.presentation.gui.protocols import Renderer


class GViewerExt:
    """
    Some extensions to graphic viewer
    """

    @staticmethod
    def draw_axis(vs: ApplicationAndViewState, renderer: Renderer) -> None:
        """Draw the XYZ axis indicator.

        Args:
            vs: Application view state with offset and rotation angles
            renderer: Renderer to use for drawing
        """
        axis_length = vs.config.axis_length
        line_width = 3.0

        view = renderer.view
        shapes = renderer.shapes

        # Save current matrix state
        view.push_matrix()
        view.load_identity()

        # Apply offset translation
        offset: Sequence[int] = vs.offset
        view.translate(float(offset[0]), float(offset[1]), float(offset[2]))

        # Rotate axes to match current view orientation
        # (so the axis rotates with the cube)
        view.rotate(math.degrees(vs.alpha_x_0), 1, 0, 0)
        view.rotate(math.degrees(vs.alpha_y_0), 0, 1, 0)
        view.rotate(math.degrees(vs.alpha_z_0), 0, 0, 1)

        # Create numpy arrays for line endpoints (Point3D is ndarray)
        origin = np.array([0, 0, 0], dtype=float)
        x_end = np.array([axis_length, 0, 0], dtype=float)
        y_end = np.array([0, axis_length, 0], dtype=float)
        z_end = np.array([0, 0, axis_length], dtype=float)

        # Draw X axis - white
        shapes.line(origin, x_end, line_width, (255, 255, 255))

        # Draw Y axis - red
        shapes.line(origin, y_end, line_width, (255, 0, 0))

        # Draw Z axis - green
        shapes.line(origin, z_end, line_width, (0, 255, 0))

        # Restore matrix state
        view.pop_matrix()
