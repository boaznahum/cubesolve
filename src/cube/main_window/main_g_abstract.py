from typing import Protocol, TYPE_CHECKING, Any, runtime_checkable

from cube.app.abstract_ap import AbstractApp
from cube.viewer.viewer_g import GCubeViewer

if TYPE_CHECKING:
    from cube.gui.protocols.renderer import Renderer


@runtime_checkable
class AbstractWindow(Protocol):
    """Protocol for the main application window.

    This defines the interface that keyboard/mouse handlers expect from a window.
    The concrete implementation (e.g., pyglet Window) implements this protocol.
    """

    # Class attribute for cursor type (used by _wait_cursor context manager)
    CURSOR_WAIT: str

    # Instance attribute for tracking edge solve count
    _last_edge_solve_count: int

    @property
    def app(self) -> AbstractApp:
        """Access the application."""
        ...

    @property
    def viewer(self) -> GCubeViewer:
        """Access the cube viewer."""
        ...

    @property
    def renderer(self) -> "Renderer":
        """Access the renderer for this window."""
        ...

    @property
    def width(self) -> int:
        """Window width in pixels."""
        ...

    @property
    def height(self) -> int:
        """Window height in pixels."""
        ...

    @property
    def animation_running(self) -> Any:
        """Whether animation is currently running."""
        ...

    def update_gui_elements(self) -> None:
        """Update all GUI elements."""
        ...

    def close(self) -> None:
        """Close the window."""
        ...

    # Cursor methods (used by keyboard handler)
    def get_system_mouse_cursor(self, cursor_type: Any) -> Any:
        """Get a system mouse cursor."""
        ...

    def set_mouse_cursor(self, cursor: Any) -> None:
        """Set the mouse cursor."""
        ...
