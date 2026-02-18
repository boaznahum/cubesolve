"""
Text popup overlay for displaying help and other multi-line text.

Renders a centered, semi-transparent modal panel on top of the 3D view.
While open, it intercepts all keyboard/mouse events (modal behavior).
"""
from __future__ import annotations

import pyglet
from pyglet import gl, shapes


# Visual constants
OVERLAY_COLOR = (0, 0, 0, 180)  # Dark semi-transparent full-window overlay
PANEL_BG_COLOR = (30, 35, 50, 240)  # Dark blue-gray panel
PANEL_BORDER_COLOR = (80, 100, 140, 255)  # Lighter border
PANEL_MARGIN_RATIO = 0.10  # 10% margin on each side -> 80% width/height

TITLE_FONT_SIZE = 16
TITLE_COLOR = (255, 255, 255, 255)
TITLE_TOP_PADDING = 10  # Space above title

CONTENT_FONT_NAME = "Consolas"  # Monospace font for aligned columns
LINE_FONT_SIZE = 11
LINE_HEIGHT = 18  # Pixels per line
LINE_LEFT_PADDING = 20
CONTENT_TOP_PADDING = 50  # Space from panel top to first content line
CHAR_WIDTH_APPROX = 8.0  # Approximate character width for Consolas at size 11

# Section header style
SECTION_COLOR = (255, 215, 80, 255)  # Gold/yellow for section headers
SECTION_FONT_SIZE = 12

# Default line color
DEFAULT_LINE_COLOR = (220, 220, 220, 255)  # Light white-gray
KEY_COLOR = (100, 220, 255, 255)  # Cyan for key bindings

# OK button style (matches toolbar buttons)
OK_BUTTON_WIDTH = 80
OK_BUTTON_HEIGHT = 30
OK_BUTTON_BG = (70, 130, 180, 255)
OK_BUTTON_BG_HOVER = (100, 160, 210, 255)
OK_BUTTON_TEXT_COLOR = (255, 255, 255, 255)
OK_BUTTON_HIGHLIGHT = (130, 180, 220, 255)
OK_BUTTON_SHADOW = (30, 70, 110, 255)
OK_BUTTON_BOTTOM_MARGIN = 15  # Space from panel bottom to button

# Scrollbar
SCROLLBAR_WIDTH = 6
SCROLLBAR_COLOR = (120, 140, 180, 180)
SCROLLBAR_BG_COLOR = (50, 55, 70, 100)
SCROLLBAR_RIGHT_MARGIN = 8


