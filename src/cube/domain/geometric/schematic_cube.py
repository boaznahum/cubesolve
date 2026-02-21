"""
The fixed geometric facts of a Rubik's cube, independent of color scheme.

A color scheme (like BOY — Blue-Orange-Yellow) assigns colors to faces
and can vary. But the underlying geometry cannot: Up is opposite Down,
Left is opposite Right, Front is opposite Back. A clockwise face rotation
always cycles top->right->bottom->left. These are physical facts about how
a human holds and views the cube.

Currently these facts are spread across several files:
- ``_CubeLayout.py`` — opposite/adjacent face mappings, slice rotation faces
- ``Face.py`` — edge positions (top/left/right/bottom), rotation 4-cycles
- ``FRotation.py`` — CW rotation transformations
- ``cube_boy.py`` — the standard BOY color scheme (one possible scheme)

This class is intended to consolidate the color-independent geometric
facts into a single source of truth. It is a singleton — there is only
one cube geometry, unlike ``CubeFaceColorSchema`` which can vary.
"""

from __future__ import annotations


class SchematicCube:

    _instance: SchematicCube | None = None

    def __init__(self) -> None:
        if SchematicCube._instance is not None:
            raise RuntimeError("SchematicCube is a singleton — use SchematicCube.instance()")

    @staticmethod
    def inst() -> SchematicCube:
        inst = SchematicCube._instance
        if inst is None:
            inst = SchematicCube()
            SchematicCube._instance = inst
        return inst
