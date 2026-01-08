"""Factory for predefined marker configurations."""
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

    Developers can also create custom markers using create_* methods.
    """

    # ============================================================
    # Animation Markers (used by solver/animation system)
    # ============================================================

    def c0(self) -> MarkerConfig:
        """C0 marker - tracker anchor indicator.

        Full ring in complementary color, used to mark tracker anchor pieces
        during even-cube center solving.
        """
        return MarkerConfig(
            name="C0",
            shape=MarkerShape.RING,
            radius_factor=1.0,
            thickness=0.8,
            height_offset=0.15,
            use_complementary_color=True,
        )

    def c1(self) -> MarkerConfig:
        """C1 marker - moved piece indicator.

        Filled circle in complementary color, marks pieces that are being
        tracked during animation (follows the sticker color).
        """
        return MarkerConfig(
            name="C1",
            shape=MarkerShape.FILLED_CIRCLE,
            radius_factor=0.6,
            thickness=1.0,
            height_offset=0.15,
            use_complementary_color=True,
        )

    def c2(self) -> MarkerConfig:
        """C2 marker - destination slot indicator.

        Thin ring in complementary color, marks the destination position
        where a piece should end up (stays at fixed position).
        """
        return MarkerConfig(
            name="C2",
            shape=MarkerShape.RING,
            radius_factor=1.0,
            thickness=0.3,
            height_offset=0.15,
            use_complementary_color=True,
        )

    # ============================================================
    # Coordinate Markers (used by Face initialization)
    # ============================================================

    def origin(self) -> MarkerConfig:
        """Origin marker - face coordinate origin.

        Black X cross marking the [0,0] reference point on each face.
        """
        return MarkerConfig(
            name="ORIGIN",
            shape=MarkerShape.CROSS,
            color=(0.0, 0.0, 0.0),  # Black
            radius_factor=1.0,
            thickness=1.0,
            height_offset=0.0,  # Crosses are drawn at surface level
        )

    def on_x(self) -> MarkerConfig:
        """On-X marker - X-axis direction indicator.

        Blueviolet X cross marking the X-axis direction on each face.
        """
        return MarkerConfig(
            name="ON_X",
            shape=MarkerShape.CROSS,
            color=(0.54, 0.17, 0.89),  # Blueviolet
            radius_factor=1.0,
            thickness=1.0,
            height_offset=0.0,
        )

    def on_y(self) -> MarkerConfig:
        """On-Y marker - Y-axis direction indicator.

        Deepskyblue X cross marking the Y-axis direction on each face.
        """
        return MarkerConfig(
            name="ON_Y",
            shape=MarkerShape.CROSS,
            color=(0.0, 0.75, 1.0),  # Deepskyblue
            radius_factor=1.0,
            thickness=1.0,
            height_offset=0.0,
        )

    # ============================================================
    # LTR Coordinate System Markers
    # ============================================================

    def ltr_origin(self) -> MarkerConfig:
        """LTR origin marker - filled black circle at coordinate origin.

        Marks the [0,0] corner of the face's LTR coordinate system.
        """
        return MarkerConfig(
            name="LTR_ORIGIN",
            shape=MarkerShape.FILLED_CIRCLE,
            color=(0.0, 0.0, 0.0),  # Black
            radius_factor=0.4,
            thickness=1.0,
            height_offset=0.1,
        )

    def ltr_arrow_x(self) -> MarkerConfig:
        """LTR X-axis arrow - red arrow pointing right.

        Indicates the X-axis (left-to-right) direction on each face.
        """
        return MarkerConfig(
            name="LTR_ARROW_X",
            shape=MarkerShape.ARROW,
            color=(1.0, 0.0, 0.0),  # Red
            radius_factor=0.8,
            thickness=1.0,
            height_offset=0.0,
            direction=0.0,  # Right
        )

    def ltr_arrow_y(self) -> MarkerConfig:
        """LTR Y-axis arrow - blue arrow pointing up.

        Indicates the Y-axis (bottom-to-top) direction on each face.
        """
        return MarkerConfig(
            name="LTR_ARROW_Y",
            shape=MarkerShape.ARROW,
            color=(0.0, 0.0, 1.0),  # Blue
            radius_factor=0.8,
            thickness=1.0,
            height_offset=0.0,
            direction=90.0,  # Up
        )

    # ============================================================
    # Legacy Markers (with fixed colors from config)
    # ============================================================

    def c0_legacy(self) -> MarkerConfig:
        """C0 marker with legacy fixed color (mediumvioletred)."""
        return MarkerConfig(
            name="C0_LEGACY",
            shape=MarkerShape.RING,
            color=color_255_to_float((199, 21, 133)),  # mediumvioletred
            radius_factor=1.0,
            thickness=0.8,
            height_offset=0.1,
        )

    def c1_legacy(self) -> MarkerConfig:
        """C1 marker with legacy fixed color (mediumvioletred)."""
        return MarkerConfig(
            name="C1_LEGACY",
            shape=MarkerShape.FILLED_CIRCLE,
            color=color_255_to_float((199, 21, 133)),  # mediumvioletred
            radius_factor=0.6,
            thickness=1.0,
            height_offset=0.1,
        )

    def c2_legacy(self) -> MarkerConfig:
        """C2 marker with legacy fixed color (darkgreen)."""
        return MarkerConfig(
            name="C2_LEGACY",
            shape=MarkerShape.RING,
            color=color_255_to_float((0, 100, 0)),  # darkgreen
            radius_factor=1.0,
            thickness=0.3,
            height_offset=0.1,
        )

    # ============================================================
    # Custom Marker Creation
    # ============================================================

    def create_ring(
        self,
        name: str,
        color: tuple[float, float, float] | None = None,
        radius_factor: float = 1.0,
        thickness: float = 0.5,
        height_offset: float = 0.1,
        use_complementary_color: bool = False,
    ) -> MarkerConfig:
        """Create a custom ring marker."""
        return MarkerConfig(
            name=name,
            shape=MarkerShape.RING,
            color=color,
            radius_factor=radius_factor,
            thickness=thickness,
            height_offset=height_offset,
            use_complementary_color=use_complementary_color,
        )

    def create_filled_circle(
        self,
        name: str,
        color: tuple[float, float, float] | None = None,
        radius_factor: float = 0.6,
        height_offset: float = 0.1,
        use_complementary_color: bool = False,
    ) -> MarkerConfig:
        """Create a custom filled circle marker."""
        return MarkerConfig(
            name=name,
            shape=MarkerShape.FILLED_CIRCLE,
            color=color,
            radius_factor=radius_factor,
            thickness=1.0,  # Always filled
            height_offset=height_offset,
            use_complementary_color=use_complementary_color,
        )

    def create_cross(
        self,
        name: str,
        color: tuple[float, float, float],
    ) -> MarkerConfig:
        """Create a custom cross marker."""
        return MarkerConfig(
            name=name,
            shape=MarkerShape.CROSS,
            color=color,
            radius_factor=1.0,
            thickness=1.0,
            height_offset=0.0,  # Crosses are at surface level
        )

    # ============================================================
    # Get All Predefined Markers
    # ============================================================

    def get_all_predefined(self) -> dict[str, MarkerConfig]:
        """Get all predefined markers as a dictionary."""
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
