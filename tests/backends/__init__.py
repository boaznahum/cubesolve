"""
Backend protocol tests.

Tests in this package verify that GUI backend implementations
correctly implement the protocol interfaces.

Tests are parameterized by backend, allowing the same tests to run
against different implementations (headless, pyglet, tkinter, etc.).

Usage:
    # Run all backend tests
    pytest tests/backends/

    # Run only headless backend tests
    pytest tests/backends/ -k headless

    # Run only pyglet backend tests (requires display)
    pytest tests/backends/ -k pyglet

    # Run tests for all available backends
    pytest tests/backends/ --backend=all
"""
