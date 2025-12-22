"""
Modern OpenGL Cube Viewer for pyglet2 backend.

This viewer renders a Rubik's cube using modern OpenGL (shaders, VBOs)
instead of legacy immediate mode rendering.

Architecture:
    ModernGLCubeViewer (this class)
        └── ModernGLBoard (_modern_gl_board.py)
            └── ModernGLFace (_modern_gl_face.py)
                └── ModernGLCell (_modern_gl_cell.py)

    This mirrors the legacy architecture:
    GCubeViewer → _Board → _FaceBoard → _Cell

Coordinate System (OpenGL right-handed):
    +Y (Up)
    |
    |   +Z (Front, toward viewer)
    |  /
    | /
    +------ +X (Right)

Face Layout:
           +-------+
           |   U   |
           |  +Y   |
       +---+---+---+---+
       | L | F | R | B |
       |-X |+Z |+X |-Z |
       +---+---+---+---+
           |   D   |
           |  -Y   |
           +-------+

Animation Support:
    This viewer supports smooth face rotation animation:
    1. AnimationManager calls viewer.create_animation() to create animation
    2. Animated cells are marked and separated from static cells
    3. draw() renders static cells normally
    4. Animation's _draw() calls draw_animated() for rotating parts
    5. unhidden_all() ends the animation and clears the state
"""
from __future__ import annotations

import math
import time
from collections.abc import Collection, Iterable, Set
from typing import TYPE_CHECKING, Tuple

import numpy as np
from numpy import ndarray

from cube.application.protocols import AnimatableViewer
from cube.domain.model._part_slice import PartSlice
from cube.domain.model.cube_boy import Color, FaceName
from cube.domain.model.CubeListener import CubeListener

from ._modern_gl_board import ModernGLBoard
from ._modern_gl_constants import (
    BORDER_LINE_WIDTH,
    CELL_DEBUG_KEY,
    CELL_TEXTURE_KEY,
    COLOR_TO_HOME_FACE,
    FACE_TRANSFORMS,
    HALF_CUBE_SIZE,
)

if TYPE_CHECKING:
    from cube.application.animation.AnimationManager import Animation
    from cube.application.state import ApplicationAndViewState
    from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
    from cube.domain.model.Cube import Cube
    from cube.presentation.gui.backends.pyglet2.ModernGLRenderer import ModernGLRenderer


