"""Per-client session for the webgl backend.

Each browser connection gets its own independent session with:
- Own AbstractApp (cube state, solver, operator)
- Own WebglAnimationManager (sends animation events, not frames)
- No per-session renderer — rendering is entirely client-side

Unlike the web backend which sends rendering commands per frame,
this backend sends:
- cube_state: face colors as NxN grid of RGB values
- animation_start: face rotation event for client-side animation
- animation_stop: cancel client animations
- text_update: solver status, move count, animation text
"""

from __future__ import annotations

import json
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from cube.application.exceptions.ExceptionAppExit import AppExit
from cube.presentation.gui.backends.webgl.CubeStateSerializer import extract_cube_state
from cube.presentation.gui.commands import Command, CommandContext
from cube.version import get_version

if TYPE_CHECKING:
    from aiohttp.web import WebSocketResponse

    from cube.application.AbstractApp import AbstractApp
    from cube.domain.algs.Alg import Alg
    from cube.domain.model import Edge, Part
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face
    from cube.presentation.gui.backends.webgl.WebglAnimationManager import WebglAnimationManager
    from cube.presentation.gui.backends.webgl.WebglEventLoop import WebglEventLoop
    from cube.presentation.gui.backends.webgl.WebglRenderer import WebglRenderer
    from cube.presentation.gui.commands import CommandSequence


