#!/usr/bin/env python
"""Debug s2 discovery."""

import sys
sys.path.insert(0, '/home/user/cubesolve/src')

import uuid
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

app = AbstractApp.create_non_default(cube_size=5, animation=False)
solver = CageNxNSolver(app.op)
helper = CommunicatorHelper(solver)
cube = app.cube

source_face = cube.up
target_face = cube.front
target_point = (0, 0)
n_slices = cube.n_slices

# Get source point
natural_source = helper.get_natural_source_ltr(source_face, target_face, target_point)
source_point = natural_source

print(f"Testing UP→FRONT with t={target_point}, s1={source_point}")
print(f"Cube size: {n_slices}x{n_slices}")

# Create marker
marker_t_key = f"test_marker_{uuid.uuid4().hex[:4]}"
print(f"\nBefore communicator:")
print(f"  Placing marker '{marker_t_key}' at t={target_point} on FRONT")

target_piece = target_face.center.get_center_slice(target_point)
target_piece.edge.c_attributes[marker_t_key] = "TEST_MARKER"

# Verify marker was placed
print(f"  Marker placed: {marker_t_key in target_piece.edge.c_attributes}")
print(f"  Piece attributes: {target_piece.edge.c_attributes}")

# Execute communicator
print(f"\nExecuting communicator...")
alg = helper.do_communicator(
    source_face=source_face,
    target_face=target_face,
    target_block=(target_point, target_point),
    source_block=(source_point, source_point),
    preserve_state=True
)

print(f"Algorithm: {alg}")

# Search for marker on all faces
print(f"\nSearching for marker after communicator...")
all_faces = [cube.front, cube.back, cube.up, cube.down, cube.left, cube.right]
face_names = ["FRONT", "BACK", "UP", "DOWN", "LEFT", "RIGHT"]

found = False
for face, face_name in zip(all_faces, face_names):
    print(f"  Searching {face_name}...")
    for r in range(n_slices):
        for c in range(n_slices):
            pos = (r, c)
            piece = face.center.get_center_slice(pos)
            if marker_t_key in piece.edge.c_attributes:
                print(f"    ✅ Found at {pos}: {piece.edge.c_attributes[marker_t_key]}")
                found = True
            # Show any markers we find
            if piece.edge.c_attributes:
                markers = [k for k in piece.edge.c_attributes.keys() if 'marker' in k.lower() or 'test' in k.lower()]
                if markers:
                    print(f"    → At {pos}: {markers}")

if not found:
    print(f"  ❌ Marker not found on any face!")
    print(f"\n  Checking what's at target position on FRONT after communicator:")
    target_piece_after = target_face.center.get_center_slice(target_point)
    print(f"    Attributes: {target_piece_after.edge.c_attributes}")
