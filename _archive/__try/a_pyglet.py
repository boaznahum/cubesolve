import glooey
import math

import pyglet
from pyglet import shapes

window = pyglet.window.Window(720, 480, "Shapes")
batch = pyglet.graphics.Batch()


circle = shapes.Circle(360, 240, 100, color=(255, 255, 255), batch=batch)
circle.radius = 175 + math.sin(0 * 1.17) * 30
circle.opacity = 127


@window.event
def on_draw():
    """Clear the screen and draw shapes"""
    batch.draw()
    print("xxxxxxxxxxxxxxx")


#gui = glooey.Gui(window, batch=batch)



#gui.add(glooey.Button("RRR"))

# widget = glooey.Placeholder()
# gui.add(widget)

# window.batch.draw()


pyglet.app.run()