"""
Tests for Renderer protocol implementation.

These tests verify that backend renderers correctly implement
the Renderer, ShapeRenderer, DisplayListManager, and ViewStateManager protocols.
"""

import pytest
import numpy as np

from cube.gui.protocols import Renderer, ShapeRenderer, DisplayListManager, ViewStateManager
from cube.gui.types import make_point3d


class TestRendererProtocol:
    """Tests for the main Renderer protocol."""

    def test_renderer_has_required_properties(self, renderer: Renderer, backend_name: str):
        """Renderer must have shapes, display_lists, and view properties."""
        assert hasattr(renderer, 'shapes')
        assert hasattr(renderer, 'display_lists')
        assert hasattr(renderer, 'view')

    def test_renderer_properties_return_correct_types(self, renderer: Renderer, backend_name: str):
        """Renderer properties must return protocol-compatible objects."""
        assert isinstance(renderer.shapes, ShapeRenderer)
        assert isinstance(renderer.display_lists, DisplayListManager)
        assert isinstance(renderer.view, ViewStateManager)

    def test_renderer_clear(self, renderer: Renderer, backend_name: str):
        """Renderer.clear() should not raise."""
        renderer.clear()
        renderer.clear((255, 0, 0, 255))  # With color

    def test_renderer_frame_lifecycle(self, renderer: Renderer, backend_name: str):
        """Renderer frame methods should work in sequence."""
        renderer.begin_frame()
        renderer.clear()
        renderer.end_frame()

    def test_renderer_flush(self, renderer: Renderer, backend_name: str):
        """Renderer.flush() should not raise."""
        renderer.flush()


class TestShapeRendererProtocol:
    """Tests for ShapeRenderer protocol."""

    @pytest.fixture
    def shapes(self, renderer: Renderer) -> ShapeRenderer:
        """Get shape renderer from renderer."""
        return renderer.shapes

    @pytest.fixture
    def quad_vertices(self) -> list:
        """Create quad vertices for testing."""
        return [
            make_point3d(-1, -1, 0),
            make_point3d(1, -1, 0),
            make_point3d(1, 1, 0),
            make_point3d(-1, 1, 0),
        ]

    @pytest.fixture
    def triangle_vertices(self) -> list:
        """Create triangle vertices for testing."""
        return [
            make_point3d(0, 1, 0),
            make_point3d(-1, -1, 0),
            make_point3d(1, -1, 0),
        ]

    def test_quad(self, shapes: ShapeRenderer, quad_vertices: list, backend_name: str):
        """ShapeRenderer.quad() should not raise."""
        shapes.quad(quad_vertices, (255, 0, 0))

    def test_quad_with_border(self, shapes: ShapeRenderer, quad_vertices: list, backend_name: str):
        """ShapeRenderer.quad_with_border() should not raise."""
        shapes.quad_with_border(
            quad_vertices,
            face_color=(255, 0, 0),
            line_width=2.0,
            line_color=(255, 255, 255),
        )

    def test_triangle(self, shapes: ShapeRenderer, triangle_vertices: list, backend_name: str):
        """ShapeRenderer.triangle() should not raise."""
        shapes.triangle(triangle_vertices, (0, 255, 0))

    def test_line(self, shapes: ShapeRenderer, backend_name: str):
        """ShapeRenderer.line() should not raise."""
        p1 = make_point3d(0, 0, 0)
        p2 = make_point3d(1, 1, 1)
        shapes.line(p1, p2, width=1.0, color=(255, 255, 255))

    def test_sphere(self, shapes: ShapeRenderer, backend_name: str):
        """ShapeRenderer.sphere() should not raise."""
        center = make_point3d(0, 0, 0)
        shapes.sphere(center, radius=0.5, color=(0, 0, 255))

    def test_cylinder(self, shapes: ShapeRenderer, backend_name: str):
        """ShapeRenderer.cylinder() should not raise."""
        p1 = make_point3d(0, 0, 0)
        p2 = make_point3d(0, 1, 0)
        shapes.cylinder(p1, p2, radius1=0.5, radius2=0.5, color=(255, 255, 0))


