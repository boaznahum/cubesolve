"""
Modern OpenGL Cube Viewer for pyglet2 backend.

This viewer renders a Rubik's cube using modern OpenGL (shaders, VBOs)
instead of legacy immediate mode rendering.

Animation Support:
    This viewer supports smooth face rotation animation by tracking which
    cells are being animated and rendering them with a rotation matrix.
    The animation flow:
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

from cube.domain.model.cube_boy import Color, FaceName
from cube.domain.model._part_slice import PartSlice

from cube.presentation.gui.protocols.AnimatableViewer import AnimatableViewer

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.algs import AnimationAbleAlg
    from cube.application.state import ApplicationAndViewState
    from cube.application.animation.AnimationManager import Animation
    from cube.presentation.gui.backends.pyglet2.ModernGLRenderer import ModernGLRenderer


# Color mapping: cube color enum -> RGB (0-1 normalized)
_COLORS: dict[Color, tuple[float, float, float]] = {
    Color.WHITE: (1.0, 1.0, 1.0),
    Color.YELLOW: (1.0, 0.84, 0.0),
    Color.GREEN: (0.0, 0.61, 0.28),
    Color.BLUE: (0.0, 0.27, 0.68),
    Color.RED: (0.72, 0.07, 0.20),
    Color.ORANGE: (1.0, 0.35, 0.0),
}

# Face positions in 3D space
# Each face has: center point, right direction, up direction
# Cube is centered at origin with faces at distance FACE_OFFSET
FACE_OFFSET = 50.0  # Half the cube size

_FACE_TRANSFORMS: dict[FaceName, tuple[
    tuple[float, float, float],  # center
    tuple[float, float, float],  # right direction
    tuple[float, float, float],  # up direction
]] = {
    FaceName.F: ((0, 0, FACE_OFFSET), (1, 0, 0), (0, 1, 0)),      # Front: +Z
    FaceName.B: ((0, 0, -FACE_OFFSET), (-1, 0, 0), (0, 1, 0)),    # Back: -Z
    FaceName.R: ((FACE_OFFSET, 0, 0), (0, 0, -1), (0, 1, 0)),     # Right: +X
    FaceName.L: ((-FACE_OFFSET, 0, 0), (0, 0, 1), (0, 1, 0)),     # Left: -X
    FaceName.U: ((0, FACE_OFFSET, 0), (1, 0, 0), (0, 0, -1)),     # Up: +Y
    FaceName.D: ((0, -FACE_OFFSET, 0), (1, 0, 0), (0, 0, 1)),     # Down: -Y
}


class ModernGLCubeViewer(AnimatableViewer):
    """Renders a Rubik's cube using modern OpenGL (shaders, VBOs).

    Implements AnimatableViewer protocol for animation support.

    This is a simplified viewer that works with ModernGLRenderer.
    It generates triangle data for all cube facets and renders them
    in batches for efficiency.
    """

    def __init__(
        self,
        cube: Cube,
        renderer: ModernGLRenderer,
        vs: "ApplicationAndViewState | None" = None,
    ) -> None:
        """Initialize the cube viewer.

        Args:
            cube: The cube model to render
            renderer: The modern GL renderer to use
            vs: Application view state (for shadow mode support)
        """
        self._cube = cube
        self._renderer = renderer
        self._vs = vs

        # Cached triangle data (position + color interleaved)
        # Will be rebuilt when cube state changes
        self._face_triangles: np.ndarray | None = None
        self._line_data: np.ndarray | None = None

        # Per-face geometry for textured rendering (11 floats: pos+normal+color+uv)
        self._face_triangles_per_face: dict[FaceName, np.ndarray] = {}

        # Animation state - separate geometry for animated cells
        self._animated_face_triangles: np.ndarray | None = None
        self._animated_line_data: np.ndarray | None = None
        self._animated_parts: set[PartSlice] | None = None
        self._animation_face_center: ndarray | None = None
        self._animation_opposite_center: ndarray | None = None
        # Per-face animated geometry for textured rendering
        self._animated_face_triangles_per_face: dict[FaceName, np.ndarray] = {}

        # Texture mode state
        self._texture_mode: bool = False
        # Textures per face: FaceName -> texture_handle
        self._face_textures: dict[FaceName, int] = {}

        # Track if we need to rebuild
        self._dirty = True

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
        # Mark as dirty to rebuild geometry
        self._dirty = True

    @property
    def renderer(self) -> ModernGLRenderer:
        """Get the renderer instance.

        This property is required by AnimationManager.
        """
        return self._renderer

    @property
    def cube(self) -> Cube:
        """Get the cube instance.

        Part of AnimatableViewer protocol.
        """
        return self._cube

    # === Animation Interface (AnimatableViewer protocol) ===

    def get_slices_movable_gui_objects(
        self,
        face_name_rotate_axis: FaceName,
        cube_parts: Collection[PartSlice],
        hide: bool = True,
    ) -> Tuple[ndarray, ndarray, Iterable[int]]:
        """Get animation data for a set of parts.

        This method is called by AnimationManager to set up animation.
        In legacy GL, it returns display list IDs. In modern GL, we store
        the animated parts and return empty gui_objects (animation is
        handled differently).

        Args:
            face_name_rotate_axis: The face determining the rotation axis
            cube_parts: The parts being rotated
            hide: If True, mark these parts for separate animation rendering

        Returns:
            Tuple of (face_center, opposite_center, gui_objects)
            - face_center: Center of the rotation face
            - opposite_center: Center of the opposite face (for axis)
            - gui_objects: Empty iterable (modern GL doesn't use display lists)
        """
        cube = self._cube
        face = cube.face(face_name_rotate_axis)
        opposite = face.opposite

        # Get face centers in 3D space
        face_center = np.array(_FACE_TRANSFORMS[face_name_rotate_axis][0], dtype=np.float32)
        opposite_center = np.array(_FACE_TRANSFORMS[opposite.name][0], dtype=np.float32)

        if hide:
            # Store animation state
            if not isinstance(cube_parts, set):
                cube_parts = set(cube_parts)
            self._animated_parts = cube_parts
            self._animation_face_center = face_center
            self._animation_opposite_center = opposite_center

            # Force geometry rebuild to separate animated parts
            self._dirty = True

        return face_center, opposite_center, []

    def unhidden_all(self) -> None:
        """End animation and restore normal rendering.

        Called by AnimationManager when animation completes.
        """
        self._animated_parts = None
        self._animation_face_center = None
        self._animation_opposite_center = None
        self._animated_face_triangles = None
        self._animated_line_data = None
        self._animated_face_triangles_per_face.clear()
        self._dirty = True

    def is_animating(self) -> bool:
        """Check if animation is active."""
        return self._animated_parts is not None

    # === Texture Mode Control ===

    @property
    def texture_mode(self) -> bool:
        """Check if texture mode is enabled."""
        return self._texture_mode

    def set_texture_mode(self, enabled: bool) -> None:
        """Enable or disable texture mode.

        Args:
            enabled: True to enable texture rendering, False for solid colors
        """
        if self._texture_mode != enabled:
            self._texture_mode = enabled
            self._dirty = True  # Force geometry rebuild with/without UVs

    def toggle_texture_mode(self) -> bool:
        """Toggle texture mode on/off.

        Returns:
            New texture mode state (True = enabled)
        """
        self.set_texture_mode(not self._texture_mode)
        return self._texture_mode

    def load_face_texture(self, face_name: FaceName, file_path: str) -> bool:
        """Load a texture for a specific face.

        Args:
            face_name: Which face to apply the texture to
            file_path: Path to image file (PNG, JPG, etc.)

        Returns:
            True if texture loaded successfully
        """
        # Delete existing texture if any
        if face_name in self._face_textures:
            self._renderer.delete_texture(self._face_textures[face_name])
            del self._face_textures[face_name]

        # Load new texture
        handle = self._renderer.load_texture(file_path)
        if handle is not None:
            self._face_textures[face_name] = handle
            self._dirty = True
            return True
        return False

    def get_face_texture(self, face_name: FaceName) -> int | None:
        """Get texture handle for a face, or None if no texture loaded."""
        return self._face_textures.get(face_name)

    def clear_face_textures(self) -> None:
        """Remove all face textures."""
        for handle in self._face_textures.values():
            self._renderer.delete_texture(handle)
        self._face_textures.clear()
        self._dirty = True

    def load_texture_set(self, directory: str) -> int:
        """Load all face textures from a directory.

        Expects files named F.png, B.png, R.png, L.png, U.png, D.png
        (or .jpg, .bmp, etc.).

        Args:
            directory: Path to directory containing face texture images

        Returns:
            Number of textures successfully loaded (0-6)
        """
        from pathlib import Path
        dir_path = Path(directory)
        loaded = 0

        for face_name in FaceName:
            # Try common image extensions
            for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                file_path = dir_path / f"{face_name.name}{ext}"
                if file_path.exists():
                    if self.load_face_texture(face_name, str(file_path)):
                        loaded += 1
                    break

        return loaded

    def draw_animated(self, model_view: ndarray) -> None:
        """Draw animated parts with the given model-view matrix.

        This is called by the animation system's _draw() closure to render
        the rotating parts with animation transform applied.

        Args:
            model_view: The 4x4 rotation matrix to apply to animated geometry
        """
        # Check if we have anything to draw
        has_animated_geometry = (
            (not self._texture_mode and self._animated_face_triangles is not None
             and len(self._animated_face_triangles) > 0) or
            (self._texture_mode and len(self._animated_face_triangles_per_face) > 0)
        )
        if not has_animated_geometry:
            return

        # Save current model-view matrix
        self._renderer.push_matrix()

        # Apply animation rotation matrix
        self._renderer.multiply_matrix(model_view)

        # Draw animated geometry with lighting
        if self._texture_mode:
            # Textured mode: draw each face separately with its texture
            for face_name, triangles in self._animated_face_triangles_per_face.items():
                if len(triangles) > 0:
                    texture_handle = self._face_textures.get(face_name)
                    self._renderer.draw_textured_lit_triangles(triangles, texture_handle)
        else:
            # Solid color mode
            if self._animated_face_triangles is not None:
                self._renderer.draw_lit_triangles(self._animated_face_triangles)

        if self._animated_line_data is not None and len(self._animated_line_data) > 0:
            self._renderer.draw_colored_lines(self._animated_line_data, line_width=4.0)

        # Restore matrix
        self._renderer.pop_matrix()

    def create_animation(
        self,
        alg: "AnimationAbleAlg",
        vs: "ApplicationAndViewState",
    ) -> "Animation":
        """Create animation for a face rotation algorithm.

        Implements AnimatableViewer protocol. Uses VBOs for rendering
        the animated parts.

        Args:
            alg: The algorithm to animate (must implement get_animation_objects)
            vs: Application view state (for speed settings, view transforms)

        Returns:
            Animation object ready for scheduling
        """
        # Import here to avoid circular imports
        from cube.application.animation.AnimationManager import Animation

        cube = self._cube
        n_count = alg.n

        # Get the rotated face and parts
        rotate_face, cube_parts = alg.get_animation_objects(cube)

        if not isinstance(cube_parts, Set):
            cube_parts = set(cube_parts)

        # Set up animation in viewer (marks parts for separate rendering)
        face_center, opposite_face_center, _ = self.get_slices_movable_gui_objects(
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

            # Compute the rotation matrix for current angle
            ct = math.cos(current_angle)
            st = math.sin(current_angle)
            Rz = np.array([[ct, st, 0, 0],
                           [-st, ct, 0, 0],
                           [0, 0, 1, 0],
                           [0, 0, 0, 1]], dtype=float)

            model_view: ndarray = mt @ Rz @ m

            # Draw animated parts with the rotation matrix
            self.draw_animated(model_view)

        animation.delay = animation_speed.delay_between_steps
        animation._animation_draw_only = _draw
        animation._animation_update_only = _update

        return animation

    def draw(self) -> None:
        """Draw the cube.

        Rebuilds geometry if cube state changed, then renders with lighting.
        """
        if self._dirty:
            self._rebuild_geometry()
            self._dirty = False

        # Draw filled faces with lighting
        if self._texture_mode:
            # Textured mode: draw each face separately with its texture
            for face_name, triangles in self._face_triangles_per_face.items():
                if len(triangles) > 0:
                    texture_handle = self._face_textures.get(face_name)
                    self._renderer.draw_textured_lit_triangles(triangles, texture_handle)
        else:
            # Solid color mode: draw all faces in one batch
            if self._face_triangles is not None and len(self._face_triangles) > 0:
                self._renderer.draw_lit_triangles(self._face_triangles)

        # Draw grid lines (no lighting) - use thick lines like legacy GL
        if self._line_data is not None and len(self._line_data) > 0:
            self._renderer.draw_colored_lines(self._line_data, line_width=4.0)

    def _rebuild_geometry(self) -> None:
        """Rebuild all geometry from current cube state.

        If animation is active, separates geometry into:
        - Static geometry (non-animated cells) in _face_triangles/_line_data
        - Animated geometry in _animated_face_triangles/_animated_line_data

        Shadow faces (F10/F11/F12) are rendered as duplicate faces at offset positions.

        Vertex format for faces (non-textured): 9 floats per vertex (x, y, z, nx, ny, nz, r, g, b)
        Vertex format for faces (textured): 11 floats per vertex (x, y, z, nx, ny, nz, r, g, b, u, v)
        Vertex format for lines: 6 floats per vertex (x, y, z, r, g, b)
        """
        cube = self._cube
        size = cube.size
        animated_parts = self._animated_parts

        # Collect all triangle vertices (9 floats per vertex: x,y,z,nx,ny,nz,r,g,b)
        face_verts: list[float] = []
        # Lines still use 6 floats (no lighting needed)
        line_verts: list[float] = []
        animated_face_verts: list[float] = []
        animated_line_verts: list[float] = []

        # Per-face geometry for textured mode (11 floats: pos+normal+color+uv)
        face_verts_per_face: dict[FaceName, list[float]] = {fn: [] for fn in FaceName}
        animated_face_verts_per_face: dict[FaceName, list[float]] = {fn: [] for fn in FaceName}

        # Shadow face offsets (in units of FACE_OFFSET * 2 = full face size)
        # These match the legacy _board.py offsets
        shadow_offsets: dict[FaceName, tuple[float, float, float]] = {
            FaceName.L: (-0.75 * FACE_OFFSET * 2, 0, 0),  # Left shadow: offset in -X
            FaceName.D: (0, -0.5 * FACE_OFFSET * 2, 0),   # Down shadow: offset in -Y
            FaceName.B: (0, 0, -2.0 * FACE_OFFSET * 2),   # Back shadow: offset in -Z
        }

        # For each face of the cube
        for face_name in FaceName:
            face = cube.face(face_name)
            transform = _FACE_TRANSFORMS[face_name]
            center = np.array(transform[0], dtype=np.float32)
            right = np.array(transform[1], dtype=np.float32)
            up = np.array(transform[2], dtype=np.float32)

            # Generate main face geometry
            self._generate_face_geometry(
                face, face_name, center, right, up, size, animated_parts,
                face_verts, line_verts, animated_face_verts, animated_line_verts,
                face_verts_per_face[face_name], animated_face_verts_per_face[face_name]
            )

            # Generate shadow face if enabled (L, D, B faces only)
            if self._vs is not None and face_name in shadow_offsets:
                if self._vs.get_draw_shadows_mode(face_name):
                    offset = np.array(shadow_offsets[face_name], dtype=np.float32)
                    shadow_center = center + offset
                    # Shadow faces are never animated (static copies)
                    self._generate_face_geometry(
                        face, face_name, shadow_center, right, up, size, None,
                        face_verts, line_verts, [], [],
                        face_verts_per_face[face_name], []
                    )

        self._face_triangles = np.array(face_verts, dtype=np.float32)
        self._line_data = np.array(line_verts, dtype=np.float32)
        self._animated_face_triangles = np.array(animated_face_verts, dtype=np.float32) if animated_face_verts else None
        self._animated_line_data = np.array(animated_line_verts, dtype=np.float32) if animated_line_verts else None

        # Convert per-face lists to numpy arrays
        self._face_triangles_per_face = {
            fn: np.array(verts, dtype=np.float32) for fn, verts in face_verts_per_face.items()
        }
        self._animated_face_triangles_per_face = {
            fn: np.array(verts, dtype=np.float32) for fn, verts in animated_face_verts_per_face.items()
            if verts  # Only include non-empty
        }

    def _generate_face_geometry(
        self,
        face,
        face_name: FaceName,
        center: np.ndarray,
        right: np.ndarray,
        up: np.ndarray,
        size: int,
        animated_parts: set[PartSlice] | None,
        face_verts: list[float],
        line_verts: list[float],
        animated_face_verts: list[float],
        animated_line_verts: list[float],
        textured_face_verts: list[float],
        animated_textured_face_verts: list[float],
    ) -> None:
        """Generate geometry for a single face.

        Args:
            face: The cube Face object
            face_name: Name of this face (for texture lookups)
            center: Face center position in world space
            right: Face "right" direction vector
            up: Face "up" direction vector
            size: Cube size (3 for 3x3, etc.)
            animated_parts: Set of parts being animated (or None)
            face_verts: Output list for static face triangles (9 floats/vertex)
            line_verts: Output list for static line segments
            animated_face_verts: Output list for animated face triangles (9 floats/vertex)
            animated_line_verts: Output list for animated line segments
            textured_face_verts: Output list for static textured triangles (11 floats/vertex)
            animated_textured_face_verts: Output list for animated textured triangles (11 floats/vertex)
        """
        # Compute face normal (outward direction)
        normal = np.cross(right, up)
        normal = normal / np.linalg.norm(normal)
        nx, ny, nz = float(normal[0]), float(normal[1]), float(normal[2])

        # Face size in world units
        face_size = FACE_OFFSET * 2
        cell_size = face_size / size

        # Generate quads for each cell on this face
        for row in range(size):
            for col in range(size):
                # Get color for this cell
                color = self._get_cell_color(face, row, col, size)
                r, g, b = _COLORS.get(color, (0.5, 0.5, 0.5))

                # Check if this cell is animated
                is_animated = False
                if animated_parts is not None:
                    part_slice = self._get_cell_part_slice(face, row, col, size)
                    if part_slice is not None and part_slice in animated_parts:
                        is_animated = True

                # Select target lists based on animation state
                target_face_verts = animated_face_verts if is_animated else face_verts
                target_line_verts = animated_line_verts if is_animated else line_verts
                target_textured_verts = animated_textured_face_verts if is_animated else textured_face_verts

                # Calculate cell position
                # Cell (0,0) is bottom-left, (size-1, size-1) is top-right
                x0 = -FACE_OFFSET + col * cell_size
                y0 = -FACE_OFFSET + row * cell_size
                x1 = x0 + cell_size
                y1 = y0 + cell_size

                # Apply small gap between cells for grid effect
                gap = cell_size * 0.02
                x0 += gap
                y0 += gap
                x1 -= gap
                y1 -= gap

                # Calculate 4 corners in world space
                bl = center + x0 * right + y0 * up
                br = center + x1 * right + y0 * up
                tr = center + x1 * right + y1 * up
                tl = center + x0 * right + y1 * up

                # UV coordinates for this cell
                # Map cell to portion of texture: (col, row) -> (u, v)
                u0 = col / size
                v0 = row / size
                u1 = (col + 1) / size
                v1 = (row + 1) / size

                # UV coordinates for each corner
                uv_bl = (u0, v0)
                uv_br = (u1, v0)
                uv_tr = (u1, v1)
                uv_tl = (u0, v1)

                # Two triangles for quad: (bl, br, tr) and (bl, tr, tl)
                # Non-textured: position (3) + normal (3) + color (3) = 9 floats
                for v in [bl, br, tr, bl, tr, tl]:
                    target_face_verts.extend([v[0], v[1], v[2], nx, ny, nz, r, g, b])

                # Textured: position (3) + normal (3) + color (3) + uv (2) = 11 floats
                # Triangle 1: bl, br, tr
                target_textured_verts.extend([bl[0], bl[1], bl[2], nx, ny, nz, r, g, b, uv_bl[0], uv_bl[1]])
                target_textured_verts.extend([br[0], br[1], br[2], nx, ny, nz, r, g, b, uv_br[0], uv_br[1]])
                target_textured_verts.extend([tr[0], tr[1], tr[2], nx, ny, nz, r, g, b, uv_tr[0], uv_tr[1]])
                # Triangle 2: bl, tr, tl
                target_textured_verts.extend([bl[0], bl[1], bl[2], nx, ny, nz, r, g, b, uv_bl[0], uv_bl[1]])
                target_textured_verts.extend([tr[0], tr[1], tr[2], nx, ny, nz, r, g, b, uv_tr[0], uv_tr[1]])
                target_textured_verts.extend([tl[0], tl[1], tl[2], nx, ny, nz, r, g, b, uv_tl[0], uv_tl[1]])

                # Border lines (black) - still 6 floats, no normals needed
                line_color = (0.0, 0.0, 0.0)
                for p1, p2 in [(bl, br), (br, tr), (tr, tl), (tl, bl)]:
                    target_line_verts.extend([
                        p1[0], p1[1], p1[2], *line_color,
                        p2[0], p2[1], p2[2], *line_color
                    ])

    def _get_cell_part_slice(self, face, row: int, col: int, size: int) -> PartSlice | None:
        """Get the PartSlice for a cell on a face.

        Args:
            face: The Face object
            row: Row index (0 = bottom)
            col: Column index (0 = left)
            size: Cube size

        Returns:
            PartSlice for this cell, or None if not found
        """
        if size == 3:
            return self._get_cell_part_slice_3x3(face, row, col)
        else:
            return self._get_cell_part_slice_nxn(face, row, col, size)

    def _get_cell_part_slice_3x3(self, face, row: int, col: int) -> PartSlice | None:
        """Get cell PartSlice for 3x3 cube."""
        # Corners
        if row == 0 and col == 0:
            return face.corner_bottom_left.slice
        if row == 0 and col == 2:
            return face.corner_bottom_right.slice
        if row == 2 and col == 0:
            return face.corner_top_left.slice
        if row == 2 and col == 2:
            return face.corner_top_right.slice

        # Edges (single slice for 3x3)
        if row == 0 and col == 1:
            return face.edge_bottom.get_slice_by_ltr_index(face, 0)
        if row == 2 and col == 1:
            return face.edge_top.get_slice_by_ltr_index(face, 0)
        if row == 1 and col == 0:
            return face.edge_left.get_slice_by_ltr_index(face, 0)
        if row == 1 and col == 2:
            return face.edge_right.get_slice_by_ltr_index(face, 0)

        # Center (single cell for 3x3)
        if row == 1 and col == 1:
            return face.center.get_slice((0, 0))

        return None

    def _get_cell_part_slice_nxn(self, face, row: int, col: int, size: int) -> PartSlice | None:
        """Get cell PartSlice for NxN cube."""
        last = size - 1

        # Corners
        if row == 0 and col == 0:
            return face.corner_bottom_left.slice
        if row == 0 and col == last:
            return face.corner_bottom_right.slice
        if row == last and col == 0:
            return face.corner_top_left.slice
        if row == last and col == last:
            return face.corner_top_right.slice

        # Bottom edge
        if row == 0 and 0 < col < last:
            return face.edge_bottom.get_slice_by_ltr_index(face, col - 1)

        # Top edge
        if row == last and 0 < col < last:
            return face.edge_top.get_slice_by_ltr_index(face, col - 1)

        # Left edge
        if col == 0 and 0 < row < last:
            return face.edge_left.get_slice_by_ltr_index(face, row - 1)

        # Right edge
        if col == last and 0 < row < last:
            return face.edge_right.get_slice_by_ltr_index(face, row - 1)

        # Center
        if 0 < row < last and 0 < col < last:
            return face.center.get_slice((row - 1, col - 1))

        return None

    def _get_cell_color(self, face, row: int, col: int, size: int) -> Color:
        """Get the color of a cell on a face.

        Args:
            face: The Face object
            row: Row index (0 = bottom)
            col: Column index (0 = left)
            size: Cube size

        Returns:
            Color enum value for this cell
        """
        # Map (row, col) to the cube's internal part structure
        # The face has 9 parts for 3x3: corners, edges, center

        # For 3x3 cube:
        # row=2: top-left corner, top edge, top-right corner
        # row=1: left edge, center, right edge
        # row=0: bottom-left corner, bottom edge, bottom-right corner

        # For NxN, we need to map to the correct slice within each part
        if size == 3:
            return self._get_cell_color_3x3(face, row, col)
        else:
            return self._get_cell_color_nxn(face, row, col, size)

    def _get_cell_color_3x3(self, face, row: int, col: int) -> Color:
        """Get cell color for 3x3 cube (simpler case)."""
        # Corners
        if row == 0 and col == 0:
            return face.corner_bottom_left.slice.get_face_edge(face).color
        if row == 0 and col == 2:
            return face.corner_bottom_right.slice.get_face_edge(face).color
        if row == 2 and col == 0:
            return face.corner_top_left.slice.get_face_edge(face).color
        if row == 2 and col == 2:
            return face.corner_top_right.slice.get_face_edge(face).color

        # Edges (single slice for 3x3)
        if row == 0 and col == 1:
            return face.edge_bottom.get_slice_by_ltr_index(face, 0).get_face_edge(face).color
        if row == 2 and col == 1:
            return face.edge_top.get_slice_by_ltr_index(face, 0).get_face_edge(face).color
        if row == 1 and col == 0:
            return face.edge_left.get_slice_by_ltr_index(face, 0).get_face_edge(face).color
        if row == 1 and col == 2:
            return face.edge_right.get_slice_by_ltr_index(face, 0).get_face_edge(face).color

        # Center (single cell for 3x3)
        if row == 1 and col == 1:
            return face.center.get_slice((0, 0)).get_face_edge(face).color

        # Fallback
        return face.original_color

    def _get_cell_color_nxn(self, face, row: int, col: int, size: int) -> Color:
        """Get cell color for NxN cube."""
        # For NxN, the layout is:
        # - Corners at (0,0), (0, size-1), (size-1, 0), (size-1, size-1)
        # - Edges along the borders (excluding corners)
        # - Center fills the middle (size-2) x (size-2) area

        last = size - 1

        # Corners
        if row == 0 and col == 0:
            return face.corner_bottom_left.slice.get_face_edge(face).color
        if row == 0 and col == last:
            return face.corner_bottom_right.slice.get_face_edge(face).color
        if row == last and col == 0:
            return face.corner_top_left.slice.get_face_edge(face).color
        if row == last and col == last:
            return face.corner_top_right.slice.get_face_edge(face).color

        # Edges
        n_slices = size - 2  # Number of edge wing slices

        # Bottom edge
        if row == 0 and 0 < col < last:
            idx = col - 1  # 0-based index within edge
            return face.edge_bottom.get_slice_by_ltr_index(face, idx).get_face_edge(face).color

        # Top edge
        if row == last and 0 < col < last:
            idx = col - 1
            return face.edge_top.get_slice_by_ltr_index(face, idx).get_face_edge(face).color

        # Left edge
        if col == 0 and 0 < row < last:
            idx = row - 1
            return face.edge_left.get_slice_by_ltr_index(face, idx).get_face_edge(face).color

        # Right edge
        if col == last and 0 < row < last:
            idx = row - 1
            return face.edge_right.get_slice_by_ltr_index(face, idx).get_face_edge(face).color

        # Center (the middle area)
        if 0 < row < last and 0 < col < last:
            # Map to center slice grid
            center_row = row - 1
            center_col = col - 1
            return face.center.get_slice((center_row, center_col)).get_face_edge(face).color

        # Fallback
        return face.original_color

    # === Ray-Plane Intersection for Mouse Picking ===

    def find_facet_by_ray(
        self,
        ray_origin: np.ndarray,
        ray_direction: np.ndarray,
    ) -> tuple[FaceName, int, int, np.ndarray, np.ndarray] | None:
        """Find which cube facet (cell) is hit by a ray.

        Uses ray-plane intersection for each of the 6 cube faces.
        Returns the closest hit.

        Args:
            ray_origin: Ray start point in world space (3D)
            ray_direction: Ray direction in world space (3D, normalized)

        Returns:
            Tuple of (face_name, row, col, right_dir, up_dir) or None if no hit.
            - face_name: Which face was hit (F, B, R, L, U, D)
            - row, col: Cell indices on that face
            - right_dir, up_dir: Face orientation vectors for drag direction
        """
        size = self._cube.size
        face_size = FACE_OFFSET * 2
        cell_size = face_size / size

        best_hit: tuple[FaceName, int, int, np.ndarray, np.ndarray] | None = None
        best_t = float('inf')

        for face_name, (center, right, up) in _FACE_TRANSFORMS.items():
            center_np = np.array(center, dtype=np.float32)
            right_np = np.array(right, dtype=np.float32)
            up_np = np.array(up, dtype=np.float32)

            # Face normal is cross(right, up)
            normal = np.cross(right_np, up_np)
            normal = normal / np.linalg.norm(normal)

            # Ray-plane intersection: t = (center - origin) . normal / (direction . normal)
            denom = np.dot(ray_direction, normal)
            if abs(denom) < 1e-6:
                continue  # Ray parallel to plane

            t = np.dot(center_np - ray_origin, normal) / denom
            if t < 0:
                continue  # Intersection behind ray origin

            if t >= best_t:
                continue  # Further than current best

            # Calculate intersection point
            hit_point = ray_origin + t * ray_direction

            # Convert to face-local coordinates (relative to center)
            local = hit_point - center_np
            local_x = np.dot(local, right_np)  # Position along right direction
            local_y = np.dot(local, up_np)     # Position along up direction

            # Check if within face bounds
            if abs(local_x) > FACE_OFFSET or abs(local_y) > FACE_OFFSET:
                continue  # Outside face

            # Convert to cell indices
            # local_x ranges from -FACE_OFFSET to +FACE_OFFSET
            # Map to 0..size
            col = int((local_x + FACE_OFFSET) / cell_size)
            row = int((local_y + FACE_OFFSET) / cell_size)

            # Clamp to valid range
            col = max(0, min(size - 1, col))
            row = max(0, min(size - 1, row))

            best_t = t
            best_hit = (face_name, row, col, right_np, up_np)

        return best_hit

    def _setup_view_matrix(self, vs) -> None:
        """Set up the modelview matrix from view state.

        This ensures the modelview matrix is current for picking operations
        that happen outside of on_draw().

        Args:
            vs: Application view state containing rotation angles and offset
        """
        import math

        self._renderer.load_identity()

        # Apply offset translation (camera distance)
        offset = vs.offset
        self._renderer.translate(float(offset[0]), float(offset[1]), float(offset[2]))

        # Apply initial rotation (base orientation)
        self._renderer.rotate(math.degrees(vs.alpha_x_0), 1, 0, 0)
        self._renderer.rotate(math.degrees(vs.alpha_y_0), 0, 1, 0)
        self._renderer.rotate(math.degrees(vs.alpha_z_0), 0, 0, 1)

        # Apply user-controlled rotation (from mouse drag)
        self._renderer.rotate(math.degrees(vs.alpha_x), 1, 0, 0)
        self._renderer.rotate(math.degrees(vs.alpha_y), 0, 1, 0)
        self._renderer.rotate(math.degrees(vs.alpha_z), 0, 0, 1)

    def screen_to_ray(
        self,
        screen_x: float,
        screen_y: float,
        window_width: int,
        window_height: int,
        vs=None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Convert screen coordinates to a ray in world space.

        Args:
            screen_x: X coordinate in pixels (0 = left)
            screen_y: Y coordinate in pixels (0 = bottom in OpenGL)
            window_width: Window width in pixels
            window_height: Window height in pixels
            vs: Optional view state - if provided, recalculates the view matrix

        Returns:
            Tuple of (ray_origin, ray_direction) both as numpy arrays
        """
        # Recalculate view matrix if view state provided
        if vs is not None:
            self._setup_view_matrix(vs)

        # Get inverse MVP matrix from renderer
        inv_mvp = self._renderer.get_inverse_mvp()

        # Convert screen to NDC (-1 to 1)
        ndc_x = (2.0 * screen_x / window_width) - 1.0
        ndc_y = (2.0 * screen_y / window_height) - 1.0

        # Create two points: near plane (z=-1) and far plane (z=1)
        near_ndc = np.array([ndc_x, ndc_y, -1.0, 1.0], dtype=np.float32)
        far_ndc = np.array([ndc_x, ndc_y, 1.0, 1.0], dtype=np.float32)

        # Unproject to world space
        near_world = np.matmul(inv_mvp, near_ndc)
        far_world = np.matmul(inv_mvp, far_ndc)

        # Perspective divide
        near_world = near_world[:3] / near_world[3]
        far_world = far_world[:3] / far_world[3]

        # Ray from near to far
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
        vs=None,
    ) -> tuple[FaceName, int, int, np.ndarray, np.ndarray] | None:
        """Find which cube facet is under the given screen position.

        Combines screen_to_ray() and find_facet_by_ray() for easy mouse picking.

        Args:
            screen_x: X coordinate in pixels
            screen_y: Y coordinate in pixels
            window_width: Window width
            window_height: Window height
            vs: Optional view state for matrix recalculation

        Returns:
            Tuple of (face_name, row, col, right_dir, up_dir) or None
        """
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
        vs=None,
    ) -> tuple | None:
        """Find the PartEdge at screen position.

        This is the main interface for mouse picking - returns the same format
        as the legacy GCubeViewer.find_facet() method.

        Args:
            screen_x: X coordinate in pixels
            screen_y: Y coordinate in pixels
            window_width: Window width
            window_height: Window height
            vs: Optional view state for matrix recalculation

        Returns:
            Tuple of (PartEdge, right_dir, up_dir) or None
            - PartEdge: The cube part edge that was clicked
            - right_dir: Face's "right" direction vector (for drag detection)
            - up_dir: Face's "up" direction vector (for drag detection)
        """
        from cube.domain.model.PartEdge import PartEdge

        result = self.find_facet_at_screen(
            screen_x, screen_y, window_width, window_height, vs
        )
        if result is None:
            return None

        face_name, row, col, right_dir, up_dir = result

        # Get the face from the cube
        face = self._cube.face(face_name)
        size = self._cube.size

        # Convert (row, col) to PartEdge
        part_edge = self._get_part_edge_at_cell(face, row, col, size)
        if part_edge is None:
            return None

        return (part_edge, right_dir, up_dir)

    def _get_part_edge_at_cell(self, face, row: int, col: int, size: int):
        """Get the PartEdge at a specific cell on a face.

        Args:
            face: The Face object
            row: Row index (0 = bottom)
            col: Column index (0 = left)
            size: Cube size

        Returns:
            PartEdge for this cell, or None
        """
        from cube.domain.model.PartEdge import PartEdge

        last = size - 1

        # Corners (at the 4 corners of the face)
        if row == 0 and col == 0:
            return face.corner_bottom_left.slice.get_face_edge(face)
        if row == 0 and col == last:
            return face.corner_bottom_right.slice.get_face_edge(face)
        if row == last and col == 0:
            return face.corner_top_left.slice.get_face_edge(face)
        if row == last and col == last:
            return face.corner_top_right.slice.get_face_edge(face)

        # For 3x3 cube
        if size == 3:
            # Edges (middle of each border)
            if row == 0 and col == 1:
                return face.edge_bottom.get_slice_by_ltr_index(face, 0).get_face_edge(face)
            if row == last and col == 1:
                return face.edge_top.get_slice_by_ltr_index(face, 0).get_face_edge(face)
            if row == 1 and col == 0:
                return face.edge_left.get_slice_by_ltr_index(face, 0).get_face_edge(face)
            if row == 1 and col == last:
                return face.edge_right.get_slice_by_ltr_index(face, 0).get_face_edge(face)

            # Center
            if row == 1 and col == 1:
                return face.center.get_slice((0, 0)).get_face_edge(face)
        else:
            # NxN cube

            # Bottom edge (excluding corners)
            if row == 0 and 0 < col < last:
                idx = col - 1
                return face.edge_bottom.get_slice_by_ltr_index(face, idx).get_face_edge(face)

            # Top edge (excluding corners)
            if row == last and 0 < col < last:
                idx = col - 1
                return face.edge_top.get_slice_by_ltr_index(face, idx).get_face_edge(face)

            # Left edge (excluding corners)
            if col == 0 and 0 < row < last:
                idx = row - 1
                return face.edge_left.get_slice_by_ltr_index(face, idx).get_face_edge(face)

            # Right edge (excluding corners)
            if col == last and 0 < row < last:
                idx = row - 1
                return face.edge_right.get_slice_by_ltr_index(face, idx).get_face_edge(face)

            # Center (the middle area)
            if 0 < row < last and 0 < col < last:
                center_row = row - 1
                center_col = col - 1
                return face.center.get_slice((center_row, center_col)).get_face_edge(face)

        return None
