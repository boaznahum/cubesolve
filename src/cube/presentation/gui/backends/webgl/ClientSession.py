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

import asyncio
import json
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from cube.application.exceptions.ExceptionAppExit import AppExit
from cube.presentation.gui.backends.webgl.CubeStateSerializer import extract_cube_state
from cube.presentation.gui.backends.webgl.FlowStateMachine import FlowEvent, FlowState, FlowStateMachine
from cube.presentation.gui.backends.webgl.SessionState import SessionStateSnapshot
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

        # Wrap op.undo so _is_undo flag is set automatically for ALL undo paths
        _orig_undo = self._app.op.undo

        def _undo_with_flag(animation: bool = True) -> "Alg | None":
            am._is_undo = True
            try:
                return _orig_undo(animation)
            finally:
                am._is_undo = False

        self._app.op.undo = _undo_with_flag  # type: ignore[assignment]

        # Flow state machine — single source of truth for all flow control
        self._fsm: FlowStateMachine = FlowStateMachine()

        # Wire queue-drained callback: when AM finishes all animations for a
        # single redo/undo/face-turn, transition FSM from ANIMATING → READY/IDLE
        def _on_am_queue_drained() -> None:
            if self._fsm.state == FlowState.ANIMATING:
                has_redo = bool(self._app.op.redo_queue())
                has_history = bool(self._app.op.history())
                self._fsm.send(FlowEvent.ANIM_DONE, has_redo=has_redo, has_history=has_history)
                self.send_state()

        am.set_on_queue_drained(_on_am_queue_drained)

        # Client count — set externally by SessionManager
        self._client_count: int = 0

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

    # -- Reconnection --

    def reattach(self, ws: "WebSocketResponse") -> None:
        """Reattach this session to a new WebSocket after reconnect.

        Swaps the underlying WebSocket, resets flow state via FSM RECONNECT
        event, and resends the full state. This fixes the bug where
        _fast_playing stayed True after reconnect (play button disabled).
        """
        self._ws = ws
        # Cancel any in-flight animation state
        self._animation_manager.cancel_animation()
        # FSM RECONNECT: transitions to IDLE or READY based on queue
        has_redo = bool(self._app.op.redo_queue())
        has_history = bool(self._app.op.history())
        self._fsm.send_reconnect(has_redo=has_redo)
        actions = self._fsm.allowed_actions(has_redo=has_redo, has_history=has_history)
        print(
            f"Session reattached: {self.client_info.session_id[:8]} → {self._fsm.state.value} "
            f"redo={len(self._app.op.redo_queue())} history={len(self._app.op.history())} "
            f"play_all={actions.get('play_all')}",
            flush=True,
        )
        self.on_client_connected()

    # -- Send helpers (unicast to this session's WebSocket) --

    def _send(self, message: str) -> None:
        self._event_loop.send_to(self._ws, message)

    # -- Unified state snapshot --

    def _build_state_snapshot(self) -> SessionStateSnapshot:
        """Build a complete state snapshot from all server-side sources.

        This is the SINGLE place where all state is gathered. No other
        method needs to know which fields exist — just call send_state().
        """
        from cube.domain.solver.SolverName import SolverName

        app = self._app
        vs = app.vs
        op = app.op
        cfg = app.config

        # Cube state
        cube_state = extract_cube_state(app.cube)

        # History
        done: list[dict[str, str]] = [
            {"alg": str(a), "type": self._classify_alg(a)}
            for a in op.history()
        ]
        redo_list = list(reversed(op.redo_queue()))
        redo: list[dict[str, str]] = [
            {"alg": str(a), "type": self._classify_alg(a)}
            for a in redo_list
        ]

        # Text overlays
        at = vs.animation_text
        anim_lines: list[dict[str, object]] = []
        animation_text_props = cfg.animation_text
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

        # Flow state machine
        has_redo = bool(redo)
        has_history = bool(done)
        fsm = self._fsm

        return SessionStateSnapshot(
            # Cube
            cube_size=cube_state["size"],
            cube_solved=cube_state["solved"],
            cube_faces=cube_state["faces"],
            # Flow state machine
            machine_state=fsm.state.value,
            allowed_actions=fsm.allowed_actions(has_redo=has_redo, has_history=has_history),
            # Playback (derived from FSM for backward compat)
            is_playing=fsm.state in (FlowState.PLAYING, FlowState.REWINDING),
            # History
            history_done=done,
            history_redo=redo,
            redo_source="solver" if fsm.redo_source == "solver" and has_redo else "undo",
            redo_tainted=fsm.redo_tainted and has_redo,
            next_move=self._compute_next_move(redo_list),
            # Speed
            speed_index=vs.get_speed_index,
            speed_step=cfg.animation_speed_config.step,
            speed_d0=cfg.animation_speed_config.d0,
            speed_dn=cfg.animation_speed_config.dn,
            # Toolbar / Config
            debug=cfg.solver_debug,
            animation_enabled=op.animation_enabled,
            solver_name=app.slv.name,
            solver_list=[s.display_name for s in SolverName.user_visible()],
            slice_start=vs.slice_start,
            slice_stop=vs.slice_stop,
            assist_enabled=cfg.assist_config.enabled,
            assist_delay_ms=cfg.assist_config.delay_ms,
            sound_enabled=cfg.sound_config.enabled,
            # Text
            animation_text=anim_lines,
            status_text=app.slv.status,
            solver_text=app.slv.name,
            move_count=op.count,
            # Meta
            version=get_version(),
            client_count=self._client_count,
            session_id=self.client_info.session_id,
        )

    def send_state(self) -> None:
        """Send a complete state snapshot to the client.

        This is the ONLY method that should be called after any state
        change. Replaces all individual send_*() calls.
        """
        snapshot = self._build_state_snapshot()
        self._send(snapshot.to_json())


    # -- Send helpers (event messages + client count) --

    def send_client_count(self, count: int) -> None:
        """Update client count and send full state snapshot."""
        self._client_count = count
        self.send_state()

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

    def send_animation_start(self, alg: "Alg", duration_ms: int, *, is_undo: bool = False) -> None:
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
            "is_undo": is_undo,
            "state": state,
        }))

    def send_play_empty(self) -> None:
        """Tell client there are no more moves to play."""
        self._send(json.dumps({"type": "play_empty"}))

    @staticmethod
    def _classify_alg(alg: "Alg") -> str:
        """Classify an algorithm for history panel badges."""
        from cube.domain.algs.Algs import Algs
        from cube.domain.algs.FaceAlgBase import FaceAlgBase
        from cube.domain.algs.SliceAlgBase import SliceAlgBase
        from cube.domain.algs.WholeCubeAlg import WholeCubeAlg
        from cube.domain.algs.WideFaceAlg import WideFaceAlg

        if Algs.is_scramble(alg):
            return "scramble"
        if isinstance(alg, WholeCubeAlg):
            return "rotation"
        if isinstance(alg, SliceAlgBase):
            return "slice"
        if isinstance(alg, (FaceAlgBase, WideFaceAlg)):
            return "face"
        return "move"

    def _compute_next_move(self, redo_list: list["Alg"]) -> dict[str, object] | None:
        """Peek at the first redo item and compute its face/layers/direction.

        Returns None for: empty redo, scrambles.
        Whole-cube rotations (x/y/z) are mapped to all layers on equivalent face.
        """
        from cube.domain.algs.Algs import Algs

        if not redo_list:
            return None

        alg = redo_list[0]

        # Skip scrambles
        if Algs.is_scramble(alg):
            return None

        face_name: str = self._alg_to_face_name(alg)
        if not face_name:
            return None

        # Direction and layers
        from cube.domain.algs.AnimationAbleAlg import AnimationAbleAlg
        cube = self._app.cube
        size: int = cube.size
        direction: int = 1
        layers: list[int] = [0]

        # Whole-cube rotations: all layers, map to equivalent face
        if face_name in ("x", "y", "z"):
            whole_cube_map: dict[str, str] = {"x": "R", "y": "U", "z": "F"}
            face_name = whole_cube_map[face_name]
            layers = list(range(size))
            if isinstance(alg, AnimationAbleAlg):
                n = alg.n if hasattr(alg, 'n') else 1
                if n % 4 == 1:
                    direction = 1
                elif n % 4 == 3:
                    direction = -1
                elif n % 4 == 2:
                    direction = 2
        elif isinstance(alg, AnimationAbleAlg):
            n = alg.n if hasattr(alg, 'n') else 1
            if n % 4 == 1:
                direction = 1
            elif n % 4 == 3:
                direction = -1
            elif n % 4 == 2:
                direction = 2
            layers = self._extract_layers(alg, cube, size, face_name)

        alg_type: str = self._classify_alg(alg)

        return {
            "face": face_name,
            "layers": layers,
            "direction": direction,
            "alg": str(alg),
            "type": alg_type,
        }

    # -- Update --

    def update_gui_elements(self) -> None:
        """Send updated state to client (unified snapshot)."""
        self.send_state()

    # -- Client connected --

    def on_client_connected(self) -> None:
        """Send initial state to newly connected client."""
        has_redo = bool(self._app.op.redo_queue())
        has_history = bool(self._app.op.history())
        print(
            f"Session {self.client_info.session_id[:8]} - sending initial state: "
            f"fsm={self._fsm.state.value} redo={len(self._app.op.redo_queue())} "
            f"history={len(self._app.op.history())} "
            f"play_all={self._fsm.allowed_actions(has_redo=has_redo, has_history=has_history).get('play_all')}",
            flush=True,
        )
        self.send_color_map()
        self.send_state()

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

        elif msg_type == "play_next_redo":
            self._handle_play_next(forward=True)

        elif msg_type == "play_next_undo":
            self._handle_play_next(forward=False)

        elif msg_type == "animation_done":
            self._animation_manager.on_client_animation_done()

        elif msg_type == "resize":
            pass

    # -- Input handlers --

    def _handle_key(self, symbol: int, modifiers: int) -> None:
        from cube.presentation.gui.commands.concrete import NewSessionCommand, QuitCommand
        from cube.presentation.gui.key_bindings import lookup_command
        command = lookup_command(symbol, modifiers, self.animation_running)
        if command:
            # Web sessions can't quit — restart as a new session instead
            if isinstance(command, QuitCommand):
                command = NewSessionCommand()
            self.inject_command(command)

    def _handle_speed(self, speed_index: float) -> None:
        clamped = max(0.0, min(7.0, float(speed_index)))
        self._app.vs._speed = clamped

    def _handle_size(self, size: int) -> None:
        clamped = max(2, min(20, size))
        vs = self._app.vs
        if clamped != vs.cube_size:
            if not self._fsm.send(FlowEvent.SIZE_CHANGE):
                return  # Not allowed in current state
            prev_solver = self._app.slv.get_code
            vs.cube_size = clamped
            self._app.reset(clamped)
            self._app.switch_to_solver(prev_solver)
            self.send_state()

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
        self.send_state()

    def _handle_command(self, command_name: str) -> None:
        from cube.presentation.gui.commands import Commands

        if command_name == "solve":
            if not self._fsm.send(FlowEvent.SOLVE):
                return
            self._two_phase_solve()
            return

        if command_name == "solve_and_play":
            if not self._fsm.send(FlowEvent.SOLVE_AND_PLAY):
                return
            self._start_one_phase_solve()
            return

        if command_name == "scramble":
            if not self._fsm.send(FlowEvent.SCRAMBLE):
                return
            # Scramble applies instantly (no animation).
            op = self._app.op
            op.clear_redo()
            self._fsm.redo_source = "undo"
            self._fsm.redo_tainted = False
            with op.with_animation(animation=False):
                ctx = CommandContext.from_window(self)  # type: ignore[arg-type]
                Commands.SCRAMBLE_1.execute(ctx)
            # Clear history so scramble moves don't appear in redo queue.
            # Scramble is a starting point, not an undoable operation.
            op._history.clear()
            # Scramble done — transition back based on queue state
            has_redo = bool(op.redo_queue())
            has_history = bool(op.history())
            self._fsm.send(FlowEvent.ANIM_DONE, has_redo=has_redo, has_history=has_history)
            self.send_state()
            return

        if command_name == "undo":
            if not self._fsm.send(FlowEvent.UNDO):
                return
            self._fsm.redo_source = "undo"
            self._app.op.undo(animation=True)
            self.send_state()
            return

        if command_name == "redo":
            if not self._fsm.send(FlowEvent.PLAY_NEXT):
                return
            self._app.op.redo(animation=True)
            self.send_state()
            return

        if command_name == "clear_history":
            self._fsm.redo_source = "undo"
            self._fsm.redo_tainted = False
            self._app.op.reset()
            # After clearing, we're idle
            self._fsm.send(FlowEvent.RESET, has_redo=False, has_history=False)
            self.send_state()
            return

        if command_name == "reset_session":
            self._fsm.send(FlowEvent.RESET_SESSION)
            self._animation_manager.cancel_animation()
            prev_solver = self._app.slv.get_code
            self._app.reset(self._app.config.cube_size)  # Reset to config default
            self._app.switch_to_solver(prev_solver)
            self.on_client_connected()
            return

        if command_name == "fast_play":
            # Client-initiated: client sends play_next_redo directly
            return

        if command_name == "fast_rewind":
            # Client-initiated: client sends play_next_undo directly
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
        vec: tuple[int, int, int]
        if position == 'top':
            vec = axes['up']
        elif position == 'bottom':
            u = axes['up']
            vec = (-u[0], -u[1], -u[2])
        elif position == 'right':
            vec = axes['right']
        elif position == 'left':
            r = axes['right']
            vec = (-r[0], -r[1], -r[2])
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
            if not self._fsm.send(FlowEvent.FACE_TURN):
                return  # Not allowed in current state (e.g., during playback)
            if inv:
                alg = alg.inv()
            op = self._app.op
            # Detect manual move while solver redo queue exists → tainted
            if self._fsm.redo_source == "solver" and op.redo_queue():
                self._fsm.redo_tainted = True
            op.play(alg, animation=True)
            self.send_state()

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
                inv = True
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
        """Solve the cube by placing solution steps into the redo queue.

        The user can then step through with redo/next or fast-play.
        FSM must already be in SOLVING state before this is called.
        """
        try:
            app = self._app
            slv = app.slv
            solution_alg = slv.solution()
            solution_alg = solution_alg.simplify()
            # Flatten into atomic steps and enqueue as redo
            steps = list(solution_alg.flatten())
            app.op.enqueue_redo(steps)
            self._fsm.redo_source = "solver"
            self._fsm.redo_tainted = False
            # SOLVE_DONE: transitions to READY (or PLAYING if auto_play)
            has_redo = bool(app.op.redo_queue())
            has_history = bool(app.op.history())
            self._fsm.send(FlowEvent.SOLVE_DONE, has_redo=has_redo, has_history=has_history)
            self.send_state()
        except Exception as e:
            traceback.print_exc()
            self._app.set_error(f"Solve error: {e}")
            # On error, go back to IDLE/READY
            has_redo = bool(self._app.op.redo_queue())
            has_history = bool(self._app.op.history())
            self._fsm.send(FlowEvent.SOLVE_DONE, has_redo=has_redo, has_history=has_history)
            self.send_state()

    def _start_one_phase_solve(self) -> None:
        """Launch the solver in a background thread with blocking animation.

        FSM must already be in SOLVING state before this is called.
        Creates an asyncio task that runs the solver via asyncio.to_thread().
        """
        loop = self._event_loop._loop
        if loop:
            loop.create_task(self._one_phase_solve())

    async def _one_phase_solve(self) -> None:
        """Run solver in worker thread with blocking animation mode.

        The solver calls op.play() which triggers AM.run_animation() in
        blocking mode — each animated move blocks the solver thread until
        the client signals animation_done. This keeps solver annotations
        (markers from annotate() blocks) visible during animation.
        """
        am = self._animation_manager
        am.set_blocking_mode(True)
        try:
            await asyncio.to_thread(self._run_solver_blocking)
        except Exception as e:
            traceback.print_exc()
            self._app.set_error(f"Solve error: {e}")
        finally:
            am.set_blocking_mode(False)
        # Yield to event loop so any queued call_soon_threadsafe callbacks
        # from the solver thread (e.g., annotate __exit__ removing markers)
        # are processed before we send the final state.
        await asyncio.sleep(0)
        # One-phase solve: moves are in history, not redo queue.
        # Clear auto_play since the solve IS the play.
        self._fsm._auto_play = False
        has_redo = bool(self._app.op.redo_queue())
        has_history = bool(self._app.op.history())
        self._fsm.send(FlowEvent.SOLVE_DONE, has_redo=has_redo, has_history=has_history)
        self.send_state()

    def _run_solver_blocking(self) -> None:
        """Run the solver — called from worker thread via asyncio.to_thread()."""
        self._app.slv.solve(animation=True)

    def _handle_play_next(self, forward: bool) -> None:
        """Handle client request for the next move in playback.

        Client-initiated pull model: the client requests each move one at a
        time. The play_next message also serves as an ack for the previous
        animation (like animation_done).

        A single op.redo() can produce multiple AM-queued moves (when the alg
        flattens into several simple algs). The AM sends one animation_start
        at a time. Only when the AM is fully idle do we pop the next redo item.

        The first call also transitions the FSM to PLAYING/REWINDING if needed.
        """
        am = self._animation_manager
        op = self._app.op
        fsm = self._fsm

        # If FSM isn't in a playback state yet, transition now
        if fsm.state not in (FlowState.PLAYING, FlowState.REWINDING):
            event = FlowEvent.PLAY_ALL if forward else FlowEvent.REWIND_ALL
            if not fsm.send(event):
                return  # Not allowed in current state

        # Ack the previous animation — let AM process its remaining queue
        am.on_client_animation_done()

        # If AM still has queued work (from a multi-step redo), it already
        # sent the next animation_start to the client. Just update history.
        if not am.is_idle:
            self.send_state()
            return

        # AM is idle — pop next redo/undo item from the operator queue
        has_more: bool = bool(op.redo_queue()) if forward else bool(op.history())
        if not has_more:
            has_redo = bool(op.redo_queue())
            has_history = bool(op.history())
            fsm.send(FlowEvent.QUEUE_EMPTY, has_redo=has_redo, has_history=has_history)
            self.send_play_empty()
            self.send_state()
            return

        # Handle animation disabled: apply all moves instantly
        if not op.animation_enabled:
            if forward:
                while op.redo_queue():
                    op.redo(animation=False)
            else:
                while op.history():
                    op.undo(animation=False)
            has_redo = bool(op.redo_queue())
            has_history = bool(op.history())
            fsm.send(FlowEvent.QUEUE_EMPTY, has_redo=has_redo, has_history=has_history)
            self.send_play_empty()
            self.send_state()
            return

        # Pop one move with animation — may queue multiple items in AM
        if forward:
            op.redo(animation=True)
        else:
            op.undo(animation=True)

        # If AM is idle after the move (non-animatable was processed instantly),
        # recurse to get the next animatable move or reach empty
        if am.is_idle:
            self._handle_play_next(forward)
            return

        self.send_state()
    # -- Command injection --

    def inject_command(self, command: Command) -> None:
        from cube.presentation.gui.commands import Commands

        if command is Commands.SOLVE_ALL:
            if self._fsm.send(FlowEvent.SOLVE):
                self._two_phase_solve()
            return

        if command is Commands.STOP_ANIMATION:
            if self._fsm.send(FlowEvent.STOP):
                self._animation_manager.cancel_animation()
                if not self._animation_manager._blocking_mode:
                    # Queue mode: animation cancelled, immediately done.
                    has_redo = bool(self._app.op.redo_queue())
                    has_history = bool(self._app.op.history())
                    self._fsm.send(FlowEvent.ANIM_DONE, has_redo=has_redo, has_history=has_history)
                    self.send_play_empty()
                # Blocking mode: solver thread cleanup sends SOLVE_DONE
            self.send_state()
            return

        if command is Commands.RESET_CUBE:
            self._fsm.send(FlowEvent.RESET)
            prev_solver = self._app.slv.get_code
            command.execute(CommandContext.from_window(self))  # type: ignore[arg-type]
            self._app.switch_to_solver(prev_solver)
            self.send_state()
            return

        try:
            from cube.presentation.gui.commands.concrete import NewSessionCommand

            history_len_before = len(self._app.op.history())
            ctx = CommandContext.from_window(self)  # type: ignore[arg-type]
            command.execute(ctx)

            if isinstance(command, NewSessionCommand):
                # Full state refresh — treat as reset_session
                self._fsm.send(FlowEvent.RESET_SESSION)
                self.on_client_connected()
                return

            # Detect manual move while solver redo queue exists → tainted
            if (self._fsm.redo_source == "solver" and self._app.op.redo_queue()
                    and len(self._app.op.history()) > history_len_before):
                self._fsm.redo_tainted = True

            self.send_state()
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
                self.send_state()

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

    def close(self) -> None:
        """No-op for web sessions — use NewSessionCommand to restart instead."""
        pass

    def cleanup(self) -> None:
        self._renderer.cleanup()

    # Alias used by WebglAnimationManager
    def _on_draw(self) -> None:
        """Send state (alias for compatibility)."""
        self.send_state()