class TestDisplayListManagerProtocol:
    """Tests for DisplayListManager protocol."""

    @pytest.fixture
    def display_lists(self, renderer: Renderer) -> DisplayListManager:
        """Get display list manager from renderer."""
        return renderer.display_lists

    def test_create_list(self, display_lists: DisplayListManager, backend_name: str):
        """DisplayListManager.create_list() should return a handle."""
        list_id = display_lists.create_list()
        assert list_id is not None

    def test_compile_and_call_list(self, display_lists: DisplayListManager, renderer: Renderer, backend_name: str):
        """Display list compilation and execution should work."""
        list_id = display_lists.create_list()

        display_lists.begin_compile(list_id)
        renderer.shapes.quad(
            [make_point3d(-1, -1, 0), make_point3d(1, -1, 0),
             make_point3d(1, 1, 0), make_point3d(-1, 1, 0)],
            (255, 0, 0)
        )
        display_lists.end_compile()

        # Should not raise
        display_lists.call_list(list_id)

    def test_call_lists(self, display_lists: DisplayListManager, backend_name: str):
        """DisplayListManager.call_lists() should handle multiple lists."""
        list1 = display_lists.create_list()
        list2 = display_lists.create_list()

        display_lists.call_lists([list1, list2])

    def test_delete_list(self, display_lists: DisplayListManager, backend_name: str):
        """DisplayListManager.delete_list() should not raise."""
        list_id = display_lists.create_list()
        display_lists.delete_list(list_id)

    def test_delete_lists(self, display_lists: DisplayListManager, backend_name: str):
        """DisplayListManager.delete_lists() should handle multiple lists."""
        list1 = display_lists.create_list()
        list2 = display_lists.create_list()
        display_lists.delete_lists([list1, list2])


class TestViewStateManagerProtocol:
    """Tests for ViewStateManager protocol."""

    @pytest.fixture
    def view(self, renderer: Renderer) -> ViewStateManager:
        """Get view state manager from renderer."""
        return renderer.view

    def test_set_projection(self, view: ViewStateManager, backend_name: str):
        """ViewStateManager.set_projection() should not raise."""
        view.set_projection(800, 600, fov_y=45.0)

    def test_push_pop_matrix(self, view: ViewStateManager, backend_name: str):
        """Matrix stack push/pop should work."""
        view.push_matrix()
        view.pop_matrix()

    def test_nested_push_pop(self, view: ViewStateManager, backend_name: str):
        """Nested matrix push/pop should work."""
        view.push_matrix()
        view.push_matrix()
        view.pop_matrix()
        view.pop_matrix()

    def test_load_identity(self, view: ViewStateManager, backend_name: str):
        """ViewStateManager.load_identity() should not raise."""
        view.load_identity()

    def test_translate(self, view: ViewStateManager, backend_name: str):
        """ViewStateManager.translate() should not raise."""
        view.translate(1.0, 2.0, 3.0)

    def test_rotate(self, view: ViewStateManager, backend_name: str):
        """ViewStateManager.rotate() should not raise."""
        view.rotate(45.0, 0.0, 1.0, 0.0)  # 45 degrees around Y axis

    def test_scale(self, view: ViewStateManager, backend_name: str):
        """ViewStateManager.scale() should not raise."""
        view.scale(2.0, 2.0, 2.0)

    def test_multiply_matrix(self, view: ViewStateManager, backend_name: str):
        """ViewStateManager.multiply_matrix() should not raise."""
        identity = np.eye(4, dtype=np.float32)
        view.multiply_matrix(identity)

    def test_look_at(self, view: ViewStateManager, backend_name: str):
        """ViewStateManager.look_at() should not raise."""
        view.look_at(
            eye_x=0, eye_y=0, eye_z=5,
            center_x=0, center_y=0, center_z=0,
            up_x=0, up_y=1, up_z=0,
        )

    def test_transformation_sequence(self, view: ViewStateManager, backend_name: str):
        """A typical transformation sequence should work."""
        view.push_matrix()
        view.load_identity()
        view.translate(0, 0, -5)
        view.rotate(30, 1, 0, 0)
        view.rotate(45, 0, 1, 0)
        view.scale(1.5, 1.5, 1.5)
        view.pop_matrix()