class ModernGLCubeViewer(AnimatableViewer, CubeListener):
    """Renders a Rubik's cube using modern OpenGL (shaders, VBOs).

    Implements AnimatableViewer protocol for animation support.
    Implements CubeListener protocol to reload textures on cube reset.

    This viewer delegates geometry generation to ModernGLBoard,
    which manages the face/cell hierarchy.
    """

    def __init__(
        self,
        cube: "Cube",
        renderer: "ModernGLRenderer",
        vs: "ApplicationAndViewState",
    ) -> None:
        """Initialize the cube viewer.

        Args:
            cube: The cube model to render
            renderer: The modern GL renderer to use
            vs: Application view state (for shadow mode and debug support)
        """
        self._cube = cube
        self._renderer = renderer
        self._vs = vs

        # Board manages all face/cell geometry (like legacy _Board)
        self._board = ModernGLBoard(cube, vs)

        # Cached vertex data
        self._face_triangles: np.ndarray | None = None
        self._line_data: np.ndarray | None = None

        # Per-color geometry for textured rendering
        self._triangles_per_color: dict[Color, np.ndarray] = {}

        # Animation state
        self._animated_face_triangles: np.ndarray | None = None
        self._animated_line_data: np.ndarray | None = None
        self._animated_parts: set[PartSlice] | None = None
        self._animation_face_center: ndarray | None = None
        self._animation_opposite_center: ndarray | None = None
        self._animated_triangles_per_color: dict[Color, np.ndarray] = {}

        # Texture mode state
        self._texture_mode: bool = False
        self._face_textures: dict[FaceName, int] = {}
        self._textures_enabled: bool = True  # Master switch for all texture rendering

        # Per-cell texture mode (new system: textures stored in c_attributes)
        self._use_per_cell_textures: bool = False
        self._cell_textures: list[int] = []  # All cell texture handles for cleanup
        self._texture_directory: str | None = None  # For reload on reset/resize
        self._triangles_per_texture: dict[int | None, np.ndarray] = {}
        self._animated_triangles_per_texture: dict[int | None, np.ndarray] = {}

        # Dirty flag for geometry rebuild
        self._dirty = True

        # Debug counter
        self._debug_rebuild_count = 0

    # =========================================================================
    # Public Interface
    # =========================================================================

    def update(self) -> None:
        """Mark the viewer as needing update.

        Call this when cube state changes.
        """
        self._dirty = True

    def cleanup(self) -> None:
        """Clean up resources. Called on exit."""
        # No resources to clean up - VBOs are recreated each frame
        pass

    def reset(self) -> None:
        """Reset the viewer. Called on cube resize."""
        self._dirty = True

    def on_reset(self) -> None:
        """Called when cube is reset to solved state (CubeListener protocol).

        Reloads textures immediately while cube is in solved state,
        ensuring textures are assigned to correct sticker positions
        before any scramble or moves occur.
        """
        self._dirty = True
        # Reload textures now (cube is in solved state, before scramble)
        if self._use_per_cell_textures and self._texture_directory:
            self.load_texture_set_per_cell(self._texture_directory)

    def set_texture_directory(self, directory: str | None) -> None:
        """Set the texture directory without loading.

        Use this before cube.reset() to change texture sets.
        The on_reset() listener will load from the new directory.
        """
        self._texture_directory = directory
        if directory:
            self._use_per_cell_textures = True

    def _textures_need_reload(self) -> bool:
        """Check if textures need to be reloaded.

        Returns True if per-cell textures were loaded but c_attributes
        no longer contain texture handles (e.g., after cube reset).
        todo:boaz:what a waste of time !!!
        """
        # Check first PartEdge to see if texture is still there
        for part_slice in self._cube.get_all_parts():
            for edge in part_slice.edges:
                # If any edge should have texture but doesn't, need reload
                return CELL_TEXTURE_KEY not in edge.c_attributes
        return False

    def _debug_texture(self, *args) -> None:
        """Debug print for texture operations, controlled by debug_texture config."""
        self._vs.debug(self._cube.config.debug_texture, *args)

    def _debug_texture_lazy(self, func) -> None:
        """Debug print with lazy evaluation for expensive texture debug info."""
        self._vs.debug_lazy(self._cube.config.debug_texture, func)

    @property
    def renderer(self) -> "ModernGLRenderer":
        """Get the renderer instance."""
        return self._renderer

    @property
    def cube(self) -> "Cube":
        """Get the cube instance."""
        return self._cube

    # =========================================================================
    # Drawing
    # =========================================================================

    def draw(self) -> None:
        """Draw the cube.

        Rebuilds geometry if cube state changed, then renders with lighting.
        """
        if self._dirty:
            self._rebuild_geometry()
            self._dirty = False

        # Draw filled faces with lighting
        if self._textures_enabled and self._use_per_cell_textures:
            # Per-cell texture mode: each cell has its own texture from c_attributes
            for texture_handle, triangles in self._triangles_per_texture.items():
                if len(triangles) > 0:
                    self._renderer.draw_textured_lit_triangles(triangles, texture_handle)
        elif self._textures_enabled and self._texture_mode:
            # Old textured mode: draw each color group with its face texture
            for color, triangles in self._triangles_per_color.items():
                if len(triangles) > 0:
                    home_face = COLOR_TO_HOME_FACE.get(color)
                    texture_handle = self._face_textures.get(home_face) if home_face else None
                    self._renderer.draw_textured_lit_triangles(triangles, texture_handle)
        else:
            # Solid color mode (or textures disabled)
            if self._face_triangles is not None and len(self._face_triangles) > 0:
                self._renderer.draw_lit_triangles(self._face_triangles)

        # Draw grid lines
        if self._line_data is not None and len(self._line_data) > 0:
            self._renderer.draw_colored_lines(self._line_data, line_width=BORDER_LINE_WIDTH)

    def draw_animated(self, model_view: ndarray) -> None:
        """Draw animated parts with the given model-view matrix.

        Called by the animation system to render rotating parts.

        Args:
            model_view: The 4x4 rotation matrix to apply
        """
        # Check for animated geometry (considering texture enabled state)
        use_per_cell = self._textures_enabled and self._use_per_cell_textures
        use_old_tex = self._textures_enabled and self._texture_mode
        has_animated_geometry = (
            (use_per_cell and len(self._animated_triangles_per_texture) > 0) or
            (not use_per_cell and not use_old_tex
             and self._animated_face_triangles is not None
             and len(self._animated_face_triangles) > 0) or
            (not use_per_cell and use_old_tex
             and len(self._animated_triangles_per_color) > 0)
        )
        if not has_animated_geometry:
            return

        self._renderer.push_matrix()
        self._renderer.multiply_matrix(model_view)

        if use_per_cell:
            # Per-cell texture mode
            for texture_handle, triangles in self._animated_triangles_per_texture.items():
                if len(triangles) > 0:
                    self._renderer.draw_textured_lit_triangles(triangles, texture_handle)
        elif use_old_tex:
            # Old textured mode
            for color, triangles in self._animated_triangles_per_color.items():
                if len(triangles) > 0:
                    home_face = COLOR_TO_HOME_FACE.get(color)
                    texture_handle = self._face_textures.get(home_face) if home_face else None
                    self._renderer.draw_textured_lit_triangles(triangles, texture_handle)
        else:
            # Solid color mode (or textures disabled)
            if self._animated_face_triangles is not None:
                self._renderer.draw_lit_triangles(self._animated_face_triangles)

        if self._animated_line_data is not None and len(self._animated_line_data) > 0:
            self._renderer.draw_colored_lines(self._animated_line_data, line_width=BORDER_LINE_WIDTH)

        self._renderer.pop_matrix()

    def _rebuild_geometry(self) -> None:
        """Rebuild all geometry from current cube state.

        Delegates to ModernGLBoard for geometry generation.
        Textures are reloaded via CubeListener.on_reset() when cube resets.
        """
        # Debug texture state before rebuild (lazy to avoid cost when debug off)
        if self._use_per_cell_textures:
            self._debug_rebuild_count += 1
            self._debug_texture(f"\n=== _rebuild_geometry #{self._debug_rebuild_count} ===")
            self._debug_texture(f"  animated_parts: {self._animated_parts is not None}")
            self._debug_texture_lazy(lambda: self._format_texture_state("BEFORE board.update()"))

        # Note: Textures are now reloaded proactively via CubeListener.on_reset()
        # No need for lazy _textures_need_reload() check here

        # Update board with current cube state
        self._board.update()

        # Debug texture state after board update
        if self._use_per_cell_textures:
            self._debug_texture_lazy(lambda: self._format_texture_state("AFTER board.update()"))
            self._debug_texture_lazy(lambda: self._format_cell_texture_state())

        # Generate geometry (board separates static/animated)
        # Consider _textures_enabled master switch when deciding which geometry to build
        use_per_cell = self._textures_enabled and self._use_per_cell_textures
        use_old_tex = self._textures_enabled and self._texture_mode

        if use_per_cell:
            # Per-cell texture mode: group by texture handle from c_attributes
            (
                self._triangles_per_texture,
                self._line_data,
                self._animated_triangles_per_texture,
                self._animated_line_data,
            ) = self._board.generate_per_cell_textured_geometry(self._animated_parts)
            self._face_triangles = None
            self._animated_face_triangles = None
            self._triangles_per_color.clear()
            self._animated_triangles_per_color.clear()

            # Debug texture handles used in geometry
            self._debug_texture_lazy(lambda: self._format_geometry_debug())
        elif use_old_tex:
            (
                self._triangles_per_color,
                self._line_data,
                self._animated_triangles_per_color,
                self._animated_line_data,
            ) = self._board.generate_textured_geometry(self._animated_parts)
            self._face_triangles = None
            self._animated_face_triangles = None
            self._triangles_per_texture.clear()
            self._animated_triangles_per_texture.clear()
        else:
            # Solid color mode (or textures disabled)
            (
                self._face_triangles,
                self._line_data,
                self._animated_face_triangles,
                self._animated_line_data,
            ) = self._board.generate_geometry(self._animated_parts)
            self._triangles_per_color.clear()
            self._animated_triangles_per_color.clear()
            self._triangles_per_texture.clear()
            self._animated_triangles_per_texture.clear()

    # =========================================================================
    # Animation Interface (AnimatableViewer protocol)
    # =========================================================================

    def get_slices_movable_gui_objects(
        self,
        face_name_rotate_axis: FaceName,
        cube_parts: Collection[PartSlice],
        hide: bool = True,
    ) -> Tuple[ndarray, ndarray, Iterable[int]]:
        """Get animation data for a set of parts.

        Args:
            face_name_rotate_axis: The face determining the rotation axis
            cube_parts: The parts being rotated
            hide: If True, mark these parts for separate animation rendering

        Returns:
            Tuple of (face_center, opposite_center, gui_objects)
        """
        face = self._cube.face(face_name_rotate_axis)
        opposite = face.opposite

        face_center = self._board.get_face_center(face_name_rotate_axis)
        opposite_center = self._board.get_face_center(opposite.name)

        if hide:
            if not isinstance(cube_parts, set):
                cube_parts = set(cube_parts)
            self._animated_parts = cube_parts
            self._animation_face_center = face_center
            self._animation_opposite_center = opposite_center
            self._dirty = True

        return face_center, opposite_center, []

    def unhidden_all(self) -> None:
        """End animation and restore normal rendering."""
        # Debug texture state before cleanup
        if self._use_per_cell_textures:
            self._debug_texture("\n=== unhidden_all() called ===")
            self._debug_texture_lazy(lambda: self._format_texture_state("BEFORE unhidden_all clears state"))

        self._animated_parts = None
        self._animation_face_center = None
        self._animation_opposite_center = None
        self._animated_face_triangles = None
        self._animated_line_data = None
        self._animated_triangles_per_color.clear()
        self._animated_triangles_per_texture.clear()  # BUG FIX: was missing for per-cell textures!
        self._dirty = True

    def is_animating(self) -> bool:
        """Check if animation is active."""
        return self._animated_parts is not None

    def create_animation(
        self,
        alg: "AnimationAbleAlg",
        vs: "ApplicationAndViewState",
    ) -> "Animation":
        """Create animation for a face rotation algorithm.

        Implements AnimatableViewer protocol.

        Args:
            alg: The algorithm to animate
            vs: Application view state

        Returns:
            Animation object ready for scheduling
        """
        from cube.application.animation.AnimationManager import Animation

        cube = self._cube
        n_count = alg.n

        # Get the rotated face and parts
        rotate_face, cube_parts = alg.get_animation_objects(cube)

        if not isinstance(cube_parts, Set):
            cube_parts = set(cube_parts)

        # Set up animation
        face_center, opposite_face_center, _ = self.get_slices_movable_gui_objects(
            rotate_face, cube_parts
        )

        # Compute rotation parameters
        current_angle: float = 0
        n = n_count % 4
        if n == 3:
            n = -1
        target_angle = math.radians(90 * n)
        animation_speed = vs.get_speed
        angle_delta = target_angle / float(animation_speed.number_of_steps) / math.fabs(n)

        # Compute rotation axis transformation matrices
        # Reference: Rotate about an arbitrary axis (3D)
        # https://www.eng.uc.edu/~beaucag/Classes/Properties/OptionalProjects/
        # CoordinateTransformationCode/Rotate%20about%20an%20arbitrary%20axis%20(3%20dimensions).html
        mt, m = self._compute_rotation_matrices(face_center, opposite_face_center)

        animation = Animation()
        animation.done = False
        animation._animation_cleanup = lambda: self.unhidden_all()

        last_update = time.time()

        def _update() -> bool:
            nonlocal current_angle, last_update
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
            return False

        def _draw() -> None:
            nonlocal current_angle
            if abs(current_angle) > abs(target_angle):
                animation.done = True
                return

            ct = math.cos(current_angle)
            st = math.sin(current_angle)
            Rz = np.array([
                [ct, st, 0, 0],
                [-st, ct, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ], dtype=float)

            model_view: ndarray = mt @ Rz @ m
            self.draw_animated(model_view)

        animation.delay = animation_speed.delay_between_steps
        animation._animation_draw_only = _draw
        animation._animation_update_only = _update

        return animation

    def _compute_rotation_matrices(
        self,
        face_center: ndarray,
        opposite_center: ndarray,
    ) -> tuple[ndarray, ndarray]:
        """Compute transformation matrices for rotation about arbitrary axis.

        Args:
            face_center: Center of the rotating face
            opposite_center: Center of the opposite face (defines axis)

        Returns:
            Tuple of (mt, m) matrices for rotation transform
        """
        x1, y1, z1 = face_center[0], face_center[1], face_center[2]

        # Translation to origin
        t: ndarray = np.array([
            [1, 0, 0, -x1],
            [0, 1, 0, -y1],
            [0, 0, 1, -z1],
            [0, 0, 0, 1]
        ], dtype=float)
        tt = np.linalg.inv(t)

        # Rotation axis (unit vector)
        u = (face_center - opposite_center) / np.linalg.norm(face_center - opposite_center)
        a, b, c = u[0], u[1], u[2]
        d = math.sqrt(b * b + c * c)

        # Rotation to align axis with Z
        if d == 0:
            rx = np.eye(4, dtype=float)
        else:
            rx = np.array([
                [1, 0, 0, 0],
                [0, c / d, -b / d, 0],
                [0, b / d, c / d, 0],
                [0, 0, 0, 1]
            ], dtype=float)

        rx_t = np.linalg.inv(rx)
        ry = np.array([
            [d, 0, -a, 0],
            [0, 1, 0, 0],
            [a, 0, d, 0],
            [0, 0, 0, 1]
        ], dtype=float)
        ry_t = np.linalg.inv(ry)

        # Combined transforms
        mt: ndarray = tt @ rx_t @ ry_t
        m: ndarray = ry @ rx @ t

        return mt, m

    # =========================================================================
    # Texture Mode
    # =========================================================================

    @property
    def texture_mode(self) -> bool:
        """Check if texture mode is enabled."""
        return self._texture_mode

    @property
    def textures_enabled(self) -> bool:
        """Check if texture rendering is enabled (master switch)."""
        return self._textures_enabled

    def set_texture_mode(self, enabled: bool) -> None:
        """Enable or disable texture mode."""
        if self._texture_mode != enabled:
            self._texture_mode = enabled
            self._dirty = True

    def set_textures_enabled(self, enabled: bool) -> None:
        """Enable or disable all texture rendering (master switch)."""
        if self._textures_enabled != enabled:
            self._textures_enabled = enabled
            self._dirty = True

    def toggle_texture_mode(self) -> bool:
        """Toggle texture rendering on/off. Returns new state."""
        self.set_textures_enabled(not self._textures_enabled)
        return self._textures_enabled

    def load_face_texture(self, face_name: FaceName, file_path: str) -> bool:
        """Load a texture for a specific face."""
        if face_name in self._face_textures:
            self._renderer.delete_texture(self._face_textures[face_name])
            del self._face_textures[face_name]

        handle = self._renderer.load_texture(file_path)
        if handle is not None:
            self._face_textures[face_name] = handle
            self._dirty = True
            return True
        return False

    def get_face_texture(self, face_name: FaceName) -> int | None:
        """Get texture handle for a face."""
        return self._face_textures.get(face_name)

    def clear_face_textures(self) -> None:
        """Remove all face textures."""
        for handle in self._face_textures.values():
            self._renderer.delete_texture(handle)
        self._face_textures.clear()
        self._dirty = True

    def load_texture_set(self, directory: str) -> int:
        """Load all face textures from a directory (OLD method - per-face textures).

        Expects files named F.png, B.png, R.png, L.png, U.png, D.png

        Note: This uses the old per-face texture system.
        For per-cell textures (that follow stickers), use load_texture_set_per_cell().
        """
        from pathlib import Path
        dir_path = Path(directory)
        loaded = 0

        for face_name in FaceName:
            for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                file_path = dir_path / f"{face_name.name}{ext}"
                if file_path.exists():
                    if self.load_face_texture(face_name, str(file_path)):
                        loaded += 1
                    break

        return loaded

    def load_texture_set_per_cell(self, directory: str) -> int:
        """Load face textures and slice into per-cell textures.

        This is the NEW texture system where each cell has its own texture
        stored in PartEdge.c_attributes. Textures follow stickers during
        rotation via the copy_color() mechanism.

        Expects files named F.png, B.png, R.png, L.png, U.png, D.png

        Args:
            directory: Path to directory containing face images

        Returns:
            Number of faces successfully loaded
        """
        from pathlib import Path

        # Clear old cell textures
        self.clear_cell_textures()

        dir_path = Path(directory)
        size = self._cube.size
        loaded = 0

        for face_name in FaceName:
            for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                file_path = dir_path / f"{face_name.name}{ext}"
                if file_path.exists():
                    # Slice image into NxN cell textures
                    sliced = self._renderer.slice_texture(str(file_path), size)
                    if sliced:
                        # Assign texture handles to PartEdge.c_attributes
                        self._assign_cell_textures(face_name, sliced)
                        loaded += 1
                    break

        if loaded > 0:
            self._use_per_cell_textures = True
            self._texture_mode = False  # Disable old texture mode
            self._texture_directory = directory  # Store for reload on reset/resize
            self._dirty = True

        return loaded

    def _assign_cell_textures(
        self,
        face_name: FaceName,
        sliced_textures: list[list[int]],
    ) -> None:
        """Assign sliced texture handles to PartEdge.c_attributes.

        Each cell's texture handle is stored in the corresponding PartEdge's
        c_attributes dict under CELL_TEXTURE_KEY. During rotation, copy_color()
        automatically copies c_attributes, so textures follow stickers.

        Args:
            face_name: Which face the textures belong to
            sliced_textures: 2D list of texture handles [row][col]
        """
        cube_face = self._cube.face(face_name)
        size = self._cube.size

        for row in range(size):
            for col in range(size):
                texture_handle = sliced_textures[row][col]
                self._cell_textures.append(texture_handle)  # Track for cleanup

                # Get the PartEdge for this cell
                gl_face = self._board.faces[face_name]
                part_edge = gl_face.get_part_edge_at_cell(cube_face, row, col)

                if part_edge is not None:
                    part_edge.c_attributes[CELL_TEXTURE_KEY] = texture_handle
                    # Debug identifier to trace c_attributes copying
                    part_edge.c_attributes[CELL_DEBUG_KEY] = f"{face_name.value}({row},{col})"

    def clear_cell_textures(self) -> None:
        """Clear all per-cell textures from GPU and c_attributes."""
        # Delete GPU textures
        for handle in self._cell_textures:
            self._renderer.delete_texture(handle)
        self._cell_textures.clear()

        # Clear from c_attributes on all PartEdges
        for part_slice in self._cube.get_all_parts():
            for edge in part_slice.edges:
                edge.c_attributes.pop(CELL_TEXTURE_KEY, None)

        self._use_per_cell_textures = False
        self._texture_directory = None  # Don't reload on reset
        self._triangles_per_texture.clear()
        self._animated_triangles_per_texture.clear()
        self._dirty = True

    # =========================================================================
    # Mouse Picking (Ray-Plane Intersection)
    # =========================================================================

    def find_facet_by_ray(
        self,
        ray_origin: np.ndarray,
        ray_direction: np.ndarray,
    ) -> tuple[FaceName, int, int, np.ndarray, np.ndarray] | None:
        """Find which cube facet is hit by a ray.

        Uses ray-plane intersection for each face.

        Args:
            ray_origin: Ray start point in world space
            ray_direction: Ray direction (normalized)

        Returns:
            Tuple of (face_name, row, col, right_dir, up_dir) or None
        """
        size = self._cube.size
        face_size = HALF_CUBE_SIZE * 2
        cell_size = face_size / size

        best_hit: tuple[FaceName, int, int, np.ndarray, np.ndarray] | None = None
        best_t = float('inf')

        for face_name, (center, right, up) in FACE_TRANSFORMS.items():
            center_np = np.array(center, dtype=np.float32)
            right_np = np.array(right, dtype=np.float32)
            up_np = np.array(up, dtype=np.float32)

            # Face normal
            normal = np.cross(right_np, up_np)
            normal = normal / np.linalg.norm(normal)

            # Ray-plane intersection
            denom = np.dot(ray_direction, normal)
            if abs(denom) < 1e-6:
                continue

            t = np.dot(center_np - ray_origin, normal) / denom
            if t < 0 or t >= best_t:
                continue

            hit_point = ray_origin + t * ray_direction
            local = hit_point - center_np
            local_x = np.dot(local, right_np)
            local_y = np.dot(local, up_np)

            if abs(local_x) > HALF_CUBE_SIZE or abs(local_y) > HALF_CUBE_SIZE:
                continue

            col = int((local_x + HALF_CUBE_SIZE) / cell_size)
            row = int((local_y + HALF_CUBE_SIZE) / cell_size)
            col = max(0, min(size - 1, col))
            row = max(0, min(size - 1, row))

            best_t = t
            best_hit = (face_name, row, col, right_np, up_np)

        return best_hit

    def _setup_view_matrix(self, vs: "ApplicationAndViewState") -> None:
        """Set up the modelview matrix from view state."""
        self._renderer.load_identity()
        offset = vs.offset
        self._renderer.translate(float(offset[0]), float(offset[1]), float(offset[2]))
        self._renderer.rotate(math.degrees(vs.alpha_x_0), 1, 0, 0)
        self._renderer.rotate(math.degrees(vs.alpha_y_0), 0, 1, 0)
        self._renderer.rotate(math.degrees(vs.alpha_z_0), 0, 0, 1)
        self._renderer.rotate(math.degrees(vs.alpha_x), 1, 0, 0)
        self._renderer.rotate(math.degrees(vs.alpha_y), 0, 1, 0)
        self._renderer.rotate(math.degrees(vs.alpha_z), 0, 0, 1)

    def screen_to_ray(
        self,
        screen_x: float,
        screen_y: float,
        window_width: int,
        window_height: int,
        vs: "ApplicationAndViewState | None" = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Convert screen coordinates to a ray in world space."""
        if vs is not None:
            self._setup_view_matrix(vs)

        inv_mvp = self._renderer.get_inverse_mvp()

        ndc_x = (2.0 * screen_x / window_width) - 1.0
        ndc_y = (2.0 * screen_y / window_height) - 1.0

        near_ndc = np.array([ndc_x, ndc_y, -1.0, 1.0], dtype=np.float32)
        far_ndc = np.array([ndc_x, ndc_y, 1.0, 1.0], dtype=np.float32)

        near_world = np.matmul(inv_mvp, near_ndc)
        far_world = np.matmul(inv_mvp, far_ndc)

        near_world = near_world[:3] / near_world[3]
        far_world = far_world[:3] / far_world[3]

        ray_origin = near_world
        ray_direction = far_world - near_world
        ray_direction = ray_direction / np.linalg.norm(ray_direction)

        return ray_origin, ray_direction

    def find_facet_at_screen(
        self,
        screen_x: float,
        screen_y: float,
        window_width: int,
        window_height: int,
        vs: "ApplicationAndViewState | None" = None,
    ) -> tuple[FaceName, int, int, np.ndarray, np.ndarray] | None:
        """Find which cube facet is under the given screen position."""
        ray_origin, ray_direction = self.screen_to_ray(
            screen_x, screen_y, window_width, window_height, vs
        )
        return self.find_facet_by_ray(ray_origin, ray_direction)

    def get_part_edge_at_screen(
        self,
        screen_x: float,
        screen_y: float,
        window_width: int,
        window_height: int,
        vs: "ApplicationAndViewState | None" = None,
    ) -> tuple | None:
        """Find the PartEdge at screen position.

        Returns:
            Tuple of (PartEdge, right_dir, up_dir) or None
        """
        result = self.find_facet_at_screen(
            screen_x, screen_y, window_width, window_height, vs
        )
        if result is None:
            return None

        face_name, row, col, right_dir, up_dir = result

        # Delegate to board (which delegates to face)
        part_edge = self._board.get_part_edge_at_cell(face_name, row, col)
        if part_edge is None:
            return None

        return (part_edge, right_dir, up_dir)

    def _format_texture_state(self, label: str) -> str:
        """Format compact texture state for Front face for debugging."""
        from cube.domain.model.cube_boy import FaceName
        cube_face = self._cube.face(FaceName.F)
        size = self._cube.size

        lines = [f"  {label}:", "    Front face c_attributes (format: debug_id):"]
        for row in range(size - 1, -1, -1):
            row_items = []
            for col in range(size):
                part_slice = self._get_part_slice_at(FaceName.F, row, col)
                if part_slice:
                    part_edge = part_slice.get_face_edge(cube_face)
                    debug_id = part_edge.c_attributes.get(CELL_DEBUG_KEY, "???")
                    row_items.append(debug_id)
                else:
                    row_items.append("None")
            lines.append(f"      {row_items}")
        return "\n".join(lines)

    def _format_cell_texture_state(self) -> str:
        """Format cell texture state for Front face."""
        from cube.domain.model.cube_boy import FaceName
        gl_face = self._board.faces[FaceName.F]
        size = self._cube.size

        lines = ["    Front face CELLS part_edge.c_attributes:"]
        for row in range(size - 1, -1, -1):
            row_items = []
            for cell in gl_face.cells:
                if cell.row == row:
                    if cell.part_edge:
                        debug_id = cell.part_edge.c_attributes.get(CELL_DEBUG_KEY, "???")
                        row_items.append((cell.col, debug_id))
                    else:
                        row_items.append((cell.col, "NoEdge"))
            row_items.sort(key=lambda x: x[0])
            lines.append(f"      {[d for c, d in row_items]}")
        return "\n".join(lines)

    def _format_geometry_debug(self) -> str:
        """Format geometry debug info."""
        # Sort keys, treating None as -1 for sorting purposes
        static_keys = sorted(self._triangles_per_texture.keys(), key=lambda x: x if x is not None else -1)
        animated_keys = sorted(self._animated_triangles_per_texture.keys(), key=lambda x: x if x is not None else -1)
        lines = [
            "    Generated geometry:",
            f"      static texture_handles: {static_keys}",
            f"      animated texture_handles: {animated_keys}"
        ]
        return "\n".join(lines)

    def _debug_print_texture_state(self, label: str) -> None:
        """Print compact texture state for Front face for debugging (legacy).

        Note: This method prints directly, ignoring DEBUG_TEXTURE config.
        Use _debug_texture_lazy(lambda: self._format_texture_state(label)) instead.
        """
        self._debug_texture_lazy(lambda: self._format_texture_state(label))

    def _get_part_slice_at(self, face_name: FaceName, row: int, col: int):
        """Get PartSlice at position (for debugging)."""
        cube_face = self._cube.face(face_name)
        size = self._cube.size
        last = size - 1

        is_bottom_row = (row == 0)
        is_top_row = (row == last)
        is_left_col = (col == 0)
        is_right_col = (col == last)

        if is_bottom_row and is_left_col:
            return cube_face.corner_bottom_left.slice
        if is_bottom_row and is_right_col:
            return cube_face.corner_bottom_right.slice
        if is_top_row and is_left_col:
            return cube_face.corner_top_left.slice
        if is_top_row and is_right_col:
            return cube_face.corner_top_right.slice
        if is_bottom_row:
            return cube_face.edge_bottom.get_slice_by_ltr_index(cube_face, col - 1)
        if is_top_row:
            return cube_face.edge_top.get_slice_by_ltr_index(cube_face, col - 1)
        if is_left_col:
            return cube_face.edge_left.get_slice_by_ltr_index(cube_face, row - 1)
        if is_right_col:
            return cube_face.edge_right.get_slice_by_ltr_index(cube_face, row - 1)
        if 0 < row < last and 0 < col < last:
            return cube_face.center.get_slice((row - 1, col - 1))
        return None

    def debug_print_face_grid(self, face_name: FaceName) -> None:
        """Print debug grid showing c_attributes debug IDs for a face.

        Prints grid from top to bottom (row N-1 first) to match visual layout.
        Uses debug infrastructure - output controlled by DEBUG_TEXTURE config.
        """
        self._debug_texture_lazy(lambda: self._format_face_grid(face_name))

    def _format_face_grid(self, face_name: FaceName) -> str:
        """Format debug grid for a face."""
        cube_face = self._cube.face(face_name)
        size = self._cube.size
        gl_face = self._board.faces[face_name]

        lines = [
            f"\n=== DEBUG: {face_name.value} face c_attributes ===",
            "Format: debug_id (texture_handle)"
        ]
        # Print from top row to bottom (visual order)
        for row in range(size - 1, -1, -1):
            row_items = []
            for col in range(size):
                part_edge = gl_face.get_part_edge_at_cell(cube_face, row, col)
                if part_edge is not None:
                    debug_id = part_edge.c_attributes.get(CELL_DEBUG_KEY, "???")
                    tex_handle = part_edge.c_attributes.get(CELL_TEXTURE_KEY, -1)
                    row_items.append(f"{debug_id}({tex_handle})")
                else:
                    row_items.append("None")
            lines.append("  ".join(row_items))
        lines.append("=" * 60)

        # Also print what the cells see
        lines.append(f"=== DEBUG: {face_name.value} CELL texture handles ===")
        for row in range(size - 1, -1, -1):
            cell_items: list[tuple[int, int]] = []
            for cell in gl_face.cells:
                if cell.row == row:
                    tex = cell.cell_texture if cell.cell_texture else -1
                    cell_items.append((cell.col, tex))
            cell_items.sort(key=lambda x: x[0])
            lines.append("  ".join([f"({c},{t})" for c, t in cell_items]))
        lines.append("=" * 60)
        return "\n".join(lines)
