import importlib.resources as pkg_resources
from collections.abc import Sequence
from pathlib import Path

import pyglet  # type: ignore
from pyglet import gl

from . import res


class TextureData:
    __slots__ = ["_g_texture_list",
                 "_gl_texture_id",
                 "_texture_map"
                 ]

    _g_texture_list: int
    _gl_texture_id: int
    _texture_map: Sequence[tuple[int, int]]

    def __init__(self) -> None:
        super().__init__()

    @property
    def gl_list(self) -> gl.GLuint:
        return self._g_texture_list

    @property
    def texture_map(self) -> Sequence[tuple[int, int]]:
        return self._texture_map

    def cleanup(self):
        """
        Release resources upon exit
        :return:
        """

        p = (gl.GLuint * 1)()
        p[0] = self._gl_texture_id

        gl.glDeleteTextures(len(p), p)

        gl.glDeleteLists(self._g_texture_list, 1)

        print(f"{gl.glGetError()=}")

    @staticmethod
    def load(file_name: str, texture_map: Sequence[tuple[int, int]]) -> "TextureData":
        """

        :param texture_map:
        :param file_name: under viewer/res
        :return:
        """
        td = TextureData()

        g_texture_list = gl.glGenLists(1)
        #
        #gl.glNewList(g_texture_list, gl.GL_COMPILE)

        with pkg_resources.path(res, file_name) as path:
            gl_texture_id = TextureData._load_texture_and_compile(path, g_texture_list)

        #gl.glEndList()

        td._g_texture_list = g_texture_list
        td._gl_texture_id = gl_texture_id

        td._texture_map = texture_map

        return td

    @staticmethod
    def _load_texture_and_compile(image_path: Path, g_texture_list):
        """
        Thanks to https://github.com/Minipeps/TwoPhase-Cuber
        """
        image = pyglet.image.load(image_path)

        data = image.get_image_data()

        texture_data = data.get_data(fmt="RGBA")

        ids = (gl.GLuint * 1)()
        gl.glGenTextures(1, ids)
        tex_id = ids[0]

        gl.glNewList(g_texture_list, gl.GL_COMPILE)

        gl.glBindTexture(gl.GL_TEXTURE_2D, tex_id)
        gl.gluBuild2DMipmaps(gl.GL_TEXTURE_2D, 4,
                             image.width,
                             image.height,
                             gl.GL_BGRA, gl.GL_UNSIGNED_BYTE, texture_data)

        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)

        gl.glEndList()

        return tex_id