@dataclass
class ClientInfo:
    """Metadata about a connected client."""
    session_id: str
    ip: str
    city: str = "Unknown"
    country: str = "Unknown"
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ClientSession:
    """An independent cube session for a single WebSocket client.

    Each session has its own app (cube + solver + operator) and animation
    manager. No per-session renderer — rendering is entirely client-side.
    The server sends cube state and animation events.
    """

    def __init__(
        self,
        ws: "WebSocketResponse",
        event_loop: "WebglEventLoop",
        client_info: ClientInfo,
        gui_test_mode: bool = False,
    ) -> None:
        self._ws = ws
        self._event_loop = event_loop
        self.client_info = client_info

        # Create independent app for this session
        from cube.application.AbstractApp import AbstractApp
        self._app: AbstractApp = AbstractApp.create_app()
        self._gui_test_mode = gui_test_mode

        self._app.cube.has_visible_presentation = True

        self._width: int = 720
        self._height: int = 720

        self._last_edge_solve_count: int = 0

        # No viewer needed — rendering is client-side
        # But we need a no-op renderer for the AnimationManager protocol
        from cube.presentation.gui.backends.webgl.WebglRenderer import WebglRenderer
        self._renderer: WebglRenderer = WebglRenderer()

        # Create animation manager
        from cube.presentation.gui.backends.webgl.WebglAnimationManager import WebglAnimationManager
        am = WebglAnimationManager(self._app.vs, self._app.op)
        self._app.enable_animation(am)
        am.set_event_loop(self._event_loop)
        am.set_window(self)  # type: ignore[arg-type]
        am.set_web_window(self)
        self._animation_manager: WebglAnimationManager = am

    @property
    def app(self) -> "AbstractApp":
        return self._app

    @property
    def viewer(self) -> None:
        """No viewer — rendering is client-side."""
        return None

    @property
    def renderer(self) -> "WebglRenderer":
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
        return None

    # -- Send helpers (unicast to this session's WebSocket) --

    def _send(self, message: str) -> None:
        self._event_loop.send_to(self._ws, message)

    def send_version(self) -> None:
        self._send(json.dumps({"type": "version", "version": get_version()}))

    def send_client_count(self, count: int) -> None:
        self._send(json.dumps({"type": "client_count", "count": count}))

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
        vs = app.vs
        self._send(json.dumps({
            "type": "toolbar_state",
            "debug": app.config.solver_debug,
            "animation": app.op.animation_enabled,
            "solver_name": app.slv.name,
            "solver_list": solver_list,
            "slice_start": vs.slice_start,
            "slice_stop": vs.slice_stop,
        }))

    def send_color_map(self) -> None:
        """Send color name → RGB mapping to client (once at connection).

        The client uses this to build a PBR-optimized color palette keyed
        by color name, so it doesn't depend on exact server RGB values.
        """
        from cube.domain.model.Color import Color, color2rgb_int
        colors: dict[str, list[int]] = {}
        for color in Color:
            rgb = color2rgb_int(color)
            colors[color.name.lower()] = list(rgb)
        self._send(json.dumps({"type": "color_map", "colors": colors}))

    def send_cube_state(self) -> None:
        """Send current cube face colors to the client."""
        state = extract_cube_state(self._app.cube)
        self._send(json.dumps(state))

    def send_animation_start(self, alg: "Alg", duration_ms: int) -> None:
        """Send animation start event with post-move state embedded.

        The model change has already been applied before this is called,
        so extract_cube_state returns the post-move state. This ensures the
        client applies the correct final state when the animation completes.

        Sends physical layer columns (0-based from the negative side of the axis)
        so the client knows which stickers to animate. For example on a 4x4:
          R    → layers=[3]       (rightmost column)
          R[2] → layers=[2]       (second from right)
          M[1] → layers=[1]       (first inner column)
          M    → layers=[1, 2]    (all inner columns)
        """
        from cube.domain import algs as alg_types

        face_name: str = ""
        direction: int = 1  # 1=CW, -1=CCW
        layers: list[int] = [0]
        cube = self._app.cube
        size: int = cube.size

        if isinstance(alg, alg_types.AnimationAbleAlg):
            # Extract face name and direction from the algorithm
            face_name = self._alg_to_face_name(alg)
            n: int = alg.n if hasattr(alg, 'n') else 1
            direction = 1 if n % 4 == 1 else -1
            if n % 4 == 3:
                direction = -1
            elif n % 4 == 2:
                direction = 2  # 180 degrees

            # Extract physical layer columns from algorithm
            layers = self._extract_layers(alg, cube, size, face_name)

        alg_str: str = str(alg)
        alg_type: str = type(alg).__name__
        vs = self._app.vs
        print(f"  anim: {alg_str} type={alg_type} face={face_name} "
              f"layers={layers} dir={direction} size={size} "
              f"slice=[{vs.slice_start}:{vs.slice_stop}]", flush=True)

        # Embed post-move state so the client has correct colors at animation end
        state = extract_cube_state(self._app.cube)

        self._send(json.dumps({
            "type": "animation_start",
            "face": face_name,
            "direction": direction,
            "layers": layers,
            "duration_ms": duration_ms,
            "alg": alg_str,
            "alg_type": alg_type,
            "state": state,
        }))

    def send_animation_stop(self) -> None:
        """Tell the client to stop all animations and snap to state."""
        self._send(json.dumps({"type": "animation_stop"}))

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
        self._send(json.dumps({"type": "flush_queue"}))

    def send_session_id(self) -> None:
        self._send(json.dumps({
            "type": "session_id",
            "session_id": self.client_info.session_id,
        }))

    # -- Update --

    def update_gui_elements(self) -> None:
        """Send updated cube state and text to client."""
        self.send_cube_state()
        self.send_text()

    # -- Client connected --

    def on_client_connected(self) -> None:
        """Send initial state to newly connected client."""
        print(f"Session {self.client_info.session_id[:8]} - sending initial state", flush=True)
        self.send_session_id()
        self.send_color_map()
        self.send_version()
        self.send_speed()
        self.send_size()
        self.send_toolbar_state()
        self.send_cube_state()
        self.send_text()

    # -- Message handling --

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
            pass

    # -- Input handlers --

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
            self.send_cube_state()
            self.send_text()

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
        self.send_cube_state()
        self.send_text()
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

    def _handle_mouse_rotate(self, dx: float, dy: float) -> None:
        # Client handles orbit camera locally — no server round-trip needed
        # This message is kept for parity but the client handles rotation itself
        pass

    def _handle_mouse_pan(self, dx: float, dy: float) -> None:
        # Client handles pan locally
        pass

    # Face axes (matching client FACE_DEFS) — used for adjacent face lookup
    _FACE_AXES: dict[str, dict[str, tuple[int, int, int]]] = {
        'U': {'right': (1, 0, 0), 'up': (0, 0, -1)},
        'D': {'right': (1, 0, 0), 'up': (0, 0, 1)},
        'F': {'right': (1, 0, 0), 'up': (0, 1, 0)},
        'B': {'right': (-1, 0, 0), 'up': (0, 1, 0)},
        'R': {'right': (0, 0, -1), 'up': (0, 1, 0)},
        'L': {'right': (0, 0, 1), 'up': (0, 1, 0)},
    }

    # Map axis-aligned unit vector to face name
    _VEC_TO_FACE: dict[tuple[int, int, int], str] = {
        (1, 0, 0): 'R', (-1, 0, 0): 'L',
        (0, 1, 0): 'U', (0, -1, 0): 'D',
        (0, 0, 1): 'F', (0, 0, -1): 'B',
    }

    @classmethod
    def _get_adjacent_face_name(cls, face_name: str, position: str) -> str:
        """Get the adjacent face in a direction relative to the given face.

        position: 'top' | 'bottom' | 'left' | 'right'
        """
        axes = cls._FACE_AXES[face_name]
        if position == 'top':
            vec = axes['up']
        elif position == 'bottom':
            vec = tuple(-v for v in axes['up'])
        elif position == 'right':
            vec = axes['right']
        elif position == 'left':
            vec = tuple(-v for v in axes['right'])
        else:
            raise ValueError(f"Unknown position: {position}")
        return cls._VEC_TO_FACE[vec]

    def _handle_mouse_face_turn(
        self, face_name: str, row: int, col: int,
        si: int, sx: int, sy: int,
        on_left_to_right: float, on_left_to_top: float,
    ) -> None:
        """Handle mouse face turn with consistent row/column rotation rules.

        Rules (same for ALL sticker types — corner, edge, center):
          - Drag horizontal (along face right axis) → rotate the ROW
          - Drag vertical   (along face up axis)    → rotate the COLUMN

        Row mapping:  row 0 → bottom-adjacent face, row N-1 → top-adjacent face,
                      inner row → horizontal slice (E-type)
        Col mapping:  col 0 → left-adjacent face, col N-1 → right-adjacent face,
                      inner col → vertical slice (M-type)
        """
        from cube.domain.algs.Algs import Algs
        from cube.domain.model.FaceName import FaceName

        cube = self._app.cube
        size: int = cube.size
        last: int = size - 1

        try:
            fn = FaceName[face_name]
        except KeyError:
            print(f"Unknown face: {face_name}", flush=True)
            return

        face: Face = cube.face(fn)
        is_horizontal: bool = abs(on_left_to_right) > abs(on_left_to_top)

        alg: Alg | None = None
        inv: bool = False

        if is_horizontal:
            # ── Horizontal drag → rotate the ROW ──
            if row == last:
                adj_fn = FaceName[self._get_adjacent_face_name(face_name, 'top')]
                alg = Algs.of_face(adj_fn)
                inv = on_left_to_right > 0
            elif row == 0:
                adj_fn = FaceName[self._get_adjacent_face_name(face_name, 'bottom')]
                alg = Algs.of_face(adj_fn)
                inv = on_left_to_right < 0
            else:
                # Inner row → horizontal slice (uses edge_right to determine axis)
                alg = self._slice_on_edge_alg(
                    face.edge_right, face, row - 1, on_center=True)
                inv = on_left_to_right < 0
        else:
            # ── Vertical drag → rotate the COLUMN ──
            if col == last:
                adj_fn = FaceName[self._get_adjacent_face_name(face_name, 'right')]
                alg = Algs.of_face(adj_fn)
                inv = on_left_to_top < 0
            elif col == 0:
                adj_fn = FaceName[self._get_adjacent_face_name(face_name, 'left')]
                alg = Algs.of_face(adj_fn)
                inv = on_left_to_top > 0
            else:
                # Inner col → vertical slice (uses edge_top to determine axis)
                alg = self._slice_on_edge_alg(
                    face.edge_top, face, col - 1, on_center=True)
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
        """Map grid (row, col) to a cube Part for any NxN cube.

        Row 0 is bottom, row N-1 is top. Col 0 is left, col N-1 is right.
        """
        size: int = face.cube.size
        last: int = size - 1
        # Corners (at the four extremes)
        if row == last and col == 0:
            return face.corner_top_left
        if row == last and col == last:
            return face.corner_top_right
        if row == 0 and col == 0:
            return face.corner_bottom_left
        if row == 0 and col == last:
            return face.corner_bottom_right
        # Edges (one coordinate at the boundary, other in interior)
        if row == last:
            return face.edge_top
        if row == 0:
            return face.edge_bottom
        if col == last:
            return face.edge_right
        if col == 0:
            return face.edge_left
        # Center (both coordinates in interior)
        return face.center

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

    @staticmethod
    def _alg_to_face_name(alg: "Alg") -> str:
        """Extract the face name from an algorithm string for animation.

        Handles formats like: "R", "R'", "U2", "M", "[2:2]M", "[1:2]R", "X",
        "Rw" (double layer), "d" (wide face, lowercase).
        """
        s = str(alg).strip()
        if not s:
            return ""
        face_map: dict[str, str] = {
            "R": "R", "L": "L", "U": "U", "D": "D", "F": "F", "B": "B",
            "M": "M", "E": "E", "S": "S",
            "x": "x", "y": "y", "z": "z",
            "X": "x", "Y": "y", "Z": "z",
            # Wide face moves use lowercase face letters
            "r": "R", "l": "L", "u": "U", "d": "D", "f": "F", "b": "B",
        }
        # Search for a known face letter in the string
        for ch in s:
            if ch in face_map:
                return face_map[ch]
        return ""

    @staticmethod
    def _face_indices_to_layers(
        indices: list[int], face_name: str, size: int
    ) -> list[int]:
        """Convert 0-based face/slice indices to physical layer columns.

        Physical columns are 0-based from the negative side of the axis:
          Column 0 = leftmost/bottommost/backmost
          Column size-1 = rightmost/topmost/frontmost
        """
        positive_faces: set[str] = {'R', 'U', 'F'}
        if face_name in positive_faces:
            return [size - 1 - i for i in indices]
        return list(indices)

    def _extract_layers(
        self, alg: "Alg", cube: "Cube", size: int, face_name: str
    ) -> list[int]:
        """Extract physical layer columns from an algorithm for animation.

        Returns 0-based column indices from the negative side of the axis.
        """
        from cube.domain import algs as alg_types
        from cube.domain.algs.WideFaceAlg import WideFaceAlg
        from cube.domain.algs.DoubleLayerAlg import DoubleLayerAlg

        if isinstance(alg, alg_types.SliceAlgBase):
            # M, E, S moves: inner slices
            # M follows L (negative X), E follows D (negative Y): column = index + 1
            # S follows F (positive Z): column = size - 2 - index
            indices: list[int] = list(alg.normalize_slice_index(
                n_max=cube.n_slices,
                _default=range(1, cube.n_slices + 1)
            ))
            if face_name == "S":
                return [size - 2 - i for i in indices]
            return [i + 1 for i in indices]

        if isinstance(alg, alg_types.FaceAlgBase):
            # R, L, U, D, F, B face moves (including SlicedFaceAlg)
            indices = list(alg.normalize_slice_index(
                n_max=1 + cube.n_slices,
                _default=[1]
            ))
            return self._face_indices_to_layers(indices, face_name, size)

        if isinstance(alg, DoubleLayerAlg):
            # Rw = R[1:size-1] — resolve to SlicedFaceAlg and extract
            resolved: alg_types.FaceAlgBase = alg.compose_base_alg(cube)
            indices = list(resolved.normalize_slice_index(
                n_max=1 + cube.n_slices,
                _default=[1]
            ))
            return self._face_indices_to_layers(indices, face_name, size)

        if isinstance(alg, WideFaceAlg):
            # Wide face: face + all inner layers = [0, 1, ..., size-2]
            indices = list(range(size - 1))
            return self._face_indices_to_layers(indices, face_name, size)

        # Whole cube rotations or unknown: default layer [0]
        # (client selects ALL stickers for x/y/z anyway)
        return [0]

    # -- Solve --

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

    # -- Command injection --

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

    # -- Stub methods for AppWindow protocol compatibility --

    def set_mouse_visible(self, visible: bool) -> None:
        pass

    def get_opengl_info(self) -> str:
        return "WebGL Backend (client-side Three.js rendering)"

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

    # -- Cleanup --

    def cleanup(self) -> None:
        self._renderer.cleanup()

    # Alias used by WebglAnimationManager
    def _on_draw(self) -> None:
        """Send cube state (alias for compatibility)."""
        self.send_cube_state()
