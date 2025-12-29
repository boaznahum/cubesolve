from collections import defaultdict
from collections.abc import Hashable
from typing import TYPE_CHECKING, Any, TypeAlias

from .cube_boy import Color

if TYPE_CHECKING:
    from ._part_slice import PartSlice
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

    THREE ATTRIBUTE DICTIONARIES
    ============================
    PartEdge has three distinct attribute systems for different use cases:

    1. ``attributes`` - Structural/Positional (FIXED)
       - Properties of the physical slot itself
       - Set once during Face.finish_init()
       - Keys: "origin", "on_x", "on_y", "cw" (clockwise index)
       - NEVER move during rotations
       - Used for coordinate system and rotation calculations

    2. ``c_attributes`` - Color-Associated (MOVES with color)
       - Attributes that travel with the colored sticker during rotations
       - COPIED during copy_color() method
       - Keys: "n" (sequential number), tracker keys, VMarker.C1
       - Use case: Track a specific piece as it moves around the cube
       - Example: FaceTracker puts a key here to find a piece after rotation

    3. ``f_attributes`` - Fixed to Slot (STAYS at position)
       - Attributes that stay at the physical slot position
       - NOT copied during copy_color()
       - Keys: destination markers, VMarker.C2
       - Use case: Mark where a piece should end up (destination)
       - Uses defaultdict(bool) so missing keys return False

    Animation Use Case:
        - AnnWhat.Moved → uses c_attributes → marker follows the sticker
        - AnnWhat.FixedPosition → uses f_attributes → marker stays at destination

    See: design2/partedge-attribute-system.md for visual diagrams
    """
    __slots__ = ["_face", "_parent", "_color", "_annotated_by_color",
                 "_annotated_fixed_location", "_texture_direction",
                 "attributes", "c_attributes",
                 "f_attributes"]

    _face: _Face
    _color: Color
    _texture_direction: int  # 0=0°, 1=90°CW, 2=180°, 3=270°CW - see design2/face-slice-rotation.md

    def __init__(self, face: _Face, color: Color) -> None:
        """
        Create a PartEdge on a specific face with an initial color.

        Args:
            face: The Face this edge belongs to (fixed, never changes)
            color: Initial color of the sticker (can change during rotation)

        The three attribute dictionaries are initialized empty:
        - attributes: {} (structural, set by Face.finish_init)
        - c_attributes: {} (color-associated, moves with color)
        - f_attributes: defaultdict(bool) (fixed, stays at slot)
        """
        super().__init__()
        self._face = face
        self._color = color
        self._annotated_by_color: bool = False
        self._annotated_fixed_location: bool = False
        self._texture_direction: int = 0  # Texture rotation: 0=0°, 1=90°CW, 2=180°, 3=270°CW

        # Structural attributes - physical slot properties (origin, cw, on_x, on_y)
        # Set by Face.finish_init(), never move during rotation
        self.attributes: dict[Hashable, Any] = {}

        # Color-associated attributes - MOVE with color during copy_color()
        # Used by FaceTracker, animation markers (VMarker.C1)
        self.c_attributes: dict[Hashable, Any] = {}

        # Fixed attributes - STAY at physical slot, NOT copied during rotation
        # Used for destination markers (VMarker.C2)
        self.f_attributes: dict[Hashable, Any] = defaultdict(bool)

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
        - attributes: Structural slot properties
        - f_attributes: Fixed destination markers

        This distinction enables:
        - Tracking pieces: Put marker in c_attributes, it follows the color
        - Marking destinations: Put marker in f_attributes, it stays put

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
