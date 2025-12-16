"""
Native pyglet GUI toolbar with clickable buttons.

Simple approach: rectangles + text labels, direct mouse click handling.
No deferred command execution needed - commands run immediately on click.

This file contains ALL GUI controls setup and handling in one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

import pyglet
from pyglet import shapes

if TYPE_CHECKING:
    from cube.presentation.gui.backends.pyglet2.PygletAppWindow import PygletAppWindow
    from cube.presentation.gui.commands import Command

# Button style constants - bright and visible
BUTTON_HEIGHT = 32
BUTTON_PADDING = 8
BUTTON_MARGIN = 5
ROW_MARGIN = 4
BUTTON_BG_COLOR = (70, 130, 180, 255)      # Steel blue
BUTTON_BG_HOVER = (100, 160, 210, 255)     # Lighter blue on hover
BUTTON_BG_DISABLED = (80, 80, 80, 200)     # Gray when disabled
BUTTON_TEXT_COLOR = (255, 255, 255, 255)   # White text
BUTTON_TEXT_DISABLED = (140, 140, 140, 255)
TOOLBAR_BG_COLOR = (40, 40, 40, 240)       # Dark background
TOOLBAR_PADDING = 10
SEPARATOR_WIDTH = 15
LABEL_COLOR = (200, 200, 200, 255)         # Light gray for labels
FONT_SIZE = 12


@dataclass
class GUIButton:
    """A clickable button in the toolbar."""

    label: str
    command: Command | None  # None for display-only labels
    row: int = 0  # Which row this button belongs to
    x: int = 0
    y: int = 0
    width: int = 0
    enabled_fn: Callable[[], bool] | None = None
    label_fn: Callable[[], str] | None = None  # Dynamic label
    is_label: bool = False  # True for non-clickable text labels
    min_width: int = 0  # Minimum width for the button

    def get_label(self) -> str:
        """Get current label (static or dynamic)."""
        if self.label_fn:
            return self.label_fn()
        return self.label

    def is_enabled(self) -> bool:
        """Check if button is enabled."""
        if self.is_label:
            return False
        if self.enabled_fn is None:
            return True
        return self.enabled_fn()

    def contains(self, mx: int, my: int) -> bool:
        """Check if point (mx, my) is inside button bounds."""
        return (self.x <= mx <= self.x + self.width and
                self.y <= my <= self.y + BUTTON_HEIGHT)


class GUIToolbar:
    """A multi-row toolbar with clickable buttons, aligned to top-right.

    All GUI controls setup and event handling is centralized here.
    PygletAppWindow only needs to:
    - Call create_toolbar() to set up
    - Call toolbar.draw() in on_draw()
    - Call toolbar.handle_click(x, y) in on_mouse_press()
    - Call toolbar.handle_motion(x, y) in on_mouse_motion()
    - Call toolbar.update_window_size() in on_resize()
    """

    def __init__(self, window_width: int, window_height: int):
        """Initialize toolbar."""
        self._window_width = window_width
        self._window_height = window_height
        self._buttons: list[GUIButton] = []
        self._current_row = 0
        self._batch = pyglet.graphics.Batch()
        self._hover_button: GUIButton | None = None

        # Shapes for rendering
        self._shapes_dirty = True
        self._bg_rect: shapes.Rectangle | None = None
        self._button_rects: list[shapes.Rectangle | None] = []
        self._button_labels: list[pyglet.text.Label | None] = []

    def add_button(
        self,
        label: str,
        command: Command,
        enabled_fn: Callable[[], bool] | None = None,
        label_fn: Callable[[], str] | None = None,
        min_width: int = 0,
    ) -> None:
        """Add a clickable button to current row."""
        self._buttons.append(GUIButton(
            label=label,
            command=command,
            row=self._current_row,
            enabled_fn=enabled_fn,
            label_fn=label_fn,
            min_width=min_width,
        ))
        self._shapes_dirty = True

    def add_label(self, label: str, label_fn: Callable[[], str] | None = None, min_width: int = 0) -> None:
        """Add a non-clickable text label to current row."""
        self._buttons.append(GUIButton(
            label=label,
            command=None,
            row=self._current_row,
            is_label=True,
            label_fn=label_fn,
            min_width=min_width,
        ))
        self._shapes_dirty = True

    def add_separator(self) -> None:
        """Add visual spacing between button groups."""
        self._buttons.append(GUIButton(
            label="",
            command=None,
            row=self._current_row,
            is_label=True,
            min_width=SEPARATOR_WIDTH,
        ))
        self._shapes_dirty = True

    def new_row(self) -> None:
        """Start a new row of buttons."""
        self._current_row += 1
        self._shapes_dirty = True

    def update_window_size(self, width: int, height: int) -> None:
        """Update when window is resized."""
        self._window_width = width
        self._window_height = height
        self._shapes_dirty = True

    def _rebuild_shapes(self) -> None:
        """Rebuild all shapes."""
        self._batch = pyglet.graphics.Batch()
        self._button_rects.clear()
        self._button_labels.clear()

        if not self._buttons:
            self._bg_rect = None
            return

        # Group buttons by row
        rows: list[list[GUIButton]] = []
        for btn in self._buttons:
            while len(rows) <= btn.row:
                rows.append([])
            rows[btn.row].append(btn)

        # Calculate width for each button and row widths
        row_widths: list[int] = []
        for row_buttons in rows:
            row_width = TOOLBAR_PADDING
            for btn in row_buttons:
                current_label = btn.get_label()
                text_width = len(current_label) * 9 + BUTTON_PADDING * 2
                btn.width = max(text_width, btn.min_width, 36)
                row_width += btn.width + BUTTON_MARGIN
            row_widths.append(row_width - BUTTON_MARGIN + TOOLBAR_PADDING)

        # Find max row width for toolbar background
        max_row_width = max(row_widths) if row_widths else 0
        num_rows = len(rows)
        toolbar_height = num_rows * BUTTON_HEIGHT + (num_rows - 1) * ROW_MARGIN + TOOLBAR_PADDING * 2

        # Position toolbar at top-right
        toolbar_x = self._window_width - max_row_width
        toolbar_y = self._window_height - toolbar_height

        # Toolbar background
        self._bg_rect = shapes.Rectangle(
            toolbar_x, toolbar_y,
            max_row_width, toolbar_height,
            color=TOOLBAR_BG_COLOR[:3],
            batch=self._batch
        )
        self._bg_rect.opacity = TOOLBAR_BG_COLOR[3]

        # Position buttons right-aligned within each row
        for row_idx, row_buttons in enumerate(rows):
            # Calculate row start position (right-aligned)
            row_width = row_widths[row_idx]
            x = self._window_width - row_width + TOOLBAR_PADDING
            y = self._window_height - TOOLBAR_PADDING - BUTTON_HEIGHT - row_idx * (BUTTON_HEIGHT + ROW_MARGIN)

            for btn in row_buttons:
                btn.x = x
                btn.y = y
                x += btn.width + BUTTON_MARGIN

        # Create button shapes and labels
        for btn in self._buttons:
            current_label = btn.get_label()

            if btn.is_label:
                # Non-clickable label - no background rectangle
                self._button_rects.append(None)
            else:
                enabled = btn.is_enabled()
                bg_color = BUTTON_BG_COLOR if enabled else BUTTON_BG_DISABLED

                rect = shapes.Rectangle(
                    btn.x, btn.y, btn.width, BUTTON_HEIGHT,
                    color=bg_color[:3],
                    batch=self._batch
                )
                rect.opacity = bg_color[3]
                self._button_rects.append(rect)

            # Text label
            if current_label:
                text_color = LABEL_COLOR if btn.is_label else (
                    BUTTON_TEXT_COLOR if btn.is_enabled() else BUTTON_TEXT_DISABLED
                )
                label = pyglet.text.Label(
                    current_label,
                    font_size=FONT_SIZE,
                    x=btn.x + btn.width // 2,
                    y=btn.y + BUTTON_HEIGHT // 2,
                    anchor_x='center',
                    anchor_y='center',
                    color=text_color,
                    batch=self._batch
                )
                self._button_labels.append(label)
            else:
                self._button_labels.append(None)

        self._shapes_dirty = False

    def draw(self) -> None:
        """Draw the toolbar."""
        # Always rebuild to handle dynamic labels
        self._rebuild_shapes()

        # Update button colors based on hover state
        for i, btn in enumerate(self._buttons):
            rect = self._button_rects[i]
            if btn.is_label or rect is None:
                continue

            enabled = btn.is_enabled()
            is_hover = btn == self._hover_button and enabled

            if is_hover:
                bg_color = BUTTON_BG_HOVER
            elif enabled:
                bg_color = BUTTON_BG_COLOR
            else:
                bg_color = BUTTON_BG_DISABLED

            rect.color = bg_color[:3]
            rect.opacity = bg_color[3]

            text_color = BUTTON_TEXT_COLOR if enabled else BUTTON_TEXT_DISABLED
            label = self._button_labels[i]
            if label:
                label.color = text_color

        self._batch.draw()

    def handle_click(self, x: int, y: int) -> Command | None:
        """Handle mouse click. Returns command to execute or None."""
        for btn in self._buttons:
            if btn.contains(x, y) and btn.is_enabled() and btn.command:
                return btn.command
        return None

    def handle_motion(self, x: int, y: int) -> None:
        """Handle mouse motion for hover effects."""
        self._hover_button = None
        for btn in self._buttons:
            if btn.contains(x, y) and not btn.is_label:
                self._hover_button = btn
                break


def create_toolbar(window: PygletAppWindow) -> GUIToolbar:
    """Factory function to create and configure the standard toolbar.

    This is the SINGLE PLACE where all GUI controls are defined.
    To add/remove/modify buttons, edit this function.

    Args:
        window: The PygletAppWindow instance

    Returns:
        Configured GUIToolbar ready to use
    """
    from cube.presentation.gui.commands import Commands

    toolbar = GUIToolbar(window.width, window.height)
    app = window.app
    vs = app.vs
    op = app.op

    # === ROW 1: Size, Scramble, Solve/Reset ===

    # Cube size display and controls
    toolbar.add_label("Size", label_fn=lambda: f"{app.cube.size}x{app.cube.size}", min_width=50)
    toolbar.add_button("-", Commands.SIZE_DEC)
    toolbar.add_button("+", Commands.SIZE_INC)

    toolbar.add_separator()

    # Scramble buttons 0-9
    toolbar.add_button("0", Commands.SCRAMBLE_0)
    toolbar.add_button("1", Commands.SCRAMBLE_1)
    toolbar.add_button("2", Commands.SCRAMBLE_2)
    toolbar.add_button("3", Commands.SCRAMBLE_3)
    toolbar.add_button("4", Commands.SCRAMBLE_4)
    toolbar.add_button("5", Commands.SCRAMBLE_5)
    toolbar.add_button("6", Commands.SCRAMBLE_6)
    toolbar.add_button("7", Commands.SCRAMBLE_7)
    toolbar.add_button("8", Commands.SCRAMBLE_8)
    toolbar.add_button("9", Commands.SCRAMBLE_9)

    toolbar.add_separator()

    # Solve controls
    toolbar.add_button("Solve", Commands.SOLVE_ALL)
    toolbar.add_button("Instant", Commands.SOLVE_ALL_NO_ANIMATION)
    toolbar.add_button("Reset", Commands.RESET_CUBE)

    # === ROW 2: Animation, Speed, Debug, SS, Stop, Quit ===
    toolbar.new_row()

    # Animation controls
    toolbar.add_button(
        "Anim",
        Commands.TOGGLE_ANIMATION,
        label_fn=lambda: "Anim:ON" if op.animation_enabled else "Anim:OFF",
        min_width=70,
    )

    # Speed controls
    toolbar.add_label("Spd", label_fn=lambda: f"[{vs.get_speed_index}]", min_width=40)
    toolbar.add_button("-", Commands.SPEED_DOWN)
    toolbar.add_button("+", Commands.SPEED_UP)

    toolbar.add_separator()

    # Debug and single-step
    toolbar.add_button(
        "Debug",
        Commands.TOGGLE_DEBUG,
        label_fn=lambda: "Dbg:ON" if app.slv.is_debug_config_mode else "Dbg:OFF",
        min_width=65,
    )
    toolbar.add_button(
        "SS",
        Commands.SINGLE_STEP_TOGGLE,
        label_fn=lambda: "SS:ON" if vs.single_step_mode else "SS:OFF",
        min_width=55,
    )

    # Next step (enabled when paused)
    toolbar.add_button(
        "Next",
        Commands.PAUSE_TOGGLE,
        enabled_fn=lambda: vs.paused_on_single_step_mode is not None,
    )

    # Stop (enabled when animation running)
    toolbar.add_button(
        "Stop",
        Commands.STOP_ANIMATION,
        enabled_fn=lambda: window.animation_running,
    )

    toolbar.add_separator()

    toolbar.add_button("Quit", Commands.QUIT)

    return toolbar
