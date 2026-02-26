"""Per-client session for the web backend.

Each browser connection gets its own independent session with:
- Own AbstractApp (cube state, solver, operator)
- Own GCubeViewer
- Own WebAnimationManager
- Own rendering pipeline (command buffer + renderer sub-components)

This allows multiple browsers to interact with independent cubes simultaneously.
"""

from __future__ import annotations

import json
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from cube.application.exceptions.ExceptionAppExit import AppExit
from cube.presentation.gui.backends.web.WebRenderer import (
    WebDisplayListManager,
    WebShapeRenderer,
    WebViewStateManager,
)
from cube.presentation.gui.commands import Command, CommandContext
from cube.version import get_version

if TYPE_CHECKING:
    from aiohttp.web import WebSocketResponse

    from cube.application.AbstractApp import AbstractApp
    from cube.domain.algs.Alg import Alg
    from cube.domain.model import Edge, Part
    from cube.domain.model.Face import Face
    from cube.presentation.gui.backends.web.WebAnimationManager import WebAnimationManager
    from cube.presentation.gui.backends.web.WebEventLoop import WebEventLoop
    from cube.presentation.gui.commands import CommandSequence
    from cube.presentation.viewer.GCubeViewer import GCubeViewer


@dataclass
class ClientInfo:
    """Metadata about a connected client."""

    session_id: str
    ip: str
    city: str = "Unknown"
    country: str = "Unknown"
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SessionRenderer:
    """Lightweight renderer facade for a single session.

    Wraps per-session sub-components (shapes, display_lists, view) that each
    use this session's command buffer. Implements the Renderer protocol
    interface needed by GCubeViewer and AnimationManager.
    """

    def __init__(self, commands: list[dict]) -> None:
        self._commands = commands
        self._shapes = WebShapeRenderer(commands)
        self._display_lists = WebDisplayListManager(commands)
        self._view = WebViewStateManager(commands)

        # Wire shape renderer to display list manager for compile redirection
        self._shapes.set_display_list_manager(self._display_lists)

    @property
    def shapes(self) -> WebShapeRenderer:
        return self._shapes

    @property
    def display_lists(self) -> WebDisplayListManager:
        return self._display_lists

    @property
    def view(self) -> WebViewStateManager:
        return self._view

    def clear(self, color: tuple[int, int, int, int] = (0, 0, 0, 255)) -> None:
        self._commands.append({"cmd": "clear", "color": list(color)})

    def begin_frame(self) -> None:
        self._commands.clear()

    def end_frame(self) -> None:
        # No-op — ClientSession.on_draw() reads commands and sends them
        pass

    def setup(self) -> None:
        pass

    def cleanup(self) -> None:
        pass

    def flush(self) -> None:
        pass

    def load_texture(self, file_path: str) -> None:
        return None

    def bind_texture(self, texture: object) -> None:
        pass

    def delete_texture(self, texture: object) -> None:
        pass


