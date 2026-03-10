"""
PRIVATE MODULE - DO NOT IMPORT DIRECTLY!

This module contains configuration values for the application. It is intentionally
named with a leading underscore to indicate it is private to the application package.

To access configuration values from outside the application package:
1. Use the ConfigProtocol via cube.config property (preferred for domain/presentation layers)
2. Import as `from cube.application import _config as config` (for tests only)

DO NOT use `from cube.application._config import X` in production code.
Access config values through the ConfigProtocol interface instead.
"""
import copy
from dataclasses import dataclass, field
from typing import Tuple

from cube.config.face_tracer_config import FaceTrackerConfig, TrackerIndicatorConfig
from cube.utils.markers_config import MarkersConfig

# Type alias for config change listener callback
ConfigListener = object  # Callable[[str, object], None] — avoid import cycle


########## Sub-config dataclasses ##########

@dataclass
class AnimationSpeedConfig:
    """Animation speed parameters for WebGL frontend.

    Speed is computed as: d0 * (dn / d0) ** (index / 7.0)
    """
    # Default speed index (0-7, higher is faster)
    default_index: float = 2
    # Step size between adjacent speed dropdown options
    step: float = 0.5
    # Duration (ms) at speed index 0 (slowest)
    d0: float = 2000
    # Duration (ms) at speed index 7 (fastest)
    dn: float = 50
    # Timeout (seconds) for blocking mode wait — prevents permanent hang
    # if WebSocket dies without reconnect
    blocking_timeout: float = 60.0


@dataclass
class AssistConfig:
    """Assist mode configuration for WebGL frontend.

    When enabled, shows a brief move indicator before each animation.
    """
    # Whether assist is enabled by default
    enabled: bool = True
    # Duration (ms) of the move indicator preview
    delay_ms: int = 400


@dataclass
class SoundConfig:
    """Sound effects configuration for WebGL frontend.

    When enabled, plays a procedural click/whir sound on each cube rotation.
    """
    # Whether sound is enabled by default
    enabled: bool = False


@dataclass
class ArrowConfig:
    """Configuration for 3D arrows showing source-to-destination direction.

    Access via ConfigProtocol.arrow_config property.
    """
    # Master switch to enable/disable 3D arrows
    enabled: bool = False

    # Arrow style: "simple" (straight), "curved" (bezier), "compound" (multiple segments)
    style: str = "simple"

    # Arrow animation: "grow" (extends from source), "fade" (fades in), "none" (instant)
    animation: str = "grow"

    # Arrow head style: "cone" (3D cone), "pyramid" (3D pyramid), "flat" (2D triangle)
    head_style: str = "cone"

    # Arrow color (RGB 0.0-1.0) - bright gold to stand out from markers
    color: Tuple[float, float, float] = (1.0, 0.78, 0.0)

    # Arrow geometry
    shaft_radius: float = 2.0  # Radius of arrow shaft cylinder
    head_radius: float = 5.0  # Radius of cone base
    head_length: float = 12.0  # Length of cone/head
    height_offset: float = 25.0  # Height above cube surface (floating effect)
    animation_duration: float = 0.5  # Seconds for grow animation
    segments: int = 16  # Smoothness of cylinders


@dataclass
class SessionConfig:
    """WebGL session configuration."""
    # How long (seconds) to keep a disconnected WebSocket session alive.
    # If the client reconnects within this window, their cube state is restored.
    # Set to 0 to disable server-side session keep-alive.
    keepalive_timeout: int = 30 * 60  # 30 minutes


########## Per-session configuration ##########
# ConfigData holds ALL configuration fields. Each client session gets its own
# copy (via copy()), so changes don't leak across sessions.
# Some fields have setters with listener notification for runtime changes.

# Import Color for FIRST_FACE_COLOR default
from cube.domain.model.Color import Color as _Color  # noqa: E402

# Import SSCode for SS_CODES default
from cube.utils.SSCode import SSCode  # noqa: E402


