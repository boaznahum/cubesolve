from collections.abc import Hashable
from typing import TYPE_CHECKING, Any, TypeAlias

from cube.domain.model.Color import Color

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

    1. ``fixed_attributes`` - Fixed to Slot (STAYS at position)
       - Properties of the physical slot itself
       - Includes structural info (origin, on_x, on_y, cw) set during Face.finish_init()
       - Also includes runtime fixed markers and tracking keys
       - NEVER moves during rotations
       - Use case: Coordinate system, rotation calculations, destination markers

    2. ``moveable_attributes`` - Color-Associated (MOVES with color)
       - Attributes that travel with the colored sticker during rotations
       - COPIED during copy_color() method
       - Keys: "n" (sequential number), tracker keys, "markers" list
       - Use case: Track a specific piece as it moves around the cube
       - Example: FaceTracker puts a key here to find a piece after rotation

    Animation Use Case:
        - AnnWhat.Moved → uses moveable_attributes → marker follows the sticker
        - AnnWhat.FixedPosition → uses fixed_attributes → marker stays at destination

    See: design2/partedge-attribute-system.md for visual diagrams
    """
    __slots__ = ["_face", "_parent", "_color", "_annotated_by_color",
                 "_annotated_fixed_location", "_texture_direction",
                 "fixed_attributes", "moveable_attributes"]

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
        - fixed_attributes: {} (fixed to slot - structural info + runtime markers)
        - moveable_attributes: {} (color-associated, moves with color)
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
        self.fixed_attributes: dict[Hashable, Any] = {}

        # Moveable attributes - MOVE with color during copy_color()
        # Used by FaceTracker, moveable markers (e.g., C1 from MarkerFactory)
        self.moveable_attributes: dict[Hashable, Any] = {}

        self._parent: _PartSlice

    @property
    def face(self) -> _Face:
        return self._face

    @property
    def parent(self) -> _PartSlice:
        return self._parent

    @property
    def color(self) -> Color:
        """
        The actual sticker color at this position.

        This is the moveable data - it gets swapped between PartEdges during
        cube rotations via copy_color() or rotate_4cycle().

        NOT to be confused with self.face.color which is the face's CENTER color
        (used for position_id calculations).
        """
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
        - moveable_attributes: All color-associated attributes (cleared then updated)

        What is NOT copied (stays at this slot):
        - _face: Physical face reference
        - fixed_attributes: Fixed slot properties (structural + runtime markers)

        This distinction enables:
        - Tracking pieces: Put marker in moveable_attributes, it follows the color
        - Marking destinations: Put marker in fixed_attributes, it stays put

        See: design2/partedge-attribute-system.md for visual diagrams
        """
        self._color = source._color
        self._annotated_by_color = source._annotated_by_color
        self._texture_direction = source._texture_direction
        self.moveable_attributes.clear()
        self.moveable_attributes.update(source.moveable_attributes)

    def clone(self) -> "PartEdge":
        """
        Used as temporary for rotate, must not be used in cube
        :return:
        """
        p = PartEdge(self._face, self._color)
        p._annotated_by_color = self._annotated_by_color
        p._texture_direction = self._texture_direction
        p.fixed_attributes = self.fixed_attributes.copy()
        p.moveable_attributes = self.moveable_attributes.copy()

        return p

    def clear_moveable_attributes(self) -> None:
        """Clear moveable (color-associated) attributes."""
        self.moveable_attributes.clear()

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

    @staticmethod
    def rotate_4cycle(p0: "PartEdge", p1: "PartEdge", p2: "PartEdge", p3: "PartEdge") -> None:
        """Rotate color data in a 4-cycle: p0 ← p1 ← p2 ← p3 ← p0.

        This is an optimized rotation that swaps references instead of copying.
        In a 4-cycle, we don't need to copy dict contents - just rotate references.

        Performance: O(1) for moveable_attributes instead of O(K) where K = number of attributes.

        The cycle direction matches the copy_color pattern:
        - p0 receives p1's color data
        - p1 receives p2's color data
        - p2 receives p3's color data
        - p3 receives p0's original color data

        What gets rotated (moves with color):
        - _color: The actual sticker color
        - _annotated_by_color: Color-based annotation flag
        - _texture_direction: Texture rotation state
        - moveable_attributes: Dict reference is swapped, not copied!

        Args:
            p0, p1, p2, p3: The four PartEdges in the cycle
        """
        # Save references from all 4 positions first
        colors = (p0._color, p1._color, p2._color, p3._color)
        annotated = (p0._annotated_by_color, p1._annotated_by_color,
                     p2._annotated_by_color, p3._annotated_by_color)
        textures = (p0._texture_direction, p1._texture_direction,
                    p2._texture_direction, p3._texture_direction)
        # Key optimization: save dict REFERENCES, not copies
        m_attrs = (p0.moveable_attributes, p1.moveable_attributes, p2.moveable_attributes, p3.moveable_attributes)

        # Rotate: p0 ← p1 ← p2 ← p3 ← p0
        p0._color, p1._color, p2._color, p3._color = colors[1], colors[2], colors[3], colors[0]
        p0._annotated_by_color, p1._annotated_by_color, p2._annotated_by_color, p3._annotated_by_color = \
            annotated[1], annotated[2], annotated[3], annotated[0]
        p0._texture_direction, p1._texture_direction, p2._texture_direction, p3._texture_direction = \
            textures[1], textures[2], textures[3], textures[0]
        # Swap dict references - O(1) instead of clear+update which is O(K)
        p0.moveable_attributes, p1.moveable_attributes, p2.moveable_attributes, p3.moveable_attributes = \
            m_attrs[1], m_attrs[2], m_attrs[3], m_attrs[0]
