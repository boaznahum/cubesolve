"""Common OpenGL utilities shared between pyglet backends.

This module provides shared OpenGL utility functions for both pyglet (legacy)
and pyglet2 (modern GL) backends.
"""
from __future__ import annotations


def _decode_gl_string(value) -> str:
    """Decode a value returned by glGetString to a Python string.

    Args:
        value: Value from glGetString (could be bytes, ctypes pointer, or None)

    Returns:
        Decoded string or "Unknown"
    """
    if value is None:
        return "Unknown"

    # If it's already a string
    if isinstance(value, str):
        return value

    # If it's bytes, decode it
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')

    # If it's a ctypes pointer (LP_c_ubyte), convert to bytes first
    try:
        import ctypes
        if hasattr(value, 'contents'):
            # It's a ctypes pointer - need to read the C string
            raw = ctypes.cast(value, ctypes.c_char_p).value
            return raw.decode('utf-8', errors='replace') if raw else "Unknown"
    except Exception:
        pass

    # Last resort - convert to string
    return str(value) if value else "Unknown"


def get_opengl_info_string() -> str:
    """Get OpenGL version and renderer info as a formatted string.

    Returns:
        Formatted string with OpenGL version, GLSL version, renderer, and vendor.
        Returns error message if OpenGL info cannot be retrieved.
    """
    try:
        from pyglet import gl

        version = gl.glGetString(gl.GL_VERSION)
        renderer = gl.glGetString(gl.GL_RENDERER)
        vendor = gl.glGetString(gl.GL_VENDOR)
        glsl_version = gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION)

        # Decode to strings (handles bytes, ctypes pointers, etc.)
        version_str = _decode_gl_string(version)
        renderer_str = _decode_gl_string(renderer)
        vendor_str = _decode_gl_string(vendor)
        glsl_str = _decode_gl_string(glsl_version)

        return (
            f"  Version:  {version_str}\n"
            f"  GLSL:     {glsl_str}\n"
            f"  Renderer: {renderer_str}\n"
            f"  Vendor:   {vendor_str}"
        )
    except Exception as e:
        return f"  Error retrieving OpenGL info: {e}"
