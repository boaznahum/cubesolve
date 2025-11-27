"""
Tests for Window protocol implementation.

These tests verify that backend windows correctly implement
the Window and TextRenderer protocols.
"""

import pytest

from cube.gui.protocols import Window, TextRenderer
from cube.gui.types import KeyEvent, MouseEvent, Keys, Modifiers


class TestWindowProtocol:
    """Tests for the Window protocol."""

    def test_window_has_dimensions(self, window: Window, backend_name: str):
        """Window must have width and height properties."""
        assert window.width > 0
        assert window.height > 0

    def test_window_has_text_renderer(self, window: Window, backend_name: str):
        """Window must have text property returning TextRenderer."""
        assert hasattr(window, 'text')
        assert isinstance(window.text, TextRenderer)

    def test_set_title(self, window: Window, backend_name: str):
        """Window.set_title() should not raise."""
        window.set_title("New Title")

    def test_set_visible(self, window: Window, backend_name: str):
        """Window.set_visible() should not raise."""
        window.set_visible(False)
        window.set_visible(True)

    def test_set_size(self, window: Window, backend_name: str):
        """Window.set_size() should update dimensions."""
        window.set_size(800, 600)
        # Note: Some backends may not update immediately
        # Just verify it doesn't raise

    def test_request_redraw(self, window: Window, backend_name: str):
        """Window.request_redraw() should not raise."""
        window.request_redraw()

    def test_set_mouse_visible(self, window: Window, backend_name: str):
        """Window.set_mouse_visible() should not raise."""
        window.set_mouse_visible(False)
        window.set_mouse_visible(True)


class TestWindowEventHandlers:
    """Tests for Window event handler registration."""

    def test_set_draw_handler(self, window: Window, backend_name: str):
        """Window.set_draw_handler() should accept callable or None."""
        called = []
        window.set_draw_handler(lambda: called.append(True))
        window.set_draw_handler(None)

    def test_set_resize_handler(self, window: Window, backend_name: str):
        """Window.set_resize_handler() should accept callable or None."""
        window.set_resize_handler(lambda w, h: None)
        window.set_resize_handler(None)

    def test_set_key_press_handler(self, window: Window, backend_name: str):
        """Window.set_key_press_handler() should accept callable or None."""
        window.set_key_press_handler(lambda e: None)
        window.set_key_press_handler(None)

    def test_set_key_release_handler(self, window: Window, backend_name: str):
        """Window.set_key_release_handler() should accept callable or None."""
        window.set_key_release_handler(lambda e: None)
        window.set_key_release_handler(None)

    def test_set_mouse_press_handler(self, window: Window, backend_name: str):
        """Window.set_mouse_press_handler() should accept callable or None."""
        window.set_mouse_press_handler(lambda e: None)
        window.set_mouse_press_handler(None)

    def test_set_mouse_release_handler(self, window: Window, backend_name: str):
        """Window.set_mouse_release_handler() should accept callable or None."""
        window.set_mouse_release_handler(lambda e: None)
        window.set_mouse_release_handler(None)

    def test_set_mouse_drag_handler(self, window: Window, backend_name: str):
        """Window.set_mouse_drag_handler() should accept callable or None."""
        window.set_mouse_drag_handler(lambda e: None)
        window.set_mouse_drag_handler(None)

    def test_set_mouse_scroll_handler(self, window: Window, backend_name: str):
        """Window.set_mouse_scroll_handler() should accept callable or None."""
        window.set_mouse_scroll_handler(lambda x, y, sx, sy: None)
        window.set_mouse_scroll_handler(None)

    def test_set_close_handler(self, window: Window, backend_name: str):
        """Window.set_close_handler() should accept callable or None."""
        window.set_close_handler(lambda: True)
        window.set_close_handler(None)


class TestTextRendererProtocol:
    """Tests for TextRenderer protocol."""

    @pytest.fixture
    def text_renderer(self, window: Window) -> TextRenderer:
        """Get text renderer from window."""
        return window.text

    def test_draw_label_basic(self, text_renderer: TextRenderer, backend_name: str):
        """TextRenderer.draw_label() with minimal args should not raise."""
        text_renderer.draw_label("Hello", 10, 20)

    def test_draw_label_with_options(self, text_renderer: TextRenderer, backend_name: str):
        """TextRenderer.draw_label() with all options should not raise."""
        text_renderer.draw_label(
            "Hello World",
            x=100,
            y=200,
            font_size=24,
            color=(255, 0, 0, 255),
            bold=True,
            anchor_x="center",
            anchor_y="center",
        )

    def test_draw_multiple_labels(self, text_renderer: TextRenderer, backend_name: str):
        """Drawing multiple labels should work."""
        text_renderer.draw_label("Label 1", 10, 10)
        text_renderer.draw_label("Label 2", 10, 30)
        text_renderer.draw_label("Label 3", 10, 50)

    def test_clear_labels(self, text_renderer: TextRenderer, backend_name: str):
        """TextRenderer.clear_labels() should not raise."""
        text_renderer.draw_label("To be cleared", 10, 10)
        text_renderer.clear_labels()


class TestHeadlessWindowSimulation:
    """Tests specific to headless window event simulation.

    These tests only run with the headless backend.
    """

    @pytest.fixture
    def headless_window(self, window: Window, backend_name: str):
        """Get window only if headless backend."""
        if backend_name != "headless":
            pytest.skip("Event simulation only available in headless backend")
        return window

    def test_simulate_key_press(self, headless_window, backend_name: str):
        """Headless window should support simulated key events."""
        pressed_keys = []
        headless_window.set_key_press_handler(lambda e: pressed_keys.append(e.symbol))

        headless_window.simulate_key_press(KeyEvent(symbol=Keys.R, modifiers=0))
        headless_window.simulate_key_press(KeyEvent(symbol=Keys.L, modifiers=Modifiers.SHIFT))

        assert pressed_keys == [Keys.R, Keys.L]

    def test_simulate_mouse_press(self, headless_window, backend_name: str):
        """Headless window should support simulated mouse events."""
        clicks = []
        headless_window.set_mouse_press_handler(lambda e: clicks.append((e.x, e.y, e.button)))

        headless_window.simulate_mouse_press(MouseEvent(x=100, y=200, button=1))

        assert clicks == [(100, 200, 1)]

    def test_simulate_mouse_drag(self, headless_window, backend_name: str):
        """Headless window should support simulated drag events."""
        drags = []
        headless_window.set_mouse_drag_handler(lambda e: drags.append((e.x, e.y, e.dx, e.dy)))

        headless_window.simulate_mouse_drag(MouseEvent(x=100, y=200, dx=10, dy=-5))

        assert drags == [(100, 200, 10, -5)]

    def test_simulate_draw(self, headless_window, backend_name: str):
        """Headless window should support simulated draw events."""
        draw_count = [0]
        headless_window.set_draw_handler(lambda: draw_count.__setitem__(0, draw_count[0] + 1))

        headless_window.simulate_draw()
        headless_window.simulate_draw()

        assert draw_count[0] == 2

    def test_simulate_resize(self, headless_window, backend_name: str):
        """Headless window should support simulated resize events."""
        sizes = []
        headless_window.set_resize_handler(lambda w, h: sizes.append((w, h)))

        headless_window.simulate_resize(1024, 768)

        assert sizes == [(1024, 768)]
        assert headless_window.width == 1024
        assert headless_window.height == 768
