# https://hub.packtpub.com/creating-amazing-3d-guis-pyglet/

from pyglet.gl import *


def on_draw(xRotation=30, yRotation=30):
    return
    # Push Matrix onto stack
    glPushMatrix()

    glRotatef(xRotation, 1, 0, 0)
    glRotatef(yRotation, 0, 1, 0)

    # Draw the six sides of the cube
    glBegin(GL_QUADS)

    # White
    glColor3ub(255, 255, 255)
    glVertex3f(50, 50, 50)

    # Yellow
    glColor3ub(255, 255, 0)
    glVertex3f(50, -50, 50)

    # Red
    glColor3ub(255, 0, 0)
    glVertex3f(-50, -50, 50)
    glVertex3f(-50, 50, 50)

    # Blue
    glColor3f(0, 0, 1)
    glVertex3f(-50, 50, -50)

    # <… more color defines for cube faces>

    glEnd()

    # Pop Matrix off stack
    glPopMatrix()

def on_resize(width, height):
    #https://hub.packtpub.com/creating-amazing-3d-guis-pyglet/
    # set the Viewport
    glViewport(0, 0, width, height)

    # using Projection mode
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    aspectRatio = width / height
    gluPerspective(35, aspectRatio, 1, 1000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0, 0, -400)
