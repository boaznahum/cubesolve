#!/usr/bin/env python
"""Debug why marker isn't moving after communicator."""

import sys
sys.path.insert(0, '/home/user/cubesolve/src')

import uuid
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

# Use exact same setup as test_3cycle_up_front.py
CUBE_SIZE = 5
app = AbstractApp.create_non_default(cube_size=CUBE_SIZE, animation=False)
solver = CageNxNSolver(app.op)
helper = CommunicatorHelper(solver)
cube = app.cube

n_slices = cube.n_slices
print(f"Cube size: {n_slices}x{n_slices}")

source_face = cube.up
target_face = cube.front
target_point = (0, 0)
n_slices = cube.n_slices

print(f"\n--- Testing target position t = {target_point} ---")

cube.reset()
source_face = cube.up
target_face = cube.front

# Get natural source point
natural_source = helper.get_natural_source_ltr(source_face, target_face, target_point)
print(f"Natural source s1 = {natural_source}")

source_point = natural_source
target_block = (target_point, target_point)
source_block = (source_point, source_point)

# Create marker
marker_t_key = f"t_{uuid.uuid4().hex[:4]}"
marker_t_val = "T_MARKER"

# Place marker on t (target) - BEFORE execution
target_piece_before = target_face.center.get_center_slice(target_point)
target_piece_before.edge.c_attributes[marker_t_key] = marker_t_val
print(f"Placed {marker_t_key}={marker_t_val} at t={target_point} on FRONT")

# Verify marker is there
print(f"Attributes before comm: {target_piece_before.edge.c_attributes}")

# Execute communicator
print(f"Executing communicator...")
alg = helper.do_communicator(
    source_face=source_face,
    target_face=target_face,
    target_block=target_block,
    source_block=source_block,
    preserve_state=True
)

print(f"Algorithm executed: {alg}")

# Now check where all markers are
print(f"\nAfter communicator:")

# Check target position
target_piece_after = target_face.center.get_center_slice(target_point)
print(f"  At t={target_point} on FRONT: {target_piece_after.edge.c_attributes}")

# Search ALL faces
print(f"  Searching ALL FACES for {marker_t_key}...")
all_faces = [cube.front, cube.back, cube.up, cube.down, cube.left, cube.right]
face_names = ["FRONT", "BACK", "UP", "DOWN", "LEFT", "RIGHT"]

found = False
for face, face_name in zip(all_faces, face_names):
    for search_row in range(n_slices):
        for search_col in range(n_slices):
            search_point = (search_row, search_col)
            search_piece = face.center.get_center_slice(search_point)
            if marker_t_key in search_piece.edge.c_attributes:
                print(f"    Found {marker_t_key} at {search_point} on {face_name}")
                found = True
                break
        if found:
            break
    if found:
        break

if not found:
    print(f"    ⚠️  {marker_t_key} not found on any face!")
    print(f"\n  Dumping all positions with attributes:")
    for face, face_name in zip(all_faces, face_names):
        print(f"    {face_name}:")
        for search_row in range(n_slices):
            for search_col in range(n_slices):
                search_point = (search_row, search_col)
                search_piece = face.center.get_center_slice(search_point)
                if search_piece.edge.c_attributes:
                    print(f"      {search_point}: {search_piece.edge.c_attributes}")
