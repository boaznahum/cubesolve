"""
TextRenderer protocol definition.

This protocol defines the interface for text rendering.
"""

from typing import Protocol, runtime_checkable

from cube.gui.types import Color4


@runtime_checkable
class TextRenderer(Protocol):
    """Protocol for text rendering.

    Backends implement this to provide text display capabilities.
    """

    def draw_label(
        self,
        text: str,
        x: int,
        y: int,
        font_size: int = 12,
        color: Color4 = (255, 255, 255, 255),
        bold: bool = False,
        anchor_x: str = "left",
        anchor_y: str = "bottom",
    ) -> None:
        """Draw text at the specified position.

        Args:
            text: Text string to render
            x: X position in window coordinates
            y: Y position in window coordinates
            font_size: Font size in points
            color: RGBA text color
            bold: Whether to use bold font
            anchor_x: Horizontal anchor ('left', 'center', 'right')
            anchor_y: Vertical anchor ('top', 'center', 'bottom')
        """
        ...

    def clear_labels(self) -> None:
        """Clear all previously drawn labels.

        Called before redrawing text each frame.
        """
        ...
