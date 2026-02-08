"""Factory for predefined marker configurations with singleton caching."""
from __future__ import annotations

from .IMarkerFactory import IMarkerFactory
from ._marker_config import MarkerConfig, color_255_to_float
from .MarkerShape import MarkerShape


class MarkerFactory(IMarkerFactory):
    """Factory providing predefined marker configurations.

    Implements IMarkerFactory protocol.

    This factory provides all standard markers used in the application:
    - Animation markers: C0, C1, C2
    - Coordinate markers: ORIGIN, ON_X, ON_Y
    - Debug/sample markers

    All factory methods use caching (singleton pattern) - calling the same method
    with the same arguments returns the same MarkerConfig instance every time.
    The cache is maintained at the class level, shared across all instances.

    Developers can also create custom markers using create_* methods.
    """

    # Class-level cache for singleton instances
    _cache: dict[tuple[str, ...], MarkerConfig] = {}

    # ============================================================
    # Animation Markers (used by solver/animation system)
    # ============================================================

    def center_tracker(self) -> MarkerConfig:
        """Center tracker marker - small filled circle on tracked center slices.

        Shows "this piece is being tracked" with a small complementary-color dot.
        Distinct from c0() which marks the tracker anchor for animation.
        """
        key = ("center_tracker",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.FILLED_CIRCLE,
                radius_factor=0.4,
                thickness=1.0,
                height_offset=0.12,
                use_complementary_color=True,
            )
        return MarkerFactory._cache[key]

    def c0(self) -> MarkerConfig:
        """C0 marker - tracker anchor indicator.

        Full ring in complementary color, used to mark tracker anchor pieces
        during even-cube center solving.
        """
        key = ("c0",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.RING,
                radius_factor=1.0,
                thickness=0.8,
                height_offset=0.15,
                use_complementary_color=True,
            )
        return MarkerFactory._cache[key]

    def c1(self) -> MarkerConfig:
        """C1 marker - moved piece indicator.

        Filled circle in complementary color, marks pieces that are being
        tracked during animation (follows the sticker color).
        """
        key = ("c1",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.FILLED_CIRCLE,
                radius_factor=0.6,
                thickness=1.0,
                height_offset=0.15,
                use_complementary_color=True,
            )
        return MarkerFactory._cache[key]

    def c2(self) -> MarkerConfig:
        """C2 marker - destination slot indicator.

        Thin ring in complementary color, marks the destination position
        where a piece should end up (stays at fixed position).
        """
        key = ("c2",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.RING,
                radius_factor=1.0,
                thickness=0.3,
                height_offset=0.15,
                use_complementary_color=True,
            )
        return MarkerFactory._cache[key]

    def at_risk(self) -> MarkerConfig:
        """At-risk marker - bold red X for pieces that may be destroyed.

        Used in commutator 3-cycle to mark the s2 piece (second point on source)
        which will be replaced by whatever is at the target position.
        This warns the user that this piece is at risk of being destroyed.

        Uses BOLD_CROSS shape (thick capsule strokes like CHECKMARK).
        """
        key = ("at_risk",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.BOLD_CROSS,
                color=(1.0, 0.2, 0.2),  # Red
                radius_factor=0.85,     # Same as checkmark
                thickness=1.0,          # Bold strokes
                height_offset=0.15,     # Same as c1/c2
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Coordinate Markers (used by Face initialization)
    # ============================================================

    def origin(self) -> MarkerConfig:
        """Origin marker - face coordinate origin.

        Black X cross marking the [0,0] reference point on each face.
        """
        key = ("origin",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.CROSS,
                color=(0.0, 0.0, 0.0),  # Black
                radius_factor=1.0,
                thickness=1.0,
                height_offset=0.0,  # Crosses are drawn at surface level
            )
        return MarkerFactory._cache[key]

    def on_x(self) -> MarkerConfig:
        """On-X marker - X-axis direction indicator.

        Blueviolet X cross marking the X-axis direction on each face.
        """
        key = ("on_x",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.CROSS,
                color=(0.54, 0.17, 0.89),  # Blueviolet
                radius_factor=1.0,
                thickness=1.0,
                height_offset=0.0,
            )
        return MarkerFactory._cache[key]

    def on_y(self) -> MarkerConfig:
        """On-Y marker - Y-axis direction indicator.

        Deepskyblue X cross marking the Y-axis direction on each face.
        """
        key = ("on_y",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.CROSS,
                color=(0.0, 0.75, 1.0),  # Deepskyblue
                radius_factor=1.0,
                thickness=1.0,
                height_offset=0.0,
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # LTR Coordinate System Markers
    # ============================================================

    def ltr_origin(self) -> MarkerConfig:
        """LTR origin marker - filled black circle at coordinate origin.

        Marks the [0,0] corner of the face's LTR coordinate system.
        """
        key = ("ltr_origin",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.FILLED_CIRCLE,
                color=(0.0, 0.0, 0.0),  # Black
                radius_factor=0.4,
                thickness=1.0,
                height_offset=0.1,
            )
        return MarkerFactory._cache[key]

    def ltr_arrow_x(self) -> MarkerConfig:
        """LTR X-axis arrow - red arrow pointing right.

        Indicates the X-axis (left-to-right) direction on each face.
        """
        key = ("ltr_arrow_x",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.ARROW,
                color=(1.0, 0.0, 0.0),  # Red
                radius_factor=0.8,
                thickness=1.0,
                height_offset=0.0,
                direction=0.0,  # Right
            )
        return MarkerFactory._cache[key]

    def ltr_arrow_y(self) -> MarkerConfig:
        """LTR Y-axis arrow - blue arrow pointing up.

        Indicates the Y-axis (bottom-to-top) direction on each face.
        """
        key = ("ltr_arrow_y",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.ARROW,
                color=(0.0, 0.0, 1.0),  # Blue
                radius_factor=0.8,
                thickness=1.0,
                height_offset=0.0,
                direction=90.0,  # Up
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Legacy Markers (with fixed colors from config)
    # ============================================================

    def c0_legacy(self) -> MarkerConfig:
        """C0 marker with legacy fixed color (mediumvioletred)."""
        key = ("c0_legacy",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.RING,
                color=color_255_to_float((199, 21, 133)),  # mediumvioletred
                radius_factor=1.0,
                thickness=0.8,
                height_offset=0.1,
            )
        return MarkerFactory._cache[key]

    def c1_legacy(self) -> MarkerConfig:
        """C1 marker with legacy fixed color (mediumvioletred)."""
        key = ("c1_legacy",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.FILLED_CIRCLE,
                color=color_255_to_float((199, 21, 133)),  # mediumvioletred
                radius_factor=0.6,
                thickness=1.0,
                height_offset=0.1,
            )
        return MarkerFactory._cache[key]

    def c2_legacy(self) -> MarkerConfig:
        """C2 marker with legacy fixed color (darkgreen)."""
        key = ("c2_legacy",)
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.RING,
                color=color_255_to_float((0, 100, 0)),  # darkgreen
                radius_factor=1.0,
                thickness=0.3,
                height_offset=0.1,
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Custom Marker Creation
    # ============================================================

    def create_ring(
        self,
        color: tuple[float, float, float] | None = None,
        radius_factor: float = 1.0,
        thickness: float = 0.5,
        height_offset: float = 0.1,
        use_complementary_color: bool = False,
    ) -> MarkerConfig:
        """Create a custom ring marker."""
        key = ("create_ring", str(color), str(radius_factor), str(thickness), str(height_offset), str(use_complementary_color))
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.RING,
                color=color,
                radius_factor=radius_factor,
                thickness=thickness,
                height_offset=height_offset,
                use_complementary_color=use_complementary_color,
            )
        return MarkerFactory._cache[key]

    def create_filled_circle(
        self,
        color: tuple[float, float, float] | None = None,
        radius_factor: float = 0.6,
        height_offset: float = 0.1,
        use_complementary_color: bool = False,
    ) -> MarkerConfig:
        """Create a custom filled circle marker."""
        key = ("create_filled_circle", str(color), str(radius_factor), str(height_offset), str(use_complementary_color))
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.FILLED_CIRCLE,
                color=color,
                radius_factor=radius_factor,
                thickness=1.0,  # Always filled
                height_offset=height_offset,
                use_complementary_color=use_complementary_color,
            )
        return MarkerFactory._cache[key]

    def create_cross(
        self,
        color: tuple[float, float, float],
    ) -> MarkerConfig:
        """Create a custom cross marker."""
        key = ("create_cross", str(color))
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.CROSS,
                color=color,
                radius_factor=1.0,
                thickness=1.0,
                height_offset=0.0,  # Crosses are at surface level
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Special Shape Markers
    # ============================================================

    def checkmark(
        self,
        color: tuple[float, float, float] = (0.0, 0.8, 0.0),
    ) -> MarkerConfig:
        """Create a thick green checkmark (✓) marker.

        A beautiful, thick checkmark indicating success/completion.
        Cached by color.

        Args:
            color: RGB color tuple (0.0-1.0 range). Default bright green.

        Returns:
            MarkerConfig for the checkmark marker.
        """
        key = ("checkmark", str(color))
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.CHECKMARK,
                color=color,
                radius_factor=0.85,
                thickness=1.0,  # Bold strokes
                height_offset=0.08,  # Low, just above surface
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Character Markers
    # ============================================================

    def char(
        self,
        character: str,
        color: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> MarkerConfig:
        """Create a character marker.

        Draws a single character on the cell. Cached by (character, color) tuple.

        Args:
            character: Single character to display (e.g., "A", "1", "+")
            color: RGB color tuple (0.0-1.0 range). Default black.

        Returns:
            MarkerConfig for the character marker.
        """
        key = ("char", character, str(color))
        if key not in MarkerFactory._cache:
            MarkerFactory._cache[key] = MarkerConfig(
                shape=MarkerShape.CHARACTER,
                color=color,
                radius_factor=0.8,
                thickness=1.0,
                height_offset=0.1,
                character=character,
            )
        return MarkerFactory._cache[key]

    # ============================================================
    # Get All Predefined Markers
    # ============================================================

    def get_all_predefined(self) -> dict[str, MarkerConfig]:
        """Get all predefined markers as a dictionary.

        Note: The keys are suggested names, but callers provide actual names
        when adding markers via MarkerManager.
        """
        return {
            "C0": self.c0(),
            "C1": self.c1(),
            "C2": self.c2(),
            "ORIGIN": self.origin(),
            "ON_X": self.on_x(),
            "ON_Y": self.on_y(),
            "C0_LEGACY": self.c0_legacy(),
            "C1_LEGACY": self.c1_legacy(),
            "C2_LEGACY": self.c2_legacy(),
        }