def _default_ss_codes() -> dict[SSCode, bool]:
    """Default single-step mode codes."""
    return {
        SSCode.NxN_CORNER_PARITY_FIX: False,
        SSCode.NxN_EDGE_PARITY_FIX: False,
        SSCode.REDUCER_CENTERS_DONE: False,
        SSCode.REDUCER_EDGES_DONE: False,
        SSCode.L1_CROSS_DONE: False,
        SSCode.L1_CORNERS_DONE: False,
        SSCode.L2_DONE: False,
        SSCode.L3_CROSS_DONE: False,
        SSCode.L3_CORNERS_DONE: False,
        SSCode.F2L_WIDE_MOVE: False,
    }


def _default_markers_config() -> MarkersConfig:
    """Default markers configuration."""
    mc = MarkersConfig()
    mc.GUI_DRAW_MARKERS = False
    mc.GUI_DRAW_SAMPLE_MARKERS = False
    mc.GUI_DRAW_LTR_ORIGIN_ARROWS = True
    mc.DRAW_CENTER_INDEXES = False
    return mc


def _default_markers() -> dict[str, Tuple[Tuple[int, int, int], float, float, float]]:
    """Default marker definitions."""
    return {
        "C0": ((199, 21, 133), 1.0, 0.8, 0.1),
        "C1": ((199, 21, 133), 0.6, 1, 0.1),
        "C2": ((0, 100, 0), 1.0, 0.3, 0.1),
    }


def _default_animation_text() -> list[Tuple[int, int, int, Tuple[int, int, int, int], bool]]:
    """Default animation text properties."""
    return [
        (10, 30, 20, (255, 255, 0, 255), True),
        (10, 55, 17, (255, 255, 255, 255), True),
        (10, 80, 14, (255, 255, 255, 255), False),
    ]


def _default_texture_sets() -> list[str | None]:
    """Default texture set list."""
    return [None, "debug4x4", "debug3x3", "arrows", "family", "letters", "numbers", "set2"]


