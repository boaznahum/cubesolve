"""Flow State Machine for the WebGL backend.

Replaces scattered boolean flags (_fast_playing, _redo_is_solver,
_redo_tainted, playbackMode, _pendingSolveAndPlay) with a single
explicit state machine that owns all flow control.

The server owns this state machine. The client reads the state name
and allowed_actions from the state snapshot — it never reasons about
what's allowed, it just checks the table.

States:
    IDLE       — No redo queue. Cube may be solved, scrambled, or fresh.
    READY      — Redo queue has moves. Waiting for user action.
    SOLVING    — Server computing solution.
    PLAYING    — Auto-playing forward through redo queue.
    REWINDING  — Auto-playing backward (undo all).
    ANIMATING  — Single move animation in progress.
    STOPPING   — User pressed stop, current animation finishing.

Key design decisions:
    - Pure logic: no imports from cube domain, easily unit-testable.
    - RESET_SESSION and RECONNECT work from ANY state.
    - Button enable/disable is a static table lookup, not if/else chains.
    - Redo metadata (source, tainted) is tracked as metadata, not states.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class FlowState(str, Enum):
    """Application flow states."""
    IDLE = "idle"
    READY = "ready"
    SOLVING = "solving"
    PLAYING = "playing"
    REWINDING = "rewinding"
    ANIMATING = "animating"
    STOPPING = "stopping"
    EDITING = "editing"


class FlowEvent(str, Enum):
    """Events that trigger state transitions."""
    # User actions
    SCRAMBLE = "scramble"
    SOLVE = "solve"
    SOLVE_AND_PLAY = "solve_and_play"
    FACE_TURN = "face_turn"
    PLAY_ALL = "play_all"
    PLAY_NEXT = "play_next"
    UNDO = "undo"
    REWIND_ALL = "rewind_all"
    STOP = "stop"
    RESET = "reset"
    RESET_SESSION = "reset_session"
    SIZE_CHANGE = "size_change"

    ENTER_EDIT = "enter_edit"
    EXIT_EDIT = "exit_edit"

    # System events
    SOLVE_DONE = "solve_done"
    ANIM_DONE = "anim_done"
    QUEUE_EMPTY = "queue_empty"
    RECONNECT = "reconnect"


# -- Static transition table --
# Maps (state, event) → target state.
# Special value None means "use a guard function" (dynamic target).
# Events not listed for a state are illegal (rejected silently).

_TRANSITIONS: dict[FlowState, dict[FlowEvent, FlowState | None]] = {
    FlowState.IDLE: {
        FlowEvent.SCRAMBLE: FlowState.ANIMATING,
        FlowEvent.SOLVE: FlowState.SOLVING,
        FlowEvent.SOLVE_AND_PLAY: FlowState.SOLVING,
        FlowEvent.FACE_TURN: FlowState.ANIMATING,
        FlowEvent.SIZE_CHANGE: FlowState.IDLE,
        FlowEvent.ENTER_EDIT: FlowState.EDITING,
        FlowEvent.RESET_SESSION: FlowState.IDLE,
    },
    FlowState.SOLVING: {
        FlowEvent.SOLVE_DONE: None,  # guard: → READY or PLAYING (auto_play)
        FlowEvent.STOP: FlowState.STOPPING,  # abort one-phase solve
        FlowEvent.RESET_SESSION: FlowState.IDLE,
    },
    FlowState.READY: {
        FlowEvent.PLAY_ALL: FlowState.PLAYING,
        FlowEvent.PLAY_NEXT: FlowState.ANIMATING,
        FlowEvent.UNDO: FlowState.ANIMATING,
        FlowEvent.REWIND_ALL: FlowState.REWINDING,
        FlowEvent.FACE_TURN: FlowState.ANIMATING,
        FlowEvent.SCRAMBLE: FlowState.ANIMATING,
        FlowEvent.SOLVE: FlowState.SOLVING,
        FlowEvent.SOLVE_AND_PLAY: FlowState.SOLVING,
        FlowEvent.RESET: FlowState.IDLE,
        FlowEvent.SIZE_CHANGE: FlowState.IDLE,
        FlowEvent.ENTER_EDIT: FlowState.EDITING,
        FlowEvent.RESET_SESSION: FlowState.IDLE,
    },
    FlowState.PLAYING: {
        FlowEvent.ANIM_DONE: FlowState.PLAYING,  # loop: request next
        FlowEvent.QUEUE_EMPTY: None,  # guard: → IDLE or READY
        FlowEvent.STOP: FlowState.STOPPING,
        FlowEvent.RESET_SESSION: FlowState.IDLE,
    },
    FlowState.REWINDING: {
        FlowEvent.ANIM_DONE: FlowState.REWINDING,  # loop: request next
        FlowEvent.QUEUE_EMPTY: None,  # guard: → IDLE or READY
        FlowEvent.STOP: FlowState.STOPPING,
        FlowEvent.RESET_SESSION: FlowState.IDLE,
    },
    FlowState.ANIMATING: {
        FlowEvent.ANIM_DONE: None,  # guard: → IDLE or READY
        FlowEvent.STOP: FlowState.STOPPING,
        FlowEvent.RESET_SESSION: FlowState.IDLE,
    },
    FlowState.STOPPING: {
        FlowEvent.ANIM_DONE: None,  # guard: → IDLE or READY
        FlowEvent.QUEUE_EMPTY: None,  # guard: → IDLE or READY
        FlowEvent.SOLVE_DONE: None,  # guard: one-phase solve aborted → IDLE or READY
        FlowEvent.RESET_SESSION: FlowState.IDLE,
    },
    FlowState.EDITING: {
        FlowEvent.EXIT_EDIT: None,  # guard: → IDLE or READY
        FlowEvent.STOP: FlowState.EDITING,  # cancel animation, stay in editing
        FlowEvent.RESET_SESSION: FlowState.IDLE,
    },
}


# -- Button enable table --
# Maps action name → set of states where it's allowed.
# Data guards (has_redo, has_history) are applied on top at runtime.

_BUTTON_TABLE: dict[str, set[FlowState]] = {
    "scramble":       {FlowState.IDLE, FlowState.READY},
    "solve":          {FlowState.IDLE, FlowState.READY},
    "solve_and_play": {FlowState.IDLE, FlowState.READY},
    "play_all":       {FlowState.READY},
    "play_next":      {FlowState.READY},
    "undo":           {FlowState.READY},
    "redo":           {FlowState.READY},
    "rewind_all":     {FlowState.READY},
    "stop":           {FlowState.ANIMATING, FlowState.PLAYING, FlowState.REWINDING, FlowState.SOLVING, FlowState.EDITING},
    "reset":          {FlowState.IDLE, FlowState.READY},
    "reset_session":  set(FlowState),  # all states
    "face_turn":      {FlowState.IDLE, FlowState.READY},
    "size_change":    {FlowState.IDLE, FlowState.READY},
    "speed_change":   set(FlowState),  # all states
    "clear_history":  {FlowState.IDLE, FlowState.READY},
    "enter_edit":     {FlowState.IDLE, FlowState.READY},
}

# Actions that additionally require data guards
_NEEDS_REDO: set[str] = {"play_all", "play_next", "redo"}
_NEEDS_HISTORY: set[str] = {"undo", "rewind_all"}


class FlowStateMachine:
    """Explicit state machine for WebGL application flow control.

    Pure logic — no cube domain imports. The caller provides context
    (has_redo, has_history) when needed for guard conditions.

    Usage::

        fsm = FlowStateMachine()
        fsm.send(FlowEvent.SCRAMBLE)          # IDLE → ANIMATING
        fsm.send(FlowEvent.ANIM_DONE,
                 has_redo=False, has_history=True)  # ANIMATING → READY
        actions = fsm.allowed_actions(has_redo=True, has_history=True)
        # {'scramble': True, 'play_all': True, 'undo': True, ...}
    """

    def __init__(self) -> None:
        self._state: FlowState = FlowState.IDLE
        self._listeners: list[Callable[[FlowState, FlowState, FlowEvent], None]] = []

        # Redo metadata (not flow state — just data carried along)
        self.redo_source: str = "undo"  # "solver" | "undo"
        self.redo_tainted: bool = False

        # Internal flag: solve_and_play pending (set on SOLVE_AND_PLAY, cleared on SOLVE_DONE)
        self._auto_play: bool = False

    @property
    def state(self) -> FlowState:
        """Current flow state."""
        return self._state

    def on_transition(self, callback: Callable[[FlowState, FlowState, FlowEvent], None]) -> None:
        """Register a callback for state transitions.

        Called with (new_state, old_state, event) after each transition.
        """
        self._listeners.append(callback)

    def send(
        self,
        event: FlowEvent,
        *,
        has_redo: bool = False,
        has_history: bool = False,
    ) -> bool:
        """Attempt a state transition.

        Returns True if the transition was accepted, False if rejected
        (illegal event for current state).

        Args:
            event: The event to process.
            has_redo: Whether the redo queue has items (for guards).
            has_history: Whether the history has items (for guards).
        """
        state = self._state
        state_transitions = _TRANSITIONS.get(state)
        if state_transitions is None:
            return False

        if event not in state_transitions:
            # Illegal transition — silently reject
            return False

        target = state_transitions[event]

        if target is None:
            # Guard function — compute target dynamically
            target = self._resolve_guard(event, has_redo=has_redo, has_history=has_history)
            if target is None:
                return False

        # Handle special event side effects
        if event == FlowEvent.SOLVE_AND_PLAY:
            self._auto_play = True
        elif event == FlowEvent.RESET_SESSION:
            self._reset_metadata()

        old_state = self._state
        self._state = target

        # Notify listeners
        for listener in self._listeners:
            listener(target, old_state, event)

        return True

    def send_reconnect(self, *, has_redo: bool = False) -> FlowState:
        """Handle reconnection — always succeeds, returns new state.

        Transitions to READY if there's a redo queue, IDLE otherwise.
        Resets auto_play flag (can't resume auto-play after reconnect).
        """
        self._auto_play = False
        old_state = self._state
        new_state = FlowState.READY if has_redo else FlowState.IDLE
        self._state = new_state

        for listener in self._listeners:
            listener(new_state, old_state, FlowEvent.RECONNECT)

        return new_state

    def allowed_actions(self, *, has_redo: bool, has_history: bool) -> dict[str, bool]:
        """Compute which actions are allowed in the current state.

        Returns a dict of action_name → bool, suitable for including
        in the state snapshot sent to the client.
        """
        result: dict[str, bool] = {}
        for action, allowed_states in _BUTTON_TABLE.items():
            allowed = self._state in allowed_states
            # Apply data guards
            if allowed and action in _NEEDS_REDO:
                allowed = has_redo
            if allowed and action in _NEEDS_HISTORY:
                allowed = has_history
            result[action] = allowed
        return result

    def _resolve_guard(
        self,
        event: FlowEvent,
        *,
        has_redo: bool,
        has_history: bool,
    ) -> FlowState | None:
        """Resolve a guarded transition to a concrete target state."""
        if event == FlowEvent.SOLVE_DONE:
            if self._state == FlowState.STOPPING:
                # Solve was aborted — don't auto-play
                self._auto_play = False
                if has_redo or has_history:
                    return FlowState.READY
                return FlowState.IDLE
            if self._auto_play:
                self._auto_play = False
                return FlowState.PLAYING
            return FlowState.READY

        if event == FlowEvent.QUEUE_EMPTY:
            # After playback/rewind exhausts queue
            if self._state == FlowState.PLAYING:
                # Forward play ended — go to READY if history exists
                return FlowState.READY if has_history else FlowState.IDLE
            if self._state == FlowState.REWINDING:
                # Rewind ended — go to READY if redo exists
                return FlowState.READY if has_redo else FlowState.IDLE
            # From STOPPING
            if has_redo or has_history:
                return FlowState.READY
            return FlowState.IDLE

        if event == FlowEvent.ANIM_DONE:
            # Single animation done — go to READY if anything remains
            if has_redo or has_history:
                return FlowState.READY
            return FlowState.IDLE

        if event == FlowEvent.EXIT_EDIT:
            if has_redo or has_history:
                return FlowState.READY
            return FlowState.IDLE

        return None

    def _reset_metadata(self) -> None:
        """Reset redo metadata on session reset."""
        self.redo_source = "undo"
        self.redo_tainted = False
        self._auto_play = False
