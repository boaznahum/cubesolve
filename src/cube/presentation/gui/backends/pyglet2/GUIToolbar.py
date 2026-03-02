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

from cube.domain.solver import SolveStep
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.presentation.gui.backends.pyglet2.PygletAppWindow import PygletAppWindow
    from cube.presentation.gui.commands import Command
    from cube.presentation.gui.key_bindings import KeyBindingService

# Button style constants - bright and visible
BUTTON_HEIGHT = 32
BUTTON_PADDING = 8
BUTTON_MARGIN = 5
ROW_MARGIN = 4
BEVEL_WIDTH = 2  # Width of 3D bevel effect

# Button colors
BUTTON_BG_COLOR = (70, 130, 180, 255)  # Steel blue
BUTTON_BG_HOVER = (100, 160, 210, 255)  # Lighter blue on hover
BUTTON_BG_DISABLED = (80, 80, 80, 200)  # Gray when disabled
BUTTON_HIGHLIGHT = (130, 180, 220, 255)  # Light edge (top/left) - raised look
BUTTON_SHADOW = (30, 70, 110, 255)  # Dark edge (bottom/right) - raised look
BUTTON_HIGHLIGHT_DISABLED = (110, 110, 110, 200)
BUTTON_SHADOW_DISABLED = (50, 50, 50, 200)

BUTTON_TEXT_COLOR = (255, 255, 255, 255)  # White text
BUTTON_TEXT_DISABLED = (140, 140, 140, 255)
TOOLBAR_BG_COLOR = (40, 40, 40, 240)  # Dark background
TOOLBAR_PADDING = 10
SEPARATOR_WIDTH = 15
LABEL_COLOR = (200, 200, 200, 255)  # Light gray for labels
FONT_SIZE = 12

# Dropdown style constants
DROPDOWN_BG_COLOR = (50, 50, 60, 245)
DROPDOWN_ITEM_HOVER = (80, 120, 170, 255)
DROPDOWN_ITEM_CURRENT = (60, 90, 130, 255)  # Slightly highlighted for current solver
DROPDOWN_TEXT_COLOR = (255, 255, 255, 255)
DROPDOWN_CURRENT_TEXT = (180, 220, 255, 255)  # Brighter text for current solver
DROPDOWN_BORDER_COLOR = (100, 140, 180, 255)
DROPDOWN_ITEM_HEIGHT = 28
DROPDOWN_ITEM_PADDING = 6


# Sentinel tag to identify the Solver button for dropdown toggling
_SOLVER_BUTTON_TAG = "__solver_dropdown__"