class ClientSession:
    """An independent cube session for a single WebSocket client.

    Each session has its own app (cube + solver + operator), viewer,
    animation manager, and rendering pipeline. Messages from the browser
    are routed here by the event loop.
    """

    def __init__(
        self,
        ws: "WebSocketResponse",
        event_loop: "WebEventLoop",
        client_info: ClientInfo,
        gui_test_mode: bool = False,
    ) -> None:
        self._ws = ws
        self._event_loop = event_loop
        self.client_info = client_info

        # Per-session rendering command buffer
        self._commands: list[dict] = []
        self._renderer = SessionRenderer(self._commands)

        # Create independent app for this session
        from cube.application.AbstractApp import AbstractApp
        self._app: AbstractApp = AbstractApp.create_app()
        self._gui_test_mode = gui_test_mode

        # Set cube visibility (web is not headless — has visual output)
        self._app.cube.has_visible_presentation = True

        self._width: int = 720
        self._height: int = 720

        # State for edge solve tracking (used by SOLVE_EDGES command)
        self._last_edge_solve_count: int = 0

        # Create viewer with session's own renderer
        from cube.presentation.viewer.GCubeViewer import GCubeViewer
        self._viewer: GCubeViewer = GCubeViewer(
            self._app.cube, self._app.vs, self._renderer  # type: ignore[arg-type]
        )

        # Create non-blocking animation manager
        from cube.presentation.gui.backends.web.WebAnimationManager import WebAnimationManager
        am = WebAnimationManager(self._app.vs, self._app.op)
        self._app.enable_animation(am)
        am.set_event_loop(self._event_loop)
        am.set_window(self)  # type: ignore[arg-type]
        am.set_web_window(self)  # type: ignore[arg-type]
        self._animation_manager: WebAnimationManager = am

    @property
    def app(self) -> "AbstractApp":
        return self._app

    @property
    def viewer(self) -> "GCubeViewer":
        return self._viewer

    @property
    def renderer(self) -> SessionRenderer:
        return self._renderer

    @property
    def animation_running(self) -> bool:
        return bool(self._animation_manager and self._animation_manager.animation_running())

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def backend(self) -> object:
        """Stub for CommandContext compatibility."""
        return None

    # ── Send helpers (unicast to this session's WebSocket) ──

    def _send(self, message: str) -> None:
        """Send a message to this session's WebSocket client."""
        self._event_loop.send_to(self._ws, message)

    def send_version(self) -> None:
        self._send(json.dumps({"type": "version", "version": get_version()}))

    def send_speed(self) -> None:
        speed_index = self._app.vs.get_speed_index
        self._send(json.dumps({"type": "speed_update", "value": speed_index}))

    def send_size(self) -> None:
        size = self._app.vs.cube_size
        self._send(json.dumps({"type": "size_update", "value": size}))

    def send_toolbar_state(self) -> None:
        from cube.domain.solver.SolverName import SolverName
        app = self._app
        solver_list = [s.display_name for s in SolverName.implemented()]
        self._send(json.dumps({
            "type": "toolbar_state",
            "debug": app.config.solver_debug,
            "animation": app.op.animation_enabled,
            "solver_name": app.slv.name,
            "solver_list": solver_list,
        }))

    def send_cube_info(self) -> None:
        cell_size: int = self._app.vs.config.cell_size
        face_size: float = 3.0 * cell_size
        half: float = face_size / 2.0
        cube_size: int = self._app.vs.cube_size

        self._send(json.dumps({
            "type": "cube_info",
            "size": cube_size,
            "faceSize": face_size,
            "faces": {
                "F": {"center": [half, half, face_size], "right": [1, 0, 0], "up": [0, 1, 0]},
                "B": {"center": [half, half, 0], "right": [-1, 0, 0], "up": [0, 1, 0]},
                "R": {"center": [face_size, half, half], "right": [0, 0, -1], "up": [0, 1, 0]},
                "L": {"center": [0, half, half], "right": [0, 0, 1], "up": [0, 1, 0]},
                "U": {"center": [half, face_size, half], "right": [1, 0, 0], "up": [0, 0, -1]},
                "D": {"center": [half, 0, half], "right": [1, 0, 0], "up": [0, 0, 1]},
            }
        }))

    def send_text(self) -> None:
        """Send animation text and status info to this client."""
        vs = self._app.vs
        app = self._app
        at = vs.animation_text

        anim_lines: list[dict[str, object]] = []
        animation_text_props = app.config.animation_text
        for i in range(3):
            line = at.get_line(i)
            if line:
                prop = animation_text_props[i]
                color: tuple[int, int, int, int] = prop[3]
                anim_lines.append({
                    "text": line,
                    "size": prop[2],
                    "color": f"rgba({color[0]},{color[1]},{color[2]},{color[3] / 255:.2f})",
                    "bold": prop[4],
                })

        slv = app.slv
        self._send(json.dumps({
            "type": "text_update",
            "animation": anim_lines,
            "status": slv.status,
            "solver": slv.name,
            "moves": app.op.count,
        }))

    def send_flush_queue(self) -> None:
        """Tell the client to discard all queued frames.

        Called when animation is cancelled so the client immediately
        shows the current state instead of draining stale frames.
        """
        self._send(json.dumps({"type": "flush_queue"}))

    def send_session_id(self) -> None:
        """Send session ID to the client."""
        self._send(json.dumps({
            "type": "session_id",
            "session_id": self.client_info.session_id,
        }))

    # ── Drawing ──

    def on_draw(self) -> None:
        """Render a frame and send it to this client."""
        import math

        self._renderer.begin_frame()
        self._renderer.clear((217, 217, 217, 255))

        vs = self._app.vs
        self._renderer.view.set_projection(self._width, self._height, fov_y=float(vs.fov_y))
        self._renderer.view.load_identity()

        offset = vs.offset
        self._renderer.view.translate(float(offset[0]), float(offset[1]), float(offset[2]))

        self._renderer.view.rotate(math.degrees(vs.alpha_x_0), 1, 0, 0)
        self._renderer.view.rotate(math.degrees(vs.alpha_y_0), 0, 1, 0)
        self._renderer.view.rotate(math.degrees(vs.alpha_z_0), 0, 0, 1)

        self._renderer.view.rotate(math.degrees(vs.alpha_x), 1, 0, 0)
        self._renderer.view.rotate(math.degrees(vs.alpha_y), 0, 1, 0)
        self._renderer.view.rotate(math.degrees(vs.alpha_z), 0, 0, 1)

        self._viewer.draw()

        if self._animation_manager:
            self._animation_manager.draw()

        # Don't call end_frame() on renderer — we send commands directly
        if self._commands:
            message = json.dumps({"type": "frame", "commands": self._commands})
            self._send(message)

        self.send_text()

    # ── Update ──

    def update_gui_elements(self) -> None:
        """Update all GUI elements and redraw."""
        if self._viewer:
            self._viewer.update()
        if self._animation_manager:
            self._animation_manager.update_gui_elements()
        self.on_draw()

    # ── Client connected ──

    def on_client_connected(self) -> None:
        """Send initial state to newly connected client."""
        print(f"Session {self.client_info.session_id[:8]} - sending initial frame", flush=True)
        self.send_session_id()
        self.send_version()
        self.send_speed()
        self.send_size()
        self.send_toolbar_state()
        self.send_cube_info()
        self.on_draw()

    # ── Message handling ──

    def handle_message(self, data: dict) -> None:
        """Handle a parsed JSON message from the browser."""
        msg_type = data.get("type")

        if msg_type == "connected":
            self.on_client_connected()

        elif msg_type == "key":
            keycode = data.get("code", 0)
            modifiers = data.get("modifiers", 0)
            key_char = data.get("key", "")
            symbol = self._event_loop._js_keycode_to_symbol(keycode, key_char)
            self._handle_key(symbol, modifiers)

        elif msg_type == "set_speed":
            self._handle_speed(data.get("value", 0))

        elif msg_type == "set_size":
            self._handle_size(data.get("value", 3))

        elif msg_type == "set_solver":
            solver_name = data.get("name", "")
            if solver_name:
                self._handle_solver(solver_name)

        elif msg_type == "command":
            self._handle_command(data.get("name", ""))

        elif msg_type == "mouse_rotate_view":
            self._handle_mouse_rotate(data.get("dx", 0.0), data.get("dy", 0.0))

        elif msg_type == "mouse_pan":
            self._handle_mouse_pan(data.get("dx", 0.0), data.get("dy", 0.0))

        elif msg_type == "mouse_face_turn":
            self._handle_mouse_face_turn(
                data.get("face", ""),
                data.get("row", 0), data.get("col", 0),
                data.get("si", -1), data.get("sx", -1), data.get("sy", -1),
                data.get("on_left_to_right", 0.0), data.get("on_left_to_top", 0.0),
            )

        elif msg_type == "resize":
            pass  # Could update width/height

    # ── Input handlers ──

    def _handle_key(self, symbol: int, modifiers: int) -> None:
        from cube.presentation.gui.key_bindings import lookup_command
        command = lookup_command(symbol, modifiers, self.animation_running)
        if command:
            self.inject_command(command)

    def _handle_speed(self, speed_index: int) -> None:
        from cube.application.state import speeds
        clamped = max(0, min(len(speeds) - 1, speed_index))
        self._app.vs._speed = clamped

    def _handle_size(self, size: int) -> None:
        clamped = max(3, min(7, size))
        vs = self._app.vs
        if clamped != vs.cube_size:
            vs.cube_size = clamped
            self._app.cube.reset(clamped)
            self._app.op.reset()
            self.update_gui_elements()
            self.send_cube_info()

    def _handle_solver(self, name: str) -> None:
        from cube.domain.solver.SolverName import SolverName
        try:
            solver_name = SolverName.lookup(name)
        except ValueError:
            print(f"Unknown solver: {name}", flush=True)
            return
        if self._app.slv.get_code is solver_name:
            return
        self._app.switch_to_solver(solver_name)
        self._app.op.reset()
        self.update_gui_elements()
        self.send_toolbar_state()

    def _handle_command(self, command_name: str) -> None:
        from cube.presentation.gui.commands import Commands

        if command_name == "solve":
            self._two_phase_solve()
            return

        command_map: dict[str, Command] = {
            "solve_instant": Commands.SOLVE_ALL_NO_ANIMATION,
            "scramble": Commands.SCRAMBLE_1,
            "reset": Commands.RESET_CUBE,
            "stop": Commands.STOP_ANIMATION,
            "toggle_debug": Commands.TOGGLE_DEBUG,
            "toggle_animation": Commands.TOGGLE_ANIMATION,
            "ROTATE_R": Commands.ROTATE_R,
            "ROTATE_R_PRIME": Commands.ROTATE_R_PRIME,
            "ROTATE_L": Commands.ROTATE_L,
            "ROTATE_L_PRIME": Commands.ROTATE_L_PRIME,
            "ROTATE_U": Commands.ROTATE_U,
            "ROTATE_U_PRIME": Commands.ROTATE_U_PRIME,
            "ROTATE_D": Commands.ROTATE_D,
            "ROTATE_D_PRIME": Commands.ROTATE_D_PRIME,
            "ROTATE_F": Commands.ROTATE_F,
            "ROTATE_F_PRIME": Commands.ROTATE_F_PRIME,
            "ROTATE_B": Commands.ROTATE_B,
            "ROTATE_B_PRIME": Commands.ROTATE_B_PRIME,
            "SLICE_M": Commands.SLICE_M,
            "SLICE_M_PRIME": Commands.SLICE_M_PRIME,
            "SLICE_E": Commands.SLICE_E,
            "SLICE_E_PRIME": Commands.SLICE_E_PRIME,
            "SLICE_S": Commands.SLICE_S,
            "SLICE_S_PRIME": Commands.SLICE_S_PRIME,
            "ZOOM_IN": Commands.ZOOM_IN,
            "ZOOM_OUT": Commands.ZOOM_OUT,
        }

        command = command_map.get(command_name)
        if command:
            self.inject_command(command)
            self.send_toolbar_state()
            if command_name in ("ZOOM_IN", "ZOOM_OUT"):
                self.update_gui_elements()

    def _handle_mouse_rotate(self, dx: float, dy: float) -> None:
        import math
        vs = self._app.vs
        vs.alpha_x += math.radians(dy)
        vs.alpha_y += math.radians(dx)
        self.on_draw()

    def _handle_mouse_pan(self, dx: float, dy: float) -> None:
        vs = self._app.vs
        vs.change_offset(dx, -dy, 0)
        self.on_draw()

    def _handle_mouse_face_turn(
        self, face_name: str, row: int, col: int,
        si: int, sx: int, sy: int,
        on_left_to_right: float, on_left_to_top: float,
    ) -> None:
        from cube.domain.algs.Algs import Algs
        from cube.domain.model import Corner, Edge, Center
        from cube.domain.model.FaceName import FaceName

        cube = self._app.cube
        try:
            fn = FaceName[face_name]
        except KeyError:
            print(f"Unknown face: {face_name}", flush=True)
            return

        face: Face = cube.face(fn)
        it_left_to_right = abs(on_left_to_right) > abs(on_left_to_top)
        part = self._grid_to_part(face, row, col)
        if part is None:
            return

        alg: Alg | None = None
        inv = False

        if isinstance(part, Corner):
            alg = Algs.of_face(face.name)
            if part is face.corner_top_right:
                inv = on_left_to_right < 0 if it_left_to_right else on_left_to_top > 0
            elif part is face.corner_top_left:
                inv = on_left_to_right < 0 if it_left_to_right else on_left_to_top < 0
            elif part is face.corner_bottom_left:
                inv = on_left_to_right > 0 if it_left_to_right else on_left_to_top < 0
            else:
                inv = on_left_to_right > 0 if it_left_to_right else on_left_to_top > 0

        elif isinstance(part, Edge):
            if part is face.edge_right:
                if it_left_to_right:
                    alg = self._slice_on_edge_alg(part, face, si)
                    inv = on_left_to_right < 0
                else:
                    alg = Algs.of_face(face.name)
                    inv = on_left_to_top > 0
            elif part is face.edge_left:
                if it_left_to_right:
                    alg = self._slice_on_edge_alg(part, face, si)
                    inv = on_left_to_right < 0
                else:
                    alg = Algs.of_face(face.name)
                    inv = on_left_to_top < 0
            elif part is face.edge_top:
                if not it_left_to_right:
                    alg = self._slice_on_edge_alg(part, face, si)
                    inv = on_left_to_top < 0
                else:
                    alg = Algs.of_face(face.name)
                    inv = on_left_to_right < 0
            elif part is face.edge_bottom:
                if not it_left_to_right:
                    alg = self._slice_on_edge_alg(part, face, si)
                    inv = on_left_to_top < 0
                else:
                    alg = Algs.of_face(face.name)
                    inv = on_left_to_right > 0

        elif isinstance(part, Center):
            if it_left_to_right:
                alg = self._slice_on_edge_alg(
                    face.edge_right, face, sy, on_center=True)
                inv = on_left_to_right < 0
            else:
                alg = self._slice_on_edge_alg(
                    face.edge_top, face, sx, on_center=True)
                inv = on_left_to_top < 0

        if alg:
            if inv:
                alg = alg.inv()
            op = self._app.op
            op.play(alg, animation=True)
            if not op.animation_enabled:
                self.update_gui_elements()

    @staticmethod
    def _grid_to_part(face: "Face", row: int, col: int) -> "Part | None":
        grid_map: dict[tuple[int, int], Part] = {
            (2, 0): face.corner_top_left,
            (2, 1): face.edge_top,
            (2, 2): face.corner_top_right,
            (1, 0): face.edge_left,
            (1, 1): face.center,
            (1, 2): face.edge_right,
            (0, 0): face.corner_bottom_left,
            (0, 1): face.edge_bottom,
            (0, 2): face.corner_bottom_right,
        }
        return grid_map.get((row, col))

    @staticmethod
    def _slice_on_edge_alg(part: "Edge", face: "Face", index: int,
                           on_center: bool = False) -> "Alg":
        from cube.domain.algs.Algs import Algs
        from cube.domain.model.FaceName import FaceName

        face_name: FaceName = face.name
        slice_alg_base: Alg
        neg_slice_index: bool
        inv: bool = False

        if face_name in (FaceName.F, FaceName.B):
            if face.is_bottom_or_top(part):
                slice_alg_base = Algs.M
                neg_slice_index = face_name == FaceName.B
                inv = face_name == FaceName.F
            else:
                slice_alg_base = Algs.E
                neg_slice_index = False
        elif face_name in (FaceName.R, FaceName.L):
            if face.is_bottom_or_top(part):
                slice_alg_base = Algs.S
                neg_slice_index = face_name == FaceName.L
                inv = face_name == FaceName.R
            else:
                slice_alg_base = Algs.E
                neg_slice_index = False
        elif face_name in (FaceName.U, FaceName.D):
            if face.is_bottom_or_top(part):
                slice_alg_base = Algs.M
                neg_slice_index = False
            else:
                slice_alg_base = Algs.S
                neg_slice_index = face_name == FaceName.D
                inv = face_name == FaceName.D
        else:
            return Algs.M

        if not on_center:
            index = part.get_face_ltr_index_from_edge_slice_index(face, index)

        if neg_slice_index:
            index = face.inv(index)

        slice_alg = slice_alg_base[index + 1]

        if inv:
            return slice_alg.prime
        return slice_alg

    # ── Solve ──

    def _two_phase_solve(self) -> None:
        try:
            app = self._app
            slv = app.slv
            solution_alg = slv.solution()
            if solution_alg.count() == 0:
                return
            solution_alg = solution_alg.simplify()
            app.op.play(solution_alg)
            self.update_gui_elements()
            self.send_toolbar_state()
        except Exception as e:
            traceback.print_exc()
            self._app.set_error(f"Solve error: {e}")
            self.update_gui_elements()

    # ── Command injection ──

    def inject_command(self, command: Command) -> None:
        from cube.presentation.gui.commands import Commands

        if command is Commands.SOLVE_ALL:
            self._two_phase_solve()
            return

        if command is Commands.STOP_ANIMATION:
            self.send_flush_queue()
            self._animation_manager.cancel_animation()
            return

        try:
            speed_before = self._app.vs.get_speed_index
            size_before = self._app.vs.cube_size
            ctx = CommandContext.from_window(self)  # type: ignore[arg-type]
            result = command.execute(ctx)
            if self._app.vs.get_speed_index != speed_before:
                self.send_speed()
            if self._app.vs.cube_size != size_before:
                self.send_size()
            self.send_toolbar_state()
            if not result.no_gui_update and not self.animation_running:
                self.update_gui_elements()
        except AppExit:
            print(f"Session {self.client_info.session_id[:8]} closing...", flush=True)
        except Exception as e:
            cfg = self._app.config
            if cfg.gui_test_mode and cfg.quit_on_error_in_test_mode:
                raise
            else:
                traceback.print_exc()
                msg = str(e)
                error_text = "Some error occurred:"
                if msg:
                    error_text += msg
                self._app.set_error(error_text)
                self.update_gui_elements()

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a key press event (for testing)."""
        self._handle_key(key, modifiers)

    def schedule_once(self, callback: Callable[[float], None], delay: float) -> None:
        self._event_loop.schedule_once(callback, delay)

    def inject_command_sequence(
        self,
        commands: "CommandSequence | list[Command]",
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        if isinstance(commands, list):
            cmd_list = commands
        else:
            cmd_list = list(commands)

        if not cmd_list:
            if on_complete:
                on_complete()
            return

        def execute_next(index: int) -> None:
            if index >= len(cmd_list):
                if on_complete:
                    on_complete()
                return
            cmd = cmd_list[index]
            result = cmd.execute(CommandContext.from_window(self))  # type: ignore[arg-type]
            if not result.no_gui_update:
                self.update_gui_elements()
            if result.delay_next_command > 0:
                def continue_sequence(_dt: float) -> None:
                    execute_next(index + 1)
                self.schedule_once(continue_sequence, result.delay_next_command)
            else:
                execute_next(index + 1)

        execute_next(0)

    # ── Stub methods for AppWindow protocol compatibility ──

    def set_mouse_visible(self, visible: bool) -> None:
        pass

    def get_opengl_info(self) -> str:
        return "Web Backend (WebGL in browser)"

    def adjust_brightness(self, delta: float) -> float | None:
        return None

    def get_brightness(self) -> float | None:
        return None

    def adjust_background(self, delta: float) -> float | None:
        return None

    def get_background(self) -> float | None:
        return None

    def next_texture_set(self) -> str | None:
        return None

    def prev_texture_set(self) -> str | None:
        return None

    def toggle_texture(self) -> bool:
        return False

    def load_texture_set(self, directory: str) -> int:
        return 0

    def show_popup(self, title: str, lines: list[str],
                   line_colors: list[tuple[int, int, int, int]] | None = None) -> None:
        pass

    # ── Cleanup ──

    def cleanup(self) -> None:
        """Clean up session resources."""
        if self._viewer:
            self._viewer.cleanup()
        self._renderer.cleanup()

    # Alias used by WebAnimationManager
    def _on_draw(self) -> None:
        """Alias for on_draw, matching the WebAppWindow interface."""
        self.on_draw()
