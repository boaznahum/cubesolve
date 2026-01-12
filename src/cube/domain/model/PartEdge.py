from collections.abc import Hashable
from typing import TYPE_CHECKING, Any, TypeAlias

from cube.domain.geometric.cube_boy import Color

if TYPE_CHECKING:
    from .PartSlice import PartSlice
    from .Cube import Cube
    from .Face import Face

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "Cube"  # type: ignore
_PartSlice: TypeAlias = "PartSlice"  # type: ignore


class PartEdge:
    """
    The smallest unit of the cube model, representing a single colored sticker.

    Each PartEdge belongs to exactly one Face and is aggregated by a PartSlice.
    The color can change during rotations (via copy_color), but the face reference
    is fixed - representing the physical slot position.

    TWO ATTRIBUTE DICTIONARIES
    ==========================
    PartEdge has two distinct attribute systems for different use cases:

    1. ``attributes`` - Fixed to Slot (STAYS at position)
       - Properties of the physical slot itself
       - Includes structural info (origin, on_x, on_y, cw) set during Face.finish_init()
       - Also includes runtime fixed markers and tracking keys
       - NEVER moves during rotations
       - Use case: Coordinate system, rotation calculations, destination markers

    2. ``c_attributes`` - Color-Associated (MOVES with color)
       - Attributes that travel with the colored sticker during rotations
       - COPIED during copy_color() method
       - Keys: "n" (sequential number), tracker keys, "markers" list
       - Use case: Track a specific piece as it moves around the cube
       - Example: FaceTracker puts a key here to find a piece after rotation

    Animation Use Case:
        - AnnWhat.Moved → uses c_attributes → marker follows the sticker
        - AnnWhat.FixedPosition → uses attributes → marker stays at destination

    See: design2/partedge-attribute-system.md for visual diagrams
    """
    __slots__ = ["_face", "_parent", "_color", "_annotated_by_color",
                 "_annotated_fixed_location", "_texture_direction",
                 "attributes", "c_attributes"]

    _face: _Face
    _color: Color
    _texture_direction: int  # 0=0°, 1=90°CW, 2=180°, 3=270°CW - see design2/face-slice-rotation.md

    def __init__(self, face: _Face, color: Color) -> None:
        """
        Create a PartEdge on a specific face with an initial color.

        Args:
            face: The Face this edge belongs to (fixed, never changes)
            color: Initial color of the sticker (can change during rotation)

        The two attribute dictionaries are initialized empty:
        - attributes: {} (fixed to slot - structural info + runtime markers)
        - c_attributes: {} (color-associated, moves with color)
        """
        super().__init__()
        self._face = face
        self._color = color
        self._annotated_by_color: bool = False
        self._annotated_fixed_location: bool = False
        self._texture_direction: int = 0  # Texture rotation: 0=0°, 1=90°CW, 2=180°, 3=270°CW

        # Fixed attributes - STAY at physical slot, NOT copied during rotation
        # Includes structural properties (origin, cw, on_x, on_y) set by Face.finish_init()
        # Also includes runtime fixed markers (e.g., C2 destination markers)
        self.attributes: dict[Hashable, Any] = {}

        # Color-associated attributes - MOVE with color during copy_color()
        # Used by FaceTracker, moveable markers (e.g., C1 from MarkerFactory)
        self.c_attributes: dict[Hashable, Any] = {}

        self._parent: _PartSlice

    @property
    def face(self) -> _Face:
        return self._face

    @property
    def parent(self) -> _PartSlice:
        return self._parent

    @property
    def color(self) -> Color:
        return self._color

    def __str__(self) -> str:
        if self._face.config.short_part_name:
            return str(self._color.name)
        else:
            return f"{self._color.name}@{self._face}"

    def copy_color(self, source: "PartEdge"):
        """
        Copy color and color-associated attributes from source.

        This is the core rotation mechanic - colors move between physical slots.
        Called by PartSlice.copy_colors() during face rotation.

        What gets COPIED:
        - _color: The actual sticker color
        - _annotated_by_color: Color-based annotation flag
        - c_attributes: All color-associated attributes (cleared then updated)

        What is NOT copied (stays at this slot):
        - _face: Physical face reference
        - attributes: Fixed slot properties (structural + runtime markers)

        This distinction enables:
        - Tracking pieces: Put marker in c_attributes, it follows the color
        - Marking destinations: Put marker in attributes, it stays put

        See: design2/partedge-attribute-system.md for visual diagrams
        """
        self._color = source._color
        self._annotated_by_color = source._annotated_by_color
        self._texture_direction = source._texture_direction
        self.c_attributes.clear()
        self.c_attributes.update(source.c_attributes)

    def clone(self) -> "PartEdge":
        """
        Used as temporary for rotate, must not be used in cube
        :return:
        """
        p = PartEdge(self._face, self._color)
        p._annotated_by_color = self._annotated_by_color
        p._texture_direction = self._texture_direction
        p.attributes = self.attributes.copy()
        p.c_attributes = self.c_attributes.copy()

        return p

    def clear_c_attributes(self) -> None:
        """Clear color-associated attributes."""
        self.c_attributes.clear()

    def annotate(self, fixed_location: bool):
        if fixed_location:
            self._annotated_fixed_location = True
        else:
            self._annotated_by_color = True

    def un_annotate(self):
        self._annotated_by_color = False
        self._annotated_fixed_location = False

    @property
    def annotated(self) -> Any:
        return self._annotated_by_color or self._annotated_fixed_location

    @property
    def annotated_by_color(self) -> Any:
        return self._annotated_by_color

    @property
    def annotated_fixed(self) -> Any:
        return self._annotated_fixed_location

    @property
    def texture_direction(self) -> int:
        """Texture rotation: 0=0°, 1=90°CW, 2=180°, 3=270°CW.

        See: design2/face-slice-rotation.md for details on how this is updated
        during face rotations.
        """
        return self._texture_direction

    def rotate_texture(self, quarter_turns: int = 1) -> None:
        """Rotate the texture direction by the given number of quarter turns CW.

        Args:
            quarter_turns: Number of 90° clockwise rotations (can be negative)
        """
        self._texture_direction = (self._texture_direction + quarter_turns) % 4
