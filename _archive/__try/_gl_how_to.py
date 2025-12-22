from pyglet.gl import *

# read matrix , but his is column-major, so you nee dto fix
v = (GLdouble * 16)()
model_view = glGetDoublev(GL_MODELVIEW_MATRIX, v)
print("Matrix 2: ")
print(v[:])

# read matrix , but his is column-major, so you nee dto fix
v = (GLdouble * 16)()
model = glGetDoublev(GL_MODEL_M, v)
print("Matrix 2: ")
print(v[:])
