from __future__ import annotations

import math
import time
from collections.abc import Collection, Set
from typing import TYPE_CHECKING, Iterable, Tuple

import numpy as np
from numpy import ndarray

from cube.application.protocols import AnimatableViewer
from cube.application.state import ApplicationAndViewState
from cube.domain.model._part_slice import PartSlice
from cube.domain.model.Cube import Cube
from cube.domain.model.cube_boy import FaceName
from cube.domain.model.Face import Face
from cube.domain.model.PartEdge import PartEdge

# noinspection PyMethodMayBeStatic
from cube.utils import prof

from ..gui.protocols.Renderer import Renderer
from ..gui.types import DisplayList
from ..gui.ViewSetup import ViewSetup
from ._board import _Board
from ._faceboard import _FaceBoard

if TYPE_CHECKING:
    from cube.application.animation.AnimationManager import Animation
    from cube.domain.algs import AnimationAbleAlg


class GCubeViewer(AnimatableViewer):
    """3D cube viewer using legacy OpenGL (display lists).

    Implements AnimatableViewer protocol for animation support.
    """
    __slots__ = ["_cube", "_board", "_vs", "_renderer"]

    def __init__(
        self,
        cube: Cube,
        vs: ApplicationAndViewState,
        renderer: Renderer | None = None,
    ) -> None:
        super().__init__()
        self._cube = cube
        self._vs = vs
        self._renderer = renderer

        self._board: _Board = _Board(cube, vs, renderer)

        self.reset()

    @property
    def renderer(self) -> Renderer | None:
        """Get the renderer instance."""
        return self._renderer

    @property
    def cube(self) -> Cube:
        """Get the cube instance."""
        return self._cube

    def reset(self):
        """
        Called on cube resize
        :return:
        """
        self._board.reset()

    def cleanup(self):
        """
        Release resources upon exit
        :return:
        """
        self._board.cleanup()

    def update(self):
        """
        Called on any cue change to re-construct graphic elements
        :return:
        """
        with prof.w_prof("GUI update", self._vs.config.viewer_trace_draw_update):
            self._board.update()

    def draw(self):
        """
        Draw the graphic elements that were update in :upate
        :return:
        """
        with prof.w_prof("GUI draw", self._vs.config.viewer_trace_draw_update):
            self._board.draw()

    def _get_face(self, name: FaceName) -> _FaceBoard:
        for f in self._board.faces:
            if f.cube_face.name == name:
                return f

        assert False

    def _get_faces(self, name: FaceName) -> Iterable[_FaceBoard]:

        for f in self._board.faces:
            if f.cube_face.name == name:
                yield f

    def _get_face_gui_objects(self, f: _FaceBoard) -> Iterable[int]:

        lists: set[int] = set()

        this_face_objects = f.gui_objects()
        lists.update(this_face_objects)

        this_cube_face: Face = f.cube_face

        cube_face_adjusts: Iterable[Face] = this_cube_face.adjusted_faces()

        for adjust in cube_face_adjusts:
            adjust_board: _FaceBoard = self._get_face(adjust.name)
            for p in adjust.parts:
                if p.on_face(this_cube_face):
                    p_lists = adjust_board.get_part_gui_object(p)
                    lists.update(p_lists)

        return lists

    def _get_faces_gui_objects(self, fs: Iterable[_FaceBoard]) -> Iterable[int]:

        lists: set[int] = set()

        for f in fs:
            lists.update(self._get_face_gui_objects(f))

        return lists

    def unhidden_all(self):
        self._board.unhidden_all()

    def get_slices_movable_gui_objects(self, face_name_rotate_axis: FaceName,
                                       cube_parts: Collection[PartSlice],
                                       hide=True) -> Tuple[ndarray, ndarray, Iterable[int]]:

        face_name: FaceName = face_name_rotate_axis

        right: _FaceBoard = self._get_face(face_name)
        left: _FaceBoard = self._get_face(self._cube.face(face_name).opposite.name)

        right_center: ndarray = right.get_center()
        # because left,back and down have more than one gui faces
        left_center: ndarray = left.get_center()

        objects: set[int] = set()

        objects.update(self._board.get_all_movable_gui_elements(cube_parts))

        if hide:
            self._board.set_hidden(objects)

        return right_center, left_center, objects

    def find_facet(self, x: float, y: float, z: float) -> Tuple[PartEdge, ndarray, ndarray] | None:

        with prof.w_prof("Locate facet", self._vs.config.prof_viewer_search_facet):
            return self._board.find_facet(x, y, z)

    def create_animation(
        self,
        alg: "AnimationAbleAlg",
        vs: ApplicationAndViewState,
    ) -> "Animation":
        """Create animation for a face rotation algorithm.

        Implements AnimatableViewer protocol. Uses display lists for rendering
        the animated parts.

        Args:
            alg: The algorithm to animate (must implement get_animation_objects)
            vs: Application view state (for speed settings, view transforms)

        Returns:
            Animation object ready for scheduling
        """
        # Import here to avoid circular imports
        from cube.application.animation.AnimationManager import Animation

        renderer = self._renderer
        if renderer is None:
            raise RuntimeError("Renderer is required for animation")

        cube = self._cube
        n_count = alg.n

        # Get the rotated face and parts
        rotate_face, cube_parts = alg.get_animation_objects(cube)

        if not isinstance(cube_parts, Set):
            cube_parts = set(cube_parts)

        # Get face centers and gui objects (display lists)
        face_center, opposite_face_center, gui_objects = self.get_slices_movable_gui_objects(
            rotate_face, cube_parts
        )

        current_angle: float = 0

        # Compute target angle
        n = n_count % 4
        if n == 3:
            n = -1
        target_angle = math.radians(90 * n)
        animation_speed = vs.get_speed
        angle_delta = target_angle / float(animation_speed.number_of_steps) / math.fabs(n)

        # Compute rotation axis transformation matrices
        # Reference: https://www.eng.uc.edu/~beaucag/Classes/Properties/OptionalProjects/
        # CoordinateTransformationCode/Rotate%20about%20an%20arbitrary%20axis%20(3%20dimensions).html
        x1 = face_center[0]
        y1 = face_center[1]
        z1 = face_center[2]
        t: ndarray = np.array([[1, 0, 0, -x1],
                               [0, 1, 0, -y1],
                               [0, 0, 1, -z1],
                               [0, 0, 0, 1]], dtype=float)
        tt = np.linalg.inv(t)
        u = (face_center - opposite_face_center) / np.linalg.norm(face_center - opposite_face_center)
        a = u[0]
        b = u[1]
        c = u[2]
        d = math.sqrt(b * b + c * c)
        if d == 0:
            rx = np.array([[1, 0, 0, 0],
                           [0, 1, 0, 0],
                           [0, 0, 1, 0],
                           [0, 0, 0, 1]], dtype=float)
        else:
            rx = np.array([[1, 0, 0, 0],
                           [0, c / d, -b / d, 0],
                           [0, b / d, c / d, 0],
                           [0, 0, 0, 1]], dtype=float)

        rx_t = np.linalg.inv(rx)
        ry = np.array([[d, 0, -a, 0],
                       [0, 1, 0, 0],
                       [a, 0, d, 0],
                       [0, 0, 0, 1]], dtype=float)
        ry_t = np.linalg.inv(ry)

        # Combined pre/post rotation matrices
        mt: ndarray = tt @ rx_t @ ry_t
        m: ndarray = ry @ rx @ t

        animation = Animation()
        animation.done = False
        animation._animation_cleanup = lambda: self.unhidden_all()

        last_update = time.time()

        def _update() -> bool:
            nonlocal current_angle
            nonlocal last_update

            if (time.time() - last_update) > animation.delay:
                _angle = current_angle + angle_delta

                if abs(_angle) > abs(target_angle):
                    if current_angle < target_angle:
                        current_angle = target_angle
                    else:
                        animation.done = True
                else:
                    current_angle = _angle

                last_update = time.time()
                return True
            else:
                return False

        def _draw() -> None:
            nonlocal current_angle

            if abs(current_angle) > abs(target_angle):
                animation.done = True
                return

            ViewSetup.prepare_objects_view(vs, renderer)

            ct = math.cos(current_angle)
            st = math.sin(current_angle)
            Rz = np.array([[ct, st, 0, 0],
                           [-st, ct, 0, 0],
                           [0, 0, 1, 0],
                           [0, 0, 0, 1]], dtype=float)

            model_view: ndarray = mt @ Rz @ m

            # Apply the animation rotation matrix
            renderer.view.multiply_matrix(model_view)

            try:
                # Use renderer to call display lists
                for f in gui_objects:
                    renderer.display_lists.call_list(DisplayList(f))
            finally:
                ViewSetup.restore_objects_view(renderer)

        animation.delay = animation_speed.delay_between_steps
        animation._animation_draw_only = _draw
        animation._animation_update_only = _update

        return animation
