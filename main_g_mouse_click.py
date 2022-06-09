#
#
#  Handles rotating with the mouse
#
#

from pyglet.window import key  # type: ignore
from pyglet import gl  # type: ignore

from algs import algs
from algs.algs import Alg, Algs
from app_state import ViewState
from cube_operator import Operator
from main_g_animation import AbstractWindow
from model.cube_boy import FaceName
from model.cube_face import Face
from model.elements import PartEdge, PartSlice, Part, Corner, Edge, EdgeSlice
from viewer.viewer_g import GCubeViewer


def on_mouse_press(window: AbstractWindow, vs: ViewState, op: Operator, viewer: GCubeViewer, x, y, modifiers):
    if modifiers & (key.MOD_SHIFT | key.MOD_CTRL):

        # almost as in
        # https://stackoverflow.com/questions/57495078/trying-to-get-3d-point-from-2d-click-on-screen-with-opengl
        # print(f"on mouse press: {x} {y}")
        x = float(x)
        y = window.height - float(y)
        # The following could work if we were not initially scaling to zoom on
        # the bed
        # if self.orthographic:
        #    return (x - self.width / 2, y - self.height / 2, 0)
        pmat = (gl.GLdouble * 16)()
        mvmat = (gl.GLdouble * 16)()
        # mvmat = self.get_modelview_mat(local_transform)
        viewport = (gl.GLint * 4)()
        px = gl.GLdouble()
        py = gl.GLdouble()
        pz = gl.GLdouble()

        vs = vs

        vs.prepare_objects_view()

        # 0, 0, width, height
        gl.glGetIntegerv(gl.GL_VIEWPORT, viewport)
        # print(f"{[f for f in viewport]}")

        gl.glGetDoublev(gl.GL_PROJECTION_MATRIX, pmat)
        gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX, mvmat)

        real_y = viewport[3] - y  # mouse is up down, gl is down up

        d = (gl.GLfloat * 1)()  # why ?

        gl.glReadPixels(int(x), int(real_y), 1, 1, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, d)
        # print(f"{[ f for f in d ]=}")
        # the z coordinate
        depth = d[0]

        gl.gluUnProject(x, real_y, depth, mvmat, pmat, viewport, px, py, pz)

        # print(f"{px.value=}, {py.value=}, {pz.value=}")

        vs.tx = px.value
        vs.ty = py.value
        vs.tz = pz.value

        vs.restore_objects_view()

        def _play(alg: Alg):

            if modifiers & key.MOD_CTRL:
                alg = alg.prime

            # print(f"{alg=}")

            op.op(alg)
            # why I need that
            if not op.animation_enabled:
                window.update_gui_elements()

        slice_face: PartEdge | None = viewer.find_facet(px.value, py.value, pz.value)
        if slice_face:
            _slice: PartSlice = slice_face.parent
            part: Part = _slice.parent
            face: Face = slice_face.face
            face_name: FaceName = face.name

            # print(f"@@@@@@@@@@@@@@@@@ {slice_face} {part} @ {slice_face.face} {type(part)}")
            # print(f"@@@@@@@@@@@@@@@@@ {str(_slice)}")

            # is it a corner ?
            if isinstance(part, Corner):
                # print("Is corner")
                face_alg = Algs.of_face(face_name)
                _play(face_alg)

            if isinstance(part, Edge):

                # print("Is Edge")

                assert isinstance(_slice, EdgeSlice)

                slice_alg: algs.SliceAlg | None = None
                neg_slice_index = False
                if face_name in [FaceName.F, FaceName.B]:

                    if face.is_bottom_or_top(part):
                        slice_alg = Algs.M  # we want over R
                        neg_slice_index = face_name == FaceName.F  # but r start at right, ltr is from left
                    else:
                        slice_alg = Algs.E  # we want over D
                        neg_slice_index = False
                elif face_name in [FaceName.R, FaceName.L]:

                    if face.is_bottom_or_top(part):
                        slice_alg = Algs.S  # we want over F
                        neg_slice_index = face_name == FaceName.L
                    else:
                        slice_alg = Algs.E  # we want over D
                        neg_slice_index = False
                elif face_name in [FaceName.U, FaceName.D]:

                    if face.is_bottom_or_top(part):
                        slice_alg = Algs.M  # we want over R
                        neg_slice_index = True
                    else:
                        slice_alg = Algs.S  # we want over F
                        neg_slice_index = face_name == FaceName.D

                if slice_alg:

                    index = _slice.index
                    index = part.get_ltr_index_from_slice_index(face, index)

                    if neg_slice_index:
                        index = face.inv(index)

                    slice_alg = slice_alg[index + 1]  # index start from 1

                    _play(slice_alg)
