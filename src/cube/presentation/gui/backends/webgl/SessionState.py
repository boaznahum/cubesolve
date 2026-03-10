"""Unified state snapshot for the webgl backend.

Instead of sending 10+ individual messages to keep the client in sync,
the server builds ONE complete snapshot and sends it as a single JSON
message after every state change.

This eliminates the "forgot to call send_X()" class of bugs entirely.

Messages that remain separate (real-time events, not state):
  - animation_start  (server → client: start a 3D animation)
  - animation_done   (client → server: animation finished)
  - play_next_redo   (client → server: request next forward move)
  - play_next_undo   (client → server: request next backward move)
  - play_empty       (server → client: no more moves to play)
  - flush_queue      (server → client: clear pending animations)
  - color_map        (server → client: one-time on connect, static)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class SessionStateSnapshot:
    """Complete state snapshot sent to the client.

    Built by ClientSession._build_state_snapshot() and sent as one
    JSON message of type "state". The client replaces its entire
    AppState from this snapshot — no incremental patching needed.

    Groups:
        cube     — face colors, size, solved status
        speed    — animation speed config
        toolbar  — debug, animation, solver, assist, slices
        text     — overlay text (animation lines, status, solver, moves)
        history  — undo/redo queues, source, tainted flag, next move hint
        playback — is_playing flag (will become state machine enum later)
        meta     — version, client_count, session_id
    """

    # -- Cube --
    cube_size: int = 3
    cube_solved: bool = False
    cube_faces: dict[str, dict[str, list[object]]] = field(default_factory=dict)

    # -- Flow state machine --
    machine_state: str = "idle"
    allowed_actions: dict[str, bool] = field(default_factory=dict)

    # -- Playback (derived from machine_state for backward compat) --
    is_playing: bool = False

    # -- History --
    history_done: list[dict[str, str]] = field(default_factory=list)
    history_redo: list[dict[str, str]] = field(default_factory=list)
    redo_source: str = "undo"      # "solver" | "undo"
    redo_tainted: bool = False
    next_move: dict[str, object] | None = None

    # -- Speed --
    speed_index: float = 0.0
    speed_step: float = 0.5
    speed_d0: float = 500.0
    speed_dn: float = 50.0

    # -- Toolbar / Config --
    debug: bool = False
    animation_enabled: bool = True
    solver_name: str = ""
    solver_list: list[str] = field(default_factory=list)
    slice_start: int = 0
    slice_stop: int = 0
    assist_enabled: bool = True
    assist_delay_ms: int = 400
    sound_enabled: bool = False
    operator_buffer_mode: bool = True
    queue_heading_h1: bool = True
    queue_heading_h2: bool = True
    default_scramble: str = "0"  # "0"-"9" or "*" (random)

    # -- Text overlays --
    animation_text: list[dict[str, object]] = field(default_factory=list)
    status_text: str = ""
    solver_text: str = ""
    move_count: int = 0

    # -- Meta --
    version: str = ""
    client_count: int = 0
    session_id: str = ""

    def to_json(self) -> str:
        """Serialize to JSON string for WebSocket transmission.

        Groups related fields into nested objects for clean client-side
        destructuring. The top-level "type" field is always "state".
        """
        msg: dict[str, object] = {
            "type": "state",

            "cube": {
                "size": self.cube_size,
                "solved": self.cube_solved,
                "faces": self.cube_faces,
            },

            "machine_state": self.machine_state,
            "allowed_actions": self.allowed_actions,

            "is_playing": self.is_playing,

            "history": {
                "done": self.history_done,
                "redo": self.history_redo,
                "redo_source": self.redo_source,
                "redo_tainted": self.redo_tainted,
            },

            "speed": {
                "index": self.speed_index,
                "step": self.speed_step,
                "d0": self.speed_d0,
                "dn": self.speed_dn,
            },

            "toolbar": {
                "debug": self.debug,
                "animation": self.animation_enabled,
                "solver_name": self.solver_name,
                "solver_list": self.solver_list,
                "slice_start": self.slice_start,
                "slice_stop": self.slice_stop,
                "assist_enabled": self.assist_enabled,
                "assist_delay_ms": self.assist_delay_ms,
                "sound_enabled": self.sound_enabled,
                "operator_buffer_mode": self.operator_buffer_mode,
                "queue_heading_h1": self.queue_heading_h1,
                "queue_heading_h2": self.queue_heading_h2,
                "default_scramble": self.default_scramble,
            },

            "text": {
                "animation": self.animation_text,
                "status": self.status_text,
                "solver": self.solver_text,
                "moves": self.move_count,
            },

            "version": self.version,
            "client_count": self.client_count,
            "session_id": self.session_id,
        }

        # next_move is optional — only include when present
        if self.next_move is not None:
            msg["history"]["next_move"] = self.next_move  # type: ignore[index]

        return json.dumps(msg)
