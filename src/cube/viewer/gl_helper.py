from contextlib import contextmanager

from pyglet import gl  # type: ignore
from pyglet.gl import *  # type: ignore


@contextmanager
def with_gl_enable(*cap: gl.GLenum ):
    """

    :param cap: see values in https://www.khronos.org/registry/OpenGL-Refpages/gl4/html/glIsEnabled.xhtml
    :return:
    """

    caps = [*cap]

    enabled = [ gl.glIsEnabled(c)  for c in caps ]

    for e, c in zip(enabled, caps):
        if not e:
            gl.glEnable(c)

    try:
        yield None
    finally:

        for e, c in zip( reversed(enabled), reversed(caps)):
            if not e:
                gl.glDisable(c)



