"""
Web renderer implementation.

Collects rendering commands and sends them to browser via WebSocket.
Uses WebGL2 on the browser side for proper depth handling.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Sequence

from cube.presentation.gui.protocols import (
    DisplayListManager,
    Renderer,
    ShapeRenderer,
    ViewStateManager,
)
from cube.presentation.gui.types import (
    Color3,
    Color4,
    DisplayList,
    Matrix4x4,
    Point3D,
    TextureHandle,
    TextureMap,
)

if TYPE_CHECKING:
    from cube.presentation.gui.backends.web.WebEventLoop import WebEventLoop


class WebShapeRenderer(ShapeRenderer):
    """Web implementation of ShapeRenderer protocol.

    Collects shape commands to be sent to browser.
    """

    def __init__(self, command_queue: list[dict]):
        self._commands = command_queue
        self._display_list_manager: "WebDisplayListManager | None" = None
        # Sticker metadata context (set before drawing a sticker quad)
        self._sticker_face: str | None = None
        self._sticker_row: int = -1
        self._sticker_col: int = -1
        self._sticker_slice_index: int = -1  # Edge LTR index within part
        self._sticker_sx: int = -1  # Center sub-x
        self._sticker_sy: int = -1  # Center sub-y

    def set_display_list_manager(self, dlm: "WebDisplayListManager") -> None:
        """Set display list manager for compile-time redirection."""
        self._display_list_manager = dlm

    def set_sticker_context(self, face: str, row: int, col: int,
                            slice_index: int = -1,
                            sx: int = -1, sy: int = -1) -> None:
        """Set metadata context for the next quad commands."""
        self._sticker_face = face
        self._sticker_row = row
        self._sticker_col = col
        self._sticker_slice_index = slice_index
        self._sticker_sx = sx
        self._sticker_sy = sy

    def clear_sticker_context(self) -> None:
        """Clear the sticker metadata context."""
        self._sticker_face = None
        self._sticker_row = -1
        self._sticker_col = -1
        self._sticker_slice_index = -1
        self._sticker_sx = -1
        self._sticker_sy = -1

    def _inject_sticker_meta(self, cmd: dict) -> None:
        """Add sticker metadata to command if context is set."""
        if self._sticker_face is not None:
            cmd["face"] = self._sticker_face
            cmd["row"] = self._sticker_row
            cmd["col"] = self._sticker_col
            if self._sticker_slice_index >= 0:
                cmd["si"] = self._sticker_slice_index
            if self._sticker_sx >= 0:
                cmd["sx"] = self._sticker_sx
                cmd["sy"] = self._sticker_sy

    def _add_command(self, cmd: dict) -> None:
        """Add command to appropriate queue (main or compile buffer)."""
        if self._display_list_manager and self._display_list_manager.is_compiling():
            self._display_list_manager.add_to_compile(cmd)
        else:
            self._commands.append(cmd)

    def quad(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Queue quad command."""
        cmd = {
            "cmd": "quad",
            "vertices": [v.tolist() for v in vertices],
            "color": list(color)
        }
        self._inject_sticker_meta(cmd)
        self._add_command(cmd)

    def quad_with_border(
        self,
        vertices: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Queue quad with border command."""
        cmd = {
            "cmd": "quad_border",
            "vertices": [v.tolist() for v in vertices],
            "face_color": list(face_color),
            "line_width": line_width,
            "line_color": list(line_color)
        }
        self._inject_sticker_meta(cmd)
        self._add_command(cmd)

    def triangle(self, vertices: Sequence[Point3D], color: Color3) -> None:
        """Queue triangle command."""
        self._add_command({
            "cmd": "triangle",
            "vertices": [v.tolist() for v in vertices],
            "color": list(color)
        })

    def line(self, p1: Point3D, p2: Point3D, width: float, color: Color3) -> None:
        """Queue line command."""
        self._add_command({
            "cmd": "line",
            "p1": p1.tolist(),
            "p2": p2.tolist(),
            "width": width,
            "color": list(color)
        })

    def sphere(self, center: Point3D, radius: float, color: Color3) -> None:
        """Queue sphere command."""
        self._add_command({
            "cmd": "sphere",
            "center": center.tolist(),
            "radius": radius,
            "color": list(color)
        })

    def cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        radius1: float,
        radius2: float,
        color: Color3,
    ) -> None:
        """Queue cylinder command."""
        self._add_command({
            "cmd": "cylinder",
            "p1": p1.tolist(),
            "p2": p2.tolist(),
            "radius1": radius1,
            "radius2": radius2,
            "color": list(color)
        })

    def disk(
        self,
        center: Point3D,
        normal: Point3D,
        inner_radius: float,
        outer_radius: float,
        color: Color3,
    ) -> None:
        """Queue disk command."""
        self._add_command({
            "cmd": "disk",
            "center": center.tolist(),
            "normal": normal.tolist(),
            "inner_radius": inner_radius,
            "outer_radius": outer_radius,
            "color": list(color)
        })

    def lines(
        self,
        points: Sequence[tuple[Point3D, Point3D]],
        width: float,
        color: Color3,
    ) -> None:
        """Queue multiple lines command."""
        self._add_command({
            "cmd": "lines",
            "points": [[p1.tolist(), p2.tolist()] for p1, p2 in points],
            "width": width,
            "color": list(color)
        })

    def quad_with_texture(
        self,
        vertices: Sequence[Point3D],
        color: Color3,
        texture: TextureHandle | None,
        texture_map: TextureMap | None,
    ) -> None:
        """Queue textured quad (falls back to solid color for now)."""
        self.quad(vertices, color)

    def cross(
        self,
        vertices: Sequence[Point3D],
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Queue cross command."""
        self._add_command({
            "cmd": "cross",
            "vertices": [v.tolist() for v in vertices],
            "line_width": line_width,
            "line_color": list(line_color)
        })

    def lines_in_quad(
        self,
        vertices: Sequence[Point3D],
        n: int,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Queue lines-in-quad command."""
        if n <= 0:
            return
        self._add_command({
            "cmd": "lines_in_quad",
            "vertices": [v.tolist() for v in vertices],
            "n": n,
            "line_width": line_width,
            "line_color": list(line_color)
        })

    def box_with_lines(
        self,
        bottom_quad: Sequence[Point3D],
        top_quad: Sequence[Point3D],
        face_color: Color3,
        line_width: float,
        line_color: Color3,
    ) -> None:
        """Queue box command."""
        self._add_command({
            "cmd": "box",
            "bottom": [v.tolist() for v in bottom_quad],
            "top": [v.tolist() for v in top_quad],
            "face_color": list(face_color),
            "line_width": line_width,
            "line_color": list(line_color)
        })

    def full_cylinder(
        self,
        p1: Point3D,
        p2: Point3D,
        outer_radius: float,
        inner_radius: float,
        color: Color3,
    ) -> None:
        """Queue full cylinder command."""
        self._add_command({
            "cmd": "full_cylinder",
            "p1": p1.tolist(),
            "p2": p2.tolist(),
            "outer_radius": outer_radius,
            "inner_radius": inner_radius,
            "color": list(color)
        })


class WebDisplayListManager(DisplayListManager):
    """Display list manager for web backend.

    Stores command sequences that can be replayed.
    """

    def __init__(self, command_queue: list[dict]):
        self._commands = command_queue
        self._next_id = 1
        self._lists: dict[int, list[dict]] = {}
        self._compiling: int | None = None
        self._compile_buffer: list[dict] = []

    def create_list(self) -> DisplayList:
        """Create a new display list."""
        list_id = DisplayList(self._next_id)
        self._next_id += 1
        self._lists[list_id] = []
        return list_id

    def begin_compile(self, list_id: DisplayList) -> None:
        """Begin compiling commands into display list."""
        self._compiling = list_id
        self._compile_buffer = []

    def end_compile(self) -> None:
        """End compilation and store commands."""
        if self._compiling is not None:
            self._lists[self._compiling] = self._compile_buffer
            self._compiling = None
            self._compile_buffer = []

    def call_list(self, list_id: DisplayList) -> None:
        """Execute a display list."""
        if list_id in self._lists:
            self._commands.extend(self._lists[list_id])

    def call_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Execute multiple display lists."""
        for list_id in list_ids:
            self.call_list(list_id)

    def delete_list(self, list_id: DisplayList) -> None:
        """Delete a display list."""
        if list_id in self._lists:
            del self._lists[list_id]

    def delete_lists(self, list_ids: Sequence[DisplayList]) -> None:
        """Delete multiple display lists."""
        for list_id in list_ids:
            self.delete_list(list_id)

    def is_compiling(self) -> bool:
        """Check if currently compiling."""
        return self._compiling is not None

    def add_to_compile(self, cmd: dict) -> None:
        """Add command to compile buffer if compiling."""
        if self._compiling is not None:
            self._compile_buffer.append(cmd)


class WebViewStateManager(ViewStateManager):
    """View state manager for web backend.

    Tracks transformation state to send with frames.
    """

    def __init__(self, command_queue: list[dict]):
        self._commands = command_queue
        self._width = 720
        self._height = 720

    def set_projection(
        self,
        width: int,
        height: int,
        fov_y: float = 50.0,
        near: float = 0.1,
        far: float = 1000.0,
    ) -> None:
        """Set projection parameters."""
        self._width = width
        self._height = height
        self._commands.append({
            "cmd": "projection",
            "width": width,
            "height": height,
            "fov_y": fov_y,
            "near": near,
            "far": far
        })

    def push_matrix(self) -> None:
        """Push matrix onto stack."""
        self._commands.append({"cmd": "push_matrix"})

    def pop_matrix(self) -> None:
        """Pop matrix from stack."""
        self._commands.append({"cmd": "pop_matrix"})

    def load_identity(self) -> None:
        """Load identity matrix."""
        self._commands.append({"cmd": "load_identity"})

    def translate(self, x: float, y: float, z: float) -> None:
        """Apply translation."""
        self._commands.append({"cmd": "translate", "x": x, "y": y, "z": z})

    def rotate(self, angle_degrees: float, x: float, y: float, z: float) -> None:
        """Apply rotation."""
        self._commands.append({
            "cmd": "rotate",
            "angle": angle_degrees,
            "x": x, "y": y, "z": z
        })

    def scale(self, x: float, y: float, z: float) -> None:
        """Apply scale."""
        self._commands.append({"cmd": "scale", "x": x, "y": y, "z": z})

    def multiply_matrix(self, matrix: Matrix4x4) -> None:
        """Multiply by matrix."""
        self._commands.append({
            "cmd": "multiply_matrix",
            "matrix": matrix.tolist()
        })

    def look_at(
        self,
        eye_x: float, eye_y: float, eye_z: float,
        center_x: float, center_y: float, center_z: float,
        up_x: float, up_y: float, up_z: float,
    ) -> None:
        """Set up view matrix."""
        self._commands.append({
            "cmd": "look_at",
            "eye": [eye_x, eye_y, eye_z],
            "center": [center_x, center_y, center_z],
            "up": [up_x, up_y, up_z]
        })

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float, float]:
        """Convert screen to world coordinates (not supported in web backend)."""
        # Would need round-trip to browser - return dummy for now
        return (0.0, 0.0, 0.0)


class WebRenderer(Renderer):
    """Web renderer using WebSocket to send commands to browser.

    Collects rendering commands during a frame and sends them
    as a batch via WebSocket when end_frame() is called.
    """

    def __init__(self) -> None:
        self._commands: list[dict] = []
        self._shapes = WebShapeRenderer(self._commands)
        self._display_lists = WebDisplayListManager(self._commands)
        self._view = WebViewStateManager(self._commands)
        self._event_loop: WebEventLoop | None = None
        self._clear_color: Color4 = (217, 217, 217, 255)

        # Wire shape renderer to display list manager for compile redirection
        self._shapes.set_display_list_manager(self._display_lists)

    def set_event_loop(self, event_loop: "WebEventLoop") -> None:
        """Set the event loop for sending messages."""
        self._event_loop = event_loop

    @property
    def shapes(self) -> WebShapeRenderer:
        """Access shape rendering methods."""
        return self._shapes

    @property
    def display_lists(self) -> WebDisplayListManager:
        """Access display list management."""
        return self._display_lists

    @property
    def view(self) -> WebViewStateManager:
        """Access view state management."""
        return self._view

    def clear(self, color: Color4 = (0, 0, 0, 255)) -> None:
        """Queue clear command."""
        self._clear_color = color
        self._commands.append({
            "cmd": "clear",
            "color": list(color)
        })

    def setup(self) -> None:
        """Initialize renderer."""
        pass

    def cleanup(self) -> None:
        """Clean up resources."""
        pass

    def begin_frame(self) -> None:
        """Begin a new frame - clear command buffer."""
        self._commands.clear()

    def end_frame(self) -> None:
        """End frame - send commands to browser.

        Sends every frame to the browser without throttling. The browser
        queues frames and renders one per requestAnimationFrame cycle,
        guaranteeing each frame is composited to screen.
        """
        if self._event_loop is not None and self._commands:
            message = json.dumps({
                "type": "frame",
                "commands": self._commands
            })
            self._event_loop.broadcast(message)

    def flush(self) -> None:
        """Flush pending commands."""
        pass

    def load_texture(self, file_path: str) -> TextureHandle | None:
        """Load texture (not yet supported)."""
        return None

    def bind_texture(self, texture: TextureHandle | None) -> None:
        """Bind texture (no-op)."""
        pass

    def delete_texture(self, texture: TextureHandle) -> None:
        """Delete texture (no-op)."""
        pass