@dataclass
class DropdownItem:
    """An item in the solver dropdown menu."""
    label: str
    solver_name: SolverName
    is_current: bool


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
    tooltip: str | None = None  # Hover tooltip text
    shift_label: str | None = None  # Alternative label when Shift is held
    shift_command: "Command | None" = None  # Alternative command for Shift+click
    tag: str = ""  # Optional tag for identification (e.g., solver dropdown)

    def get_label(self, shift_held: bool = False) -> str:
        """Get current label (static, dynamic, or shift-modified)."""
        if shift_held and self.shift_label:
            return self.shift_label
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

    def __init__(self, window_width: int, window_height: int,
                 key_binding_service: "KeyBindingService | None" = None):
        """Initialize toolbar."""
        self._window_width = window_width
        self._window_height = window_height
        self._key_binding_service = key_binding_service
        self._buttons: list[GUIButton] = []
        self._current_row = 0
        self._batch = pyglet.graphics.Batch()
        self._hover_button: GUIButton | None = None

        # Shapes for rendering
        self._shapes_dirty = True
        self._bg_rect: shapes.Rectangle | None = None
        self._button_rects: list[shapes.Rectangle | None] = []
        self._button_bevels: list[list[shapes.Line]] = []  # Bevel lines per button
        self._button_labels: list[pyglet.text.Label | None] = []

        # Shift key state (for dynamic labels and shift+click)
        self._shift_held: bool = False

        # Index where solver buttons start (for dynamic rebuild)
        self._solver_row_start: int = -1

        # Tooltip rendering
        self._tooltip_label: pyglet.text.Label | None = None
        self._tooltip_bg: shapes.Rectangle | None = None

        # Store window reference for rebuild (set by create_toolbar)
        self._window: "PygletAppWindow | None" = None

        # Solver dropdown state
        self._dropdown_open: bool = False
        self._dropdown_items: list[DropdownItem] = []
        self._dropdown_hover_idx: int = -1
        # Anchor: (x, y, width) of the Solver button — set when dropdown opens
        self._dropdown_anchor_x: int = 0
        self._dropdown_anchor_y: int = 0
        self._dropdown_anchor_w: int = 0

    def add_button(
            self,
            label: str,
            command: Command,
            enabled_fn: Callable[[], bool] | None = None,
            label_fn: Callable[[], str] | None = None,
            min_width: int = 0,
            tooltip: str | None = None,
            shift_label: str | None = None,
            shift_command: "Command | None" = None,
            tag: str = "",
    ) -> None:
        """Add a clickable button to current row."""
        # Auto-enrich tooltip with key binding
        if self._key_binding_service and command:
            key_label = self._key_binding_service.get_key_label(command)
            if key_label:
                tooltip = f"{tooltip} [{key_label}]" if tooltip else key_label

        self._buttons.append(GUIButton(
            label=label,
            command=command,
            row=self._current_row,
            enabled_fn=enabled_fn,
            label_fn=label_fn,
            min_width=min_width,
            tooltip=tooltip,
            shift_label=shift_label,
            shift_command=shift_command,
            tag=tag,
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
        # Close dropdown on resize to avoid stale positioning
        self._dropdown_open = False

    def _rebuild_shapes(self) -> None:
        """Rebuild all shapes."""
        self._batch = pyglet.graphics.Batch()
        self._button_rects.clear()
        self._button_bevels.clear()
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
                current_label = btn.get_label(self._shift_held)
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
            current_label = btn.get_label(self._shift_held)

            if btn.is_label:
                # Non-clickable label - no background rectangle or bevel
                self._button_rects.append(None)
                self._button_bevels.append([])
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

                # Add 3D bevel effect (highlight top/left, shadow bottom/right)
                highlight = BUTTON_HIGHLIGHT if enabled else BUTTON_HIGHLIGHT_DISABLED
                shadow = BUTTON_SHADOW if enabled else BUTTON_SHADOW_DISABLED
                x1, y1 = btn.x, btn.y
                x2, y2 = btn.x + btn.width, btn.y + BUTTON_HEIGHT
                bevels: list[shapes.Line] = []

                # Top highlight line
                line_top = shapes.Line(x1, y2, x2, y2, thickness=BEVEL_WIDTH,
                                       color=highlight[:3], batch=self._batch)
                line_top.opacity = highlight[3]
                bevels.append(line_top)

                # Left highlight line
                line_left = shapes.Line(x1, y1, x1, y2, thickness=BEVEL_WIDTH,
                                        color=highlight[:3], batch=self._batch)
                line_left.opacity = highlight[3]
                bevels.append(line_left)

                # Bottom shadow line
                line_bottom = shapes.Line(x1, y1, x2, y1, thickness=BEVEL_WIDTH,
                                          color=shadow[:3], batch=self._batch)
                line_bottom.opacity = shadow[3]
                bevels.append(line_bottom)

                # Right shadow line
                line_right = shapes.Line(x2, y1, x2, y2, thickness=BEVEL_WIDTH,
                                         color=shadow[:3], batch=self._batch)
                line_right.opacity = shadow[3]
                bevels.append(line_right)

                self._button_bevels.append(bevels)

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

        # Draw dropdown overlay (on top of toolbar, before tooltip)
        if self._dropdown_open:
            self._draw_dropdown()

        # Draw tooltip on top of everything
        self.draw_tooltip()

    # === Solver Dropdown ===

    def _open_dropdown(self) -> None:
        """Open the solver dropdown, populating items from SolverName.implemented()."""
        if self._window is None:
            return
        app = self._window.app
        current_name: str = app.slv.name

        self._dropdown_items = [
            DropdownItem(
                label=sn.display_name,
                solver_name=sn,
                is_current=(sn.display_name == current_name),
            )
            for sn in SolverName.implemented()
        ]

        # Find the Solver button to anchor the dropdown below it
        for btn in self._buttons:
            if btn.tag == _SOLVER_BUTTON_TAG:
                self._dropdown_anchor_x = btn.x
                self._dropdown_anchor_y = btn.y
                self._dropdown_anchor_w = btn.width
                break

        self._dropdown_open = True
        self._dropdown_hover_idx = -1

    def _close_dropdown(self) -> None:
        """Close the solver dropdown."""
        self._dropdown_open = False
        self._dropdown_items = []
        self._dropdown_hover_idx = -1

    def _dropdown_rect(self) -> tuple[int, int, int, int]:
        """Return (x, y, width, height) of the dropdown panel.

        The dropdown is positioned below the Solver button.
        In pyglet, y=0 is at the bottom, so "below" means lower y values.
        """
        num_items: int = len(self._dropdown_items)
        if num_items == 0:
            return (0, 0, 0, 0)

        # Calculate width: max of solver names or button width
        max_label_len: int = max(len(item.label) for item in self._dropdown_items)
        # Account for ">" prefix on current item
        text_width: int = (max_label_len + 2) * 9 + DROPDOWN_ITEM_PADDING * 2
        dd_width: int = max(text_width, self._dropdown_anchor_w)

        dd_height: int = num_items * DROPDOWN_ITEM_HEIGHT + 2  # 2px for border
        dd_x: int = self._dropdown_anchor_x
        # Position below the Solver button (button y is its bottom edge)
        dd_y: int = self._dropdown_anchor_y - dd_height

        return (dd_x, dd_y, dd_width, dd_height)

    def _dropdown_item_at(self, mx: int, my: int) -> int:
        """Return index of dropdown item at (mx, my), or -1 if none."""
        dd_x, dd_y, dd_width, dd_height = self._dropdown_rect()
        if not (dd_x <= mx <= dd_x + dd_width and dd_y <= my <= dd_y + dd_height):
            return -1

        # Items are drawn top-to-bottom (highest y = first item)
        # Use int() because pyglet2 passes mouse coords as float
        top_y: int = dd_y + dd_height - 1  # -1 for top border
        idx: int = int((top_y - my) // DROPDOWN_ITEM_HEIGHT)
        if 0 <= idx < len(self._dropdown_items):
            return idx
        return -1

    def _draw_dropdown(self) -> None:
        """Draw the solver dropdown panel (called from draw(), after batch)."""
        if not self._dropdown_items:
            return

        dd_x, dd_y, dd_width, dd_height = self._dropdown_rect()

        # Background
        bg = shapes.Rectangle(dd_x, dd_y, dd_width, dd_height,
                              color=DROPDOWN_BG_COLOR[:3])
        bg.opacity = DROPDOWN_BG_COLOR[3]
        bg.draw()

        # Border
        border_color = DROPDOWN_BORDER_COLOR[:3]
        border_opacity = DROPDOWN_BORDER_COLOR[3]
        lines: list[shapes.Line] = [
            shapes.Line(dd_x, dd_y, dd_x + dd_width, dd_y, color=border_color),
            shapes.Line(dd_x, dd_y + dd_height, dd_x + dd_width, dd_y + dd_height, color=border_color),
            shapes.Line(dd_x, dd_y, dd_x, dd_y + dd_height, color=border_color),
            shapes.Line(dd_x + dd_width, dd_y, dd_x + dd_width, dd_y + dd_height, color=border_color),
        ]
        for line in lines:
            line.opacity = border_opacity
            line.draw()

        # Draw items top-to-bottom
        top_y: int = dd_y + dd_height - 1  # -1 for border

        for idx, item in enumerate(self._dropdown_items):
            item_y: int = top_y - (idx + 1) * DROPDOWN_ITEM_HEIGHT

            # Item background (hover or current)
            if idx == self._dropdown_hover_idx:
                item_bg = shapes.Rectangle(dd_x + 1, item_y, dd_width - 2,
                                           DROPDOWN_ITEM_HEIGHT,
                                           color=DROPDOWN_ITEM_HOVER[:3])
                item_bg.opacity = DROPDOWN_ITEM_HOVER[3]
                item_bg.draw()
            elif item.is_current:
                item_bg = shapes.Rectangle(dd_x + 1, item_y, dd_width - 2,
                                           DROPDOWN_ITEM_HEIGHT,
                                           color=DROPDOWN_ITEM_CURRENT[:3])
                item_bg.opacity = DROPDOWN_ITEM_CURRENT[3]
                item_bg.draw()

            # Item text: prefix current solver with ">"
            prefix: str = "> " if item.is_current else "  "
            text_color = DROPDOWN_CURRENT_TEXT if item.is_current else DROPDOWN_TEXT_COLOR

            lbl = pyglet.text.Label(
                prefix + item.label,
                font_size=FONT_SIZE - 1,
                x=dd_x + DROPDOWN_ITEM_PADDING,
                y=item_y + DROPDOWN_ITEM_HEIGHT // 2,
                anchor_y='center',
                color=text_color,
            )
            lbl.draw()

    def handle_click(self, x: int, y: int) -> Command | None:
        """Handle mouse click. Returns command to execute or None.

        If Shift is held and button has shift_command, returns that instead.
        Returns a command or None. When dropdown is open and click is consumed,
        returns a SwitchToSolverCommand or None (but always consumes the event
        by returning a special sentinel — see _CLICK_CONSUMED).
        """
        # If dropdown is open, handle dropdown clicks first
        if self._dropdown_open:
            return self._handle_dropdown_click(x, y)

        # Check if solver button was clicked — toggle dropdown instead of cycling
        for btn in self._buttons:
            if btn.contains(x, y) and btn.is_enabled():
                if btn.tag == _SOLVER_BUTTON_TAG:
                    self._open_dropdown()
                    return None  # Consumed — no command to execute
                if self._shift_held and btn.shift_command:
                    return btn.shift_command
                if btn.command:
                    return btn.command
        return None

    def _handle_dropdown_click(self, x: int, y: int) -> Command | None:
        """Handle a click while dropdown is open.

        Returns command if solver selected, None otherwise.
        Always closes the dropdown.
        """
        from cube.presentation.gui.commands.concrete import SwitchToSolverCommand

        idx: int = self._dropdown_item_at(x, y)

        if idx >= 0:
            item: DropdownItem = self._dropdown_items[idx]
            self._close_dropdown()
            if not item.is_current:
                return SwitchToSolverCommand(item.solver_name)
            return None  # Already on this solver

        # Check if click is on the Solver button itself (toggle close)
        for btn in self._buttons:
            if btn.tag == _SOLVER_BUTTON_TAG and btn.contains(x, y):
                self._close_dropdown()
                return None

        # Click outside — close dropdown and consume the event
        self._close_dropdown()
        return None

    def handle_click_consumed(self, x: int, y: int) -> bool:
        """Check if a click at (x, y) would be consumed by the toolbar.

        Used by the window to know whether to pass the click to cube rotation.
        When the dropdown is open, ALL clicks are consumed (either selecting an
        item or closing the dropdown).
        """
        # When dropdown is open, consume all clicks (close on outside click)
        if self._dropdown_open:
            return True

        # Check toolbar buttons
        for btn in self._buttons:
            if btn.contains(x, y) and not btn.is_label:
                return True

        return False

    def handle_motion(self, x: int, y: int) -> None:
        """Handle mouse motion for hover effects."""
        # Update dropdown hover if open
        if self._dropdown_open:
            self._dropdown_hover_idx = self._dropdown_item_at(x, y)

        self._hover_button = None
        for btn in self._buttons:
            if btn.contains(x, y) and not btn.is_label:
                self._hover_button = btn
                break

    def handle_key_escape(self) -> bool:
        """Handle Escape key. Returns True if dropdown was closed (event consumed)."""
        if self._dropdown_open:
            self._close_dropdown()
            return True
        return False

    def set_shift_state(self, shift_held: bool) -> None:
        """Update Shift key state (called from window on key events)."""
        if self._shift_held != shift_held:
            self._shift_held = shift_held
            self._shapes_dirty = True  # Rebuild to update labels

    def rebuild_solver_buttons(self, app: "AbstractApp") -> None:
        """Rebuild Row 3 solver buttons based on current solver's supported steps.

        Called when:
        - Toolbar is first created
        - Solver is switched
        """
        from cube.presentation.gui.commands.concrete import (
            DiagnosticsCommand,
            SolveAllCommand,
            SolveAllNoAnimationCommand,
            SolveAndPlayCommand,
            SolveStepCommand,
            SolveStepNoAnimationCommand,
        )

        # Remove existing Row 3+ buttons (if any)
        if self._solver_row_start >= 0:
            self._buttons = self._buttons[:self._solver_row_start]

        # Mark start of solver buttons
        self._solver_row_start = len(self._buttons)

        # Ensure we're on Row 3 (0-indexed, so row 2)
        self._current_row = 2

        # Add "Diag" button (left of Solve)
        self.add_button(
            label="Diag",
            command=DiagnosticsCommand(),
            tooltip="Print current solver state to console",
            min_width=45,
        )

        # Add "Help" button
        from cube.presentation.gui.commands.help_command import HelpCommand
        self.add_button(
            label="Help",
            command=HelpCommand(),
            tooltip="Print keyboard and mouse help to console",
            min_width=45,
        )

        # Add "Solution" button (renamed from Solve) - uses current animation setting
        self.add_button(
            label="Solution",
            command=SolveAllCommand(),
            tooltip="Find solution (Shift: instant)",
            shift_label="Instant",
            shift_command=SolveAllNoAnimationCommand(),
            min_width=70,
        )

        # Add "Solve" button - solves and always plays with animation
        self.add_button(
            label="Solve",
            command=SolveAndPlayCommand(),
            tooltip="Solve and play solution with animation",
            min_width=55,
        )

        # Add step buttons for current solver
        solver = app.slv
        steps = solver.supported_steps()

        assert SolveStep.ALL not in steps, 'All solvers solve All'

        for step in steps:
            self.add_button(
                label=step.short_code,
                command=SolveStepCommand(step),
                tooltip=step.description,
                shift_label=f"{step.short_code}!",
                shift_command=SolveStepNoAnimationCommand(step),
            )

        # Rebuild Row 4 (animation/debug buttons) after solver buttons
        self._build_row4_buttons()

        self._shapes_dirty = True

    def _build_row4_buttons(self) -> None:
        """Build Row 4: Animation, Debug, and File Algorithm buttons.

        Called from rebuild_solver_buttons to ensure Row 4 is rebuilt
        when solver changes (since Row 3+ gets truncated).
        """
        from cube.presentation.gui.commands import Commands
        from cube.presentation.gui.commands.concrete import ExecuteFileAlgCommand

        if self._window is None:
            return  # Not initialized yet

        window = self._window
        app = window.app
        vs = app.vs
        op = app.op

        # === ROW 4: Animation, Debug, and File Algorithm Buttons ===
        self.new_row()

        # Animation controls
        self.add_button(
            "Anim",
            Commands.TOGGLE_ANIMATION,
            label_fn=lambda: "Anim:ON" if op.animation_enabled else "Anim:OFF",
            min_width=70,
        )

        # Speed controls
        self.add_label("Spd", label_fn=lambda: f"[{vs.get_speed_index}]", min_width=40)
        self.add_button("-", Commands.SPEED_DOWN)
        self.add_button("+", Commands.SPEED_UP)

        self.add_separator()

        # Debug and single-step
        self.add_button(
            "Debug",
            Commands.TOGGLE_DEBUG,
            label_fn=lambda: "Dbg:ON" if app.slv.is_debug_config_mode else "Dbg:OFF",
            min_width=65,
        )
        self.add_button(
            "SS",
            Commands.SINGLE_STEP_TOGGLE,
            label_fn=lambda: "SS:ON" if vs.single_step_mode else "SS:OFF",
            min_width=55,
        )

        # Next step (enabled when paused)
        self.add_button(
            "Next",
            Commands.PAUSE_TOGGLE,
            enabled_fn=lambda: vs.paused_on_single_step_mode is not None,
        )

        # Stop (enabled when animation running)
        self.add_button(
            "Stop",
            Commands.STOP_ANIMATION,
            enabled_fn=lambda: window.animation_running,
        )

        # File algorithm buttons (optional, based on config)
        if app.config.show_file_algs:
            self.add_separator()

            for slot in range(1, 6):
                self.add_button(
                    label=f"F{slot}",
                    command=ExecuteFileAlgCommand(slot=slot),
                    tooltip=f"Execute algorithm from f{slot}.txt (Shift: inverse)",
                    shift_label=f"F{slot}'",
                    shift_command=ExecuteFileAlgCommand(slot=slot, inverse=True),
                )

    def draw_exit_only(self) -> None:
        """Draw only a small exit button at top-right corner (for full mode).

        Returns the command if clicked via handle_exit_click().
        """
        # Small "X" button at top-right
        btn_size = 30
        margin = 10
        x = self._window_width - btn_size - margin
        y = self._window_height - btn_size - margin

        # Store position for click detection
        self._exit_btn_x = x
        self._exit_btn_y = y
        self._exit_btn_size = btn_size

        # Draw button background
        bg = shapes.Rectangle(x, y, btn_size, btn_size, color=(60, 60, 60))
        bg.opacity = 180
        bg.draw()

        # Draw "X" label
        label = pyglet.text.Label(
            "X",
            font_size=14,
            x=x + btn_size // 2,
            y=y + btn_size // 2,
            anchor_x='center',
            anchor_y='center',
            color=(255, 255, 255, 200),
        )
        label.draw()

    def handle_exit_click(self, x: int, y: int) -> "Command | None":
        """Handle click in full mode - only check exit button.

        Returns FULL_MODE_EXIT command if exit button was clicked, None otherwise.
        """
        from cube.presentation.gui.commands import Commands

        btn_x = getattr(self, '_exit_btn_x', 0)
        btn_y = getattr(self, '_exit_btn_y', 0)
        btn_size = getattr(self, '_exit_btn_size', 0)

        if (btn_x <= x <= btn_x + btn_size and
                btn_y <= y <= btn_y + btn_size):
            return Commands.FULL_MODE_EXIT
        return None

    def draw_tooltip(self) -> None:
        """Draw tooltip for hovered button (called after batch.draw)."""
        if not self._hover_button or not self._hover_button.tooltip:
            return

        text = self._hover_button.tooltip
        btn = self._hover_button

        # Calculate text width (approximate)
        text_width = len(text) * 7 + 10

        # Position tooltip below button, clamped to window edges
        tooltip_x = min(btn.x, self._window_width - text_width - 5)
        tooltip_x = max(tooltip_x, 5)
        tooltip_y = btn.y - 22

        # Ensure tooltip stays on screen vertically
        if tooltip_y < 10:
            tooltip_y = btn.y + BUTTON_HEIGHT + 5

        # Draw background
        self._tooltip_bg = shapes.Rectangle(
            tooltip_x, tooltip_y, text_width, 18,
            color=(50, 50, 50),
        )
        self._tooltip_bg.opacity = 230
        self._tooltip_bg.draw()

        # Draw text
        self._tooltip_label = pyglet.text.Label(
            text,
            font_size=10,
            x=tooltip_x + 5,
            y=tooltip_y + 9,
            anchor_y='center',
            color=(255, 255, 200, 255),
        )
        self._tooltip_label.draw()


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
    from cube.presentation.gui.key_bindings import KEY_BINDINGS_NORMAL, KeyBindingService

    key_binding_service = KeyBindingService(KEY_BINDINGS_NORMAL)
    toolbar = GUIToolbar(window.width, window.height, key_binding_service)
    app = window.app
    vs = app.vs

    # === ROW 1: Size, Scramble, Solve/Reset ===

    # Cube size display and controls
    toolbar.add_label("Size", label_fn=lambda: f"{app.cube.size}x{app.cube.size}", min_width=50)
    toolbar.add_button("2", Commands.SIZE_2)
    toolbar.add_button("3", Commands.SIZE_3)
    toolbar.add_button("4", Commands.SIZE_4)
    toolbar.add_button("5", Commands.SIZE_5)
    toolbar.add_button("-", Commands.SIZE_DEC)
    toolbar.add_button("+", Commands.SIZE_INC)

    toolbar.add_separator()

    # Scramble buttons F, 0-9
    toolbar.add_button("F", Commands.SCRAMBLE_F)
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

    # Reset buttons
    toolbar.add_button("Reset", Commands.RESET_CUBE)
    toolbar.add_button(
        "View",
        Commands.VIEW_RESET,
        tooltip="Reset view to default camera position",
    )

    # === ROW 2: Texture, Shadow, Solver, Quit ===
    toolbar.new_row()

    # Texture controls
    toolbar.add_label("Tex")
    toolbar.add_button("<", Commands.TEXTURE_SET_PREV)
    toolbar.add_button(">", Commands.TEXTURE_SET_NEXT)
    toolbar.add_button(
        "On",
        Commands.TEXTURE_TOGGLE,
        label_fn=lambda: "ON" if window._modern_viewer.textures_enabled else "OFF",
        min_width=40,
    )

    toolbar.add_separator()

    # Shadow toggle (for L, D, B faces)
    toolbar.add_button(
        "Shadow",
        Commands.SHADOW_TOGGLE_ALL,
        label_fn=lambda: "Shd:ON" if vs.any_shadow_on else "Shd:OFF",
        min_width=65,
    )

    toolbar.add_separator()

    # Solver — tagged for dropdown toggling (command is unused, kept for key binding tooltip)
    toolbar.add_button(
        "Solver",
        Commands.SWITCH_SOLVER,
        label_fn=lambda: f"Slv:{app.slv.name[:6]}",
        min_width=75,
        tooltip="Click to choose solver",
        tag=_SOLVER_BUTTON_TAG,
    )

    toolbar.add_separator()

    toolbar.add_button(
        "Full",
        Commands.FULL_MODE_TOGGLE,
        tooltip="Toggle full mode - hide toolbar",
    )
    toolbar.add_button("Quit", Commands.QUIT)

    # === ROW 3: Solver Step Buttons + ROW 4: Animation/Debug ===
    # Store window reference for _build_row4_buttons (called by rebuild_solver_buttons)
    toolbar._window = window
    toolbar.new_row()
    # rebuild_solver_buttons also builds Row 4 via _build_row4_buttons
    toolbar.rebuild_solver_buttons(app)

    return toolbar