@dataclass
class ConfigData:
    """Per-session configuration — ALL config fields.

    Each client session gets its own copy (via copy()).
    Listeners are notified when fields change via set_* methods.
    Fields without setters are still per-session (each client gets its own clone).
    """

    # ── Core ──
    cube_size: int = 3
    enable_cube_cache: bool = True
    prevent_random_face_pick_up_in_geometry: bool = False

    # ── Solvers ──
    default_solver: str = "Beginner Reducer"
    solver_for_tests: str = "Beginner Reducer"
    default_2x2_solver: str = "2x2 Beginner"
    cage_3x3_solver: str = "cfop"
    solver_debug: bool = True
    solver_pll_rotate_while_search: bool = False
    solver_sanity_check_is_a_boy: bool = False
    lbl_sanity_check: bool = False
    first_face_color: _Color = _Color.WHITE

    # ── Optimizer flags ──
    optimize_odd_cube_centers_switch_centers: bool = False
    optimize_big_cube_centers_search_complete_slices: bool = True
    optimize_big_cube_centers_search_complete_slices_only_target_zero: bool = True
    optimize_big_cube_centers_search_blocks: bool = True

    # ── Model ──
    short_part_name: bool = False
    dont_optimized_part_id: bool = False
    print_cube_as_text_during_solve: bool = False
    check_cube_sanity: bool = False

    # ── Operator ──
    operator_show_alg_annotation: bool = True
    queue_heading_h1: bool = True
    queue_heading_h2: bool = False

    # ── Animation ──
    animation_enabled: bool = True
    animation_speed_config: AnimationSpeedConfig = field(default_factory=AnimationSpeedConfig)
    animation_text: list[Tuple[int, int, int, Tuple[int, int, int, int], bool]] = field(
        default_factory=_default_animation_text)

    # ── Face tracker ──
    face_tracker: FaceTrackerConfig = field(default_factory=lambda: FaceTrackerConfig(
        annotate=True, validate=False, leave_last_annotation=True,
        use_simple_f5_tracker=True, enable_track_piece_caching=True,
    ))

    # ── Assist / Sound ──
    assist_config: AssistConfig = field(default_factory=AssistConfig)
    sound_config: SoundConfig = field(default_factory=SoundConfig)

    # ── Viewer ──
    full_mode: bool = False
    viewer_max_size_for_texture: int = 10
    viewer_trace_draw_update: bool = False
    prof_viewer_search_facet: bool = False
    cell_size: int = 30
    corner_size: float = 0.2
    axis_enabled: bool = False
    axis_length: float = 120.0  # 4 * cell_size
    max_marker_radius: float = 5.0
    viewer_draw_shadows: str = ""
    markers_config: MarkersConfig = field(default_factory=_default_markers_config)
    tracker_indicator: TrackerIndicatorConfig = field(default_factory=TrackerIndicatorConfig)
    markers: dict[str, Tuple[Tuple[int, int, int], float, float, float]] = field(
        default_factory=_default_markers)
    arrow_config: ArrowConfig = field(default_factory=ArrowConfig)

    # ── Single-step codes ──
    ss_codes: dict[SSCode, bool] = field(default_factory=_default_ss_codes)

    # ── Input ──
    keyboard_input_debug: bool = False
    gui_test_mode: bool = False
    quit_on_error_in_test_mode: bool = True
    show_file_algs: bool = True
    input_mouse_model_rotate_by_drag_right_bottom: bool = True
    input_mouse_rotate_adjusted_face: bool = True
    input_mouse_debug: bool = False

    # ── Testing ──
    test_number_of_scramble_iterations: int = 20
    aggressive_test_number_sizes: list[int] = field(default_factory=lambda: [3, 6, 7])
    aggressive_test_number_of_scramble_start: int = 0
    aggressive_test_number_of_scramble_iterations: int = 300
    scramble_key_for_f9: int = 203
    aggressive_2_test_number_sizes: list[int] = field(default_factory=lambda: [3, 6, 7])
    aggressive_2_test_number_of_scramble_start: int = 0
    aggressive_2_test_number_of_scramble_iterations: int = 100

    # ── Logging ──
    operation_log: bool = False
    operation_log_path: str = ".logs/operation.log"
    last_scramble_path: str = ".logs/last_scramble.txt"

    # ── Celebration ──
    celebration_effects: list[str] = field(
        default_factory=lambda: ["none", "confetti", "victory_spin", "sparkle", "glow", "combo"])
    celebration_effect: str = "combo"
    celebration_enabled: bool = False
    celebration_duration: float = 3.0

    # ── Lighting ──
    lighting_brightness: float = 0.65
    lighting_background: float = 0.15

    # ── Textures ──
    texture_sets: list[str | None] | None = field(default_factory=_default_texture_sets)
    texture_set_index: int = 0
    debug_texture: bool = False

    # ── Session (WebGL) ──
    session_config: SessionConfig = field(default_factory=SessionConfig)

    # ── Listeners (NOT copied) ──
    _listeners: list[ConfigListener] = field(default_factory=list, repr=False, compare=False)

    def copy(self) -> "ConfigData":
        """Create a deep copy with empty listener list."""
        new = copy.deepcopy(self)
        new._listeners = []
        return new

    def add_listener(self, listener: ConfigListener) -> None:
        """Register a callback(field_name: str, new_value: object) for changes."""
        self._listeners.append(listener)

    def remove_listener(self, listener: ConfigListener) -> None:
        """Unregister a change listener."""
        self._listeners.remove(listener)

    def _notify(self, field_name: str, value: object) -> None:
        """Notify all listeners of a field change."""
        for listener in self._listeners:
            listener(field_name, value)  # type: ignore[operator]

    def set_solver_debug(self, value: bool) -> None:
        """Set solver_debug and notify listeners."""
        if self.solver_debug != value:
            self.solver_debug = value
            self._notify("solver_debug", value)

    def set_queue_heading_h1(self, value: bool) -> None:
        """Set queue_heading_h1 and notify listeners."""
        if self.queue_heading_h1 != value:
            self.queue_heading_h1 = value
            self._notify("queue_heading_h1", value)

    def set_queue_heading_h2(self, value: bool) -> None:
        """Set queue_heading_h2 and notify listeners."""
        if self.queue_heading_h2 != value:
            self.queue_heading_h2 = value
            self._notify("queue_heading_h2", value)


# Module-level defaults instance — the single source of truth.
# Tests may modify fields before creating an app (e.g., CONFIG_DEFAULTS.gui_test_mode = True).
# Each AppConfig() copies from this at creation time.
CONFIG_DEFAULTS = ConfigData()
