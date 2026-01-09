# Why we need this (the else)
```
        if False:
            rotation_edges = cube.layout.get_face_edge_rotation_cw(rotation_face)
        else:
            # claude code don't understand why it works
            if use_clockwise:
                # Clockwise: top, right, bottom, left
                rotation_edges = [rotation_face.edge_top, rotation_face.edge_right,
                                 rotation_face.edge_bottom, rotation_face.edge_left]
            else:
                # Counter-clockwise: right, top, left, bottom
                rotation_edges = [rotation_face.edge_right, rotation_face.edge_top,
                                 rotation_face.edge_left, rotation_face.edge_bottom]

```

see image:
![img.png](img.png)

the index is close to the LTR origin