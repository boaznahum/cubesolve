"""
Modern OpenGL shader utilities for pyglet2 backend.

Provides helper functions for compiling, linking, and managing shaders
in OpenGL 3.3+ core profile.
"""
from __future__ import annotations

import ctypes
from typing import Any

from pyglet import gl


class ShaderError(Exception):
    """Exception raised when shader compilation or linking fails."""
    pass


def compile_shader(source: str, shader_type: int) -> int:
    """Compile a shader from source code.

    Args:
        source: GLSL shader source code
        shader_type: GL_VERTEX_SHADER or GL_FRAGMENT_SHADER

    Returns:
        Shader handle

    Raises:
        ShaderError: If compilation fails
    """
    shader = gl.glCreateShader(shader_type)

    # Convert source to bytes and create proper ctypes array
    source_bytes = source.encode('utf-8')
    source_array = (ctypes.c_char_p * 1)(source_bytes)
    gl.glShaderSource(
        shader, 1,
        ctypes.cast(source_array, ctypes.POINTER(ctypes.POINTER(ctypes.c_char))),
        None
    )
    gl.glCompileShader(shader)

    # Check for compilation errors
    success = ctypes.c_int()
    gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS, ctypes.byref(success))
    if not success.value:
        log = ctypes.create_string_buffer(1024)
        gl.glGetShaderInfoLog(shader, 1024, None, log)
        shader_type_name = "vertex" if shader_type == gl.GL_VERTEX_SHADER else "fragment"
        raise ShaderError(f"{shader_type_name} shader compilation failed: {log.value.decode()}")

    return shader


def create_program(vertex_source: str, fragment_source: str) -> int:
    """Create and link a shader program.

    Args:
        vertex_source: GLSL vertex shader source
        fragment_source: GLSL fragment shader source

    Returns:
        Program handle

    Raises:
        ShaderError: If compilation or linking fails
    """
    vert_shader = compile_shader(vertex_source, gl.GL_VERTEX_SHADER)
    frag_shader = compile_shader(fragment_source, gl.GL_FRAGMENT_SHADER)

    program = gl.glCreateProgram()
    gl.glAttachShader(program, vert_shader)
    gl.glAttachShader(program, frag_shader)
    gl.glLinkProgram(program)

    # Check for linking errors
    success = ctypes.c_int()
    gl.glGetProgramiv(program, gl.GL_LINK_STATUS, ctypes.byref(success))
    if not success.value:
        log = ctypes.create_string_buffer(1024)
        gl.glGetProgramInfoLog(program, 1024, None, log)
        raise ShaderError(f"Program linking failed: {log.value.decode()}")

    # Shaders can be deleted after linking
    gl.glDeleteShader(vert_shader)
    gl.glDeleteShader(frag_shader)

    return program


def get_uniform_location(program: int, name: str) -> int:
    """Get location of a uniform variable.

    Args:
        program: Shader program handle
        name: Uniform variable name

    Returns:
        Uniform location (-1 if not found)
    """
    return gl.glGetUniformLocation(program, name.encode('utf-8'))


def get_attrib_location(program: int, name: str) -> int:
    """Get location of an attribute variable.

    Args:
        program: Shader program handle
        name: Attribute variable name

    Returns:
        Attribute location (-1 if not found)
    """
    return gl.glGetAttribLocation(program, name.encode('utf-8'))


# === Standard Shaders ===

# Basic shader with position, color, and MVP matrix
BASIC_VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aColor;

uniform mat4 uMVP;

out vec3 vertexColor;

void main() {
    gl_Position = uMVP * vec4(aPos, 1.0);
    vertexColor = aColor;
}
"""

BASIC_FRAGMENT_SHADER = """
#version 330 core
in vec3 vertexColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(vertexColor, 1.0);
}
"""

# Simple shader for solid color (uniform color instead of per-vertex)
SOLID_COLOR_VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 aPos;

uniform mat4 uMVP;

void main() {
    gl_Position = uMVP * vec4(aPos, 1.0);
}
"""

SOLID_COLOR_FRAGMENT_SHADER = """
#version 330 core
uniform vec3 uColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(uColor, 1.0);
}
"""

# Phong lighting shader with per-vertex color and normal
# Vertex data: position (3) + normal (3) + color (3) = 9 floats per vertex
PHONG_VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec3 aColor;

uniform mat4 uMVP;
uniform mat4 uModelView;
uniform mat3 uNormalMatrix;

out vec3 vColor;
out vec3 vNormal;
out vec3 vFragPos;

void main() {
    gl_Position = uMVP * vec4(aPos, 1.0);
    vColor = aColor;
    vNormal = uNormalMatrix * aNormal;
    vFragPos = vec3(uModelView * vec4(aPos, 1.0));
}
"""

PHONG_FRAGMENT_SHADER = """
#version 330 core
in vec3 vColor;
in vec3 vNormal;
in vec3 vFragPos;

uniform vec3 uLightPos;
uniform vec3 uLightColor;
uniform vec3 uAmbientColor;
uniform float uShininess;

out vec4 FragColor;

void main() {
    // Ambient
    vec3 ambient = uAmbientColor * vColor;

    // Diffuse
    vec3 norm = normalize(vNormal);
    vec3 lightDir = normalize(uLightPos - vFragPos);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * uLightColor * vColor;

    // Specular (Blinn-Phong)
    vec3 viewDir = normalize(-vFragPos);  // Camera at origin in view space
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(norm, halfwayDir), 0.0), uShininess);
    vec3 specular = spec * uLightColor * 0.3;  // Reduced specular intensity

    vec3 result = ambient + diffuse + specular;
    FragColor = vec4(result, 1.0);
}
"""


class ShaderProgram:
    """Wrapper for an OpenGL shader program with cached uniform locations."""

    def __init__(self, vertex_source: str, fragment_source: str) -> None:
        """Create shader program from source.

        Args:
            vertex_source: GLSL vertex shader source
            fragment_source: GLSL fragment shader source
        """
        self._program = create_program(vertex_source, fragment_source)
        self._uniform_cache: dict[str, int] = {}

    @property
    def handle(self) -> int:
        """Get the OpenGL program handle."""
        return self._program

    def use(self) -> None:
        """Activate this shader program."""
        gl.glUseProgram(self._program)

    def get_uniform(self, name: str) -> int:
        """Get uniform location (cached)."""
        if name not in self._uniform_cache:
            self._uniform_cache[name] = get_uniform_location(self._program, name)
        return self._uniform_cache[name]

    def set_uniform_1f(self, name: str, value: float) -> None:
        """Set a float uniform."""
        loc = self.get_uniform(name)
        if loc >= 0:
            gl.glUniform1f(loc, value)

    def set_uniform_3f(self, name: str, x: float, y: float, z: float) -> None:
        """Set a vec3 uniform."""
        loc = self.get_uniform(name)
        if loc >= 0:
            gl.glUniform3f(loc, x, y, z)

    def set_uniform_4f(self, name: str, x: float, y: float, z: float, w: float) -> None:
        """Set a vec4 uniform."""
        loc = self.get_uniform(name)
        if loc >= 0:
            gl.glUniform4f(loc, x, y, z, w)

    def set_uniform_matrix4(self, name: str, matrix: Any) -> None:
        """Set a mat4 uniform from a numpy array or ctypes array.

        Args:
            name: Uniform name
            matrix: 4x4 matrix as numpy array or flat ctypes array
        """
        loc = self.get_uniform(name)
        if loc >= 0:
            # Handle numpy arrays
            if hasattr(matrix, 'ctypes'):
                data = matrix.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            else:
                # Assume it's already a ctypes pointer or similar
                data = matrix
            # GL_TRUE = transpose (numpy row-major -> OpenGL column-major)
            gl.glUniformMatrix4fv(loc, 1, gl.GL_TRUE, data)

    def delete(self) -> None:
        """Delete the shader program."""
        if self._program:
            gl.glDeleteProgram(self._program)
            self._program = 0