class TextPopup:
    """Modal text popup overlay with scrolling support.

    Shows a centered panel with title, scrollable text content, and an OK button.
    While visible, all keyboard and mouse events are intercepted.
    """

    def __init__(self, window_width: int, window_height: int) -> None:
        self._window_width: int = window_width
        self._window_height: int = window_height

        # Content (originals as provided by caller)
        self._title: str = ""
        self._orig_lines: list[str] = []
        self._orig_colors: list[tuple[int, int, int, int]] = []
        self._visible: bool = False

        # Wrapped lines (recomputed on geometry change)
        self._lines: list[str] = []
        self._line_colors: list[tuple[int, int, int, int]] = []

        # Scrolling
        self._scroll_offset: int = 0  # Lines scrolled from top
        self._max_visible_lines: int = 0  # Computed from panel height

        # OK button hover state
        self._ok_hover: bool = False

        # Panel geometry (computed)
        self._panel_x: int = 0
        self._panel_y: int = 0
        self._panel_w: int = 0
        self._panel_h: int = 0
        self._ok_x: int = 0
        self._ok_y: int = 0

    @property
    def is_visible(self) -> bool:
        """Whether the popup is currently visible."""
        return self._visible

    def show(self, title: str, lines: list[str],
             line_colors: list[tuple[int, int, int, int]] | None = None) -> None:
        """Open the popup with content.

        Args:
            title: Title text displayed at top of panel
            lines: Text lines to display
            line_colors: Optional per-line RGBA color tuples. If shorter than
                         lines, remaining lines use DEFAULT_LINE_COLOR.
        """
        self._title = title
        self._orig_lines = lines
        self._orig_colors = list(line_colors) if line_colors else []
        self._scroll_offset = 0
        self._visible = True
        self._recompute_geometry()

    def hide(self) -> None:
        """Close the popup."""
        self._visible = False

    def update_window_size(self, width: int, height: int) -> None:
        """Called on window resize."""
        self._window_width = width
        self._window_height = height
        if self._visible:
            self._recompute_geometry()

    def _recompute_geometry(self) -> None:
        """Recompute panel position, visible line count, and wrap lines."""
        margin_x = int(self._window_width * PANEL_MARGIN_RATIO)
        margin_y = int(self._window_height * PANEL_MARGIN_RATIO)
        self._panel_w = self._window_width - 2 * margin_x
        self._panel_h = self._window_height - 2 * margin_y
        self._panel_x = margin_x
        self._panel_y = margin_y

        # Available height for content (between title area and OK button)
        content_h = self._panel_h - CONTENT_TOP_PADDING - OK_BUTTON_HEIGHT - OK_BUTTON_BOTTOM_MARGIN * 2
        self._max_visible_lines = max(1, content_h // LINE_HEIGHT)

        # OK button centered at bottom of panel
        self._ok_x = self._panel_x + (self._panel_w - OK_BUTTON_WIDTH) // 2
        self._ok_y = self._panel_y + OK_BUTTON_BOTTOM_MARGIN

        # Wrap lines to fit panel width
        self._wrap_lines()

        # Clamp scroll
        self._clamp_scroll()

    def _wrap_lines(self) -> None:
        """Wrap original lines to fit within the content area width."""
        # Calculate max characters per line from available pixel width
        content_pixel_width = (self._panel_w - LINE_LEFT_PADDING
                               - SCROLLBAR_WIDTH - SCROLLBAR_RIGHT_MARGIN * 2)
        max_chars = max(20, int(content_pixel_width / CHAR_WIDTH_APPROX))

        self._lines = []
        self._line_colors = []

        for i, orig_line in enumerate(self._orig_lines):
            color = (self._orig_colors[i]
                     if i < len(self._orig_colors)
                     else DEFAULT_LINE_COLOR)

            if len(orig_line) <= max_chars:
                self._lines.append(orig_line)
                self._line_colors.append(color)
            else:
                # Measure leading whitespace for continuation indent
                stripped = orig_line.lstrip()
                indent = len(orig_line) - len(stripped)
                cont_indent = " " * (indent + 4)  # Extra indent for wrapped part

                # First chunk gets the full line up to max_chars
                remaining = orig_line
                first = True
                while remaining:
                    if first:
                        chunk = remaining[:max_chars]
                        remaining = remaining[max_chars:]
                        first = False
                    else:
                        # Continuation lines get extra indent
                        avail = max_chars - len(cont_indent)
                        chunk = cont_indent + remaining[:avail]
                        remaining = remaining[avail:]

                    self._lines.append(chunk)
                    self._line_colors.append(color)

    def _clamp_scroll(self) -> None:
        """Clamp scroll offset to valid range."""
        max_scroll = max(0, len(self._lines) - self._max_visible_lines)
        self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))

    def _get_line_color(self, index: int) -> tuple[int, int, int, int]:
        """Get color for a specific line index."""
        if index < len(self._line_colors):
            return self._line_colors[index]
        return DEFAULT_LINE_COLOR

    def draw(self) -> None:
        """Render the popup overlay. Call only when visible."""
        if not self._visible:
            return

        self._recompute_geometry()

        # --- Full-window dark overlay ---
        overlay = shapes.Rectangle(
            0, 0, self._window_width, self._window_height,
            color=OVERLAY_COLOR[:3],
        )
        overlay.opacity = OVERLAY_COLOR[3]
        overlay.draw()

        # --- Panel background ---
        panel = shapes.Rectangle(
            self._panel_x, self._panel_y, self._panel_w, self._panel_h,
            color=PANEL_BG_COLOR[:3],
        )
        panel.opacity = PANEL_BG_COLOR[3]
        panel.draw()

        # --- Panel border (4 lines) ---
        bx1, by1 = self._panel_x, self._panel_y
        bx2, by2 = bx1 + self._panel_w, by1 + self._panel_h
        border_color = PANEL_BORDER_COLOR[:3]
        border_opacity = PANEL_BORDER_COLOR[3]
        for x1, y1, x2, y2 in [
            (bx1, by2, bx2, by2),  # top
            (bx1, by1, bx2, by1),  # bottom
            (bx1, by1, bx1, by2),  # left
            (bx2, by1, bx2, by2),  # right
        ]:
            line = shapes.Line(x1, y1, x2, y2, thickness=2,
                               color=border_color)
            line.opacity = border_opacity
            line.draw()

        # --- Title ---
        title_y = by2 - TITLE_TOP_PADDING - TITLE_FONT_SIZE
        title_label = pyglet.text.Label(
            self._title,
            font_size=TITLE_FONT_SIZE,
            x=self._panel_x + self._panel_w // 2,
            y=title_y,
            anchor_x='center',
            anchor_y='top',
            color=TITLE_COLOR,
            weight='bold',
        )
        title_label.draw()

        # --- Scrollable content with scissor clipping ---
        content_top_y = by2 - CONTENT_TOP_PADDING
        content_bottom_y = self._ok_y + OK_BUTTON_HEIGHT + OK_BUTTON_BOTTOM_MARGIN
        content_height = content_top_y - content_bottom_y

        # Enable scissor test to clip content to panel area
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(
            self._panel_x + LINE_LEFT_PADDING,
            content_bottom_y,
            self._panel_w - LINE_LEFT_PADDING - SCROLLBAR_WIDTH - SCROLLBAR_RIGHT_MARGIN * 2,
            content_height,
        )

        # Draw visible lines
        end_idx = min(self._scroll_offset + self._max_visible_lines, len(self._lines))
        for i in range(self._scroll_offset, end_idx):
            line_y_pos = content_top_y - (i - self._scroll_offset) * LINE_HEIGHT - LINE_HEIGHT
            color = self._get_line_color(i)
            text = self._lines[i]

            label = pyglet.text.Label(
                text,
                font_name=CONTENT_FONT_NAME,
                font_size=LINE_FONT_SIZE,
                x=self._panel_x + LINE_LEFT_PADDING,
                y=line_y_pos,
                anchor_y='bottom',
                color=color,
            )
            label.draw()

        gl.glDisable(gl.GL_SCISSOR_TEST)

        # --- Scrollbar ---
        if len(self._lines) > self._max_visible_lines:
            self._draw_scrollbar(content_top_y, content_bottom_y)

        # --- OK button ---
        self._draw_ok_button()

    def _draw_scrollbar(self, content_top: int, content_bottom: int) -> None:
        """Draw a thin scrollbar indicator on the right side of the panel."""
        track_height = content_top - content_bottom
        track_x = self._panel_x + self._panel_w - SCROLLBAR_WIDTH - SCROLLBAR_RIGHT_MARGIN

        # Track background
        track_bg = shapes.Rectangle(
            track_x, content_bottom, SCROLLBAR_WIDTH, track_height,
            color=SCROLLBAR_BG_COLOR[:3],
        )
        track_bg.opacity = SCROLLBAR_BG_COLOR[3]
        track_bg.draw()

        # Thumb
        total_lines = len(self._lines)
        visible_ratio = self._max_visible_lines / total_lines
        thumb_height = max(20, int(track_height * visible_ratio))

        scroll_ratio = self._scroll_offset / max(1, total_lines - self._max_visible_lines)
        thumb_y = content_top - thumb_height - int((track_height - thumb_height) * scroll_ratio)

        thumb = shapes.Rectangle(
            track_x, thumb_y, SCROLLBAR_WIDTH, thumb_height,
            color=SCROLLBAR_COLOR[:3],
        )
        thumb.opacity = SCROLLBAR_COLOR[3]
        thumb.draw()

    def _draw_ok_button(self) -> None:
        """Draw the OK button at the bottom of the panel."""
        bg_color = OK_BUTTON_BG_HOVER if self._ok_hover else OK_BUTTON_BG

        # Button background
        rect = shapes.Rectangle(
            self._ok_x, self._ok_y, OK_BUTTON_WIDTH, OK_BUTTON_HEIGHT,
            color=bg_color[:3],
        )
        rect.opacity = bg_color[3]
        rect.draw()

        # Bevel highlight (top + left)
        hl = OK_BUTTON_HIGHLIGHT
        for x1, y1, x2, y2 in [
            (self._ok_x, self._ok_y + OK_BUTTON_HEIGHT,
             self._ok_x + OK_BUTTON_WIDTH, self._ok_y + OK_BUTTON_HEIGHT),
            (self._ok_x, self._ok_y,
             self._ok_x, self._ok_y + OK_BUTTON_HEIGHT),
        ]:
            line = shapes.Line(x1, y1, x2, y2, thickness=2, color=hl[:3])
            line.opacity = hl[3]
            line.draw()

        # Bevel shadow (bottom + right)
        sh = OK_BUTTON_SHADOW
        for x1, y1, x2, y2 in [
            (self._ok_x, self._ok_y,
             self._ok_x + OK_BUTTON_WIDTH, self._ok_y),
            (self._ok_x + OK_BUTTON_WIDTH, self._ok_y,
             self._ok_x + OK_BUTTON_WIDTH, self._ok_y + OK_BUTTON_HEIGHT),
        ]:
            line = shapes.Line(x1, y1, x2, y2, thickness=2, color=sh[:3])
            line.opacity = sh[3]
            line.draw()

        # Button label
        label = pyglet.text.Label(
            "OK",
            font_size=13,
            x=self._ok_x + OK_BUTTON_WIDTH // 2,
            y=self._ok_y + OK_BUTTON_HEIGHT // 2,
            anchor_x='center',
            anchor_y='center',
            color=OK_BUTTON_TEXT_COLOR,
            weight='bold',
        )
        label.draw()

    # === Event handlers (return True if consumed) ===

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle key press. Returns True if consumed (popup is visible)."""
        if not self._visible:
            return False

        from pyglet.window import key

        if symbol == key.ESCAPE or symbol == key.RETURN or symbol == key.ENTER:
            self.hide()
        elif symbol == key.UP:
            self._scroll_offset = max(0, self._scroll_offset - 1)
        elif symbol == key.DOWN:
            max_scroll = max(0, len(self._lines) - self._max_visible_lines)
            self._scroll_offset = min(max_scroll, self._scroll_offset + 1)
        elif symbol == key.PAGEUP:
            self._scroll_offset = max(0, self._scroll_offset - self._max_visible_lines)
        elif symbol == key.PAGEDOWN:
            max_scroll = max(0, len(self._lines) - self._max_visible_lines)
            self._scroll_offset = min(max_scroll,
                                      self._scroll_offset + self._max_visible_lines)
        elif symbol == key.HOME:
            self._scroll_offset = 0
        elif symbol == key.END:
            self._scroll_offset = max(0, len(self._lines) - self._max_visible_lines)

        return True  # Always consume when visible

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool:
        """Handle mouse press. Returns True if consumed."""
        if not self._visible:
            return False

        # Check OK button click
        if (self._ok_x <= x <= self._ok_x + OK_BUTTON_WIDTH and
                self._ok_y <= y <= self._ok_y + OK_BUTTON_HEIGHT):
            self.hide()

        return True  # Always consume when visible

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float) -> bool:
        """Handle mouse scroll. Returns True if consumed."""
        if not self._visible:
            return False

        lines_to_scroll = 3  # Scroll 3 lines per notch
        self._scroll_offset -= int(scroll_y * lines_to_scroll)
        self._clamp_scroll()
        return True

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool:
        """Handle mouse motion for OK button hover. Returns True if consumed."""
        if not self._visible:
            return False

        self._ok_hover = (self._ok_x <= x <= self._ok_x + OK_BUTTON_WIDTH and
                          self._ok_y <= y <= self._ok_y + OK_BUTTON_HEIGHT)
        return True
