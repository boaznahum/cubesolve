#!/usr/bin/env python
"""
Benchmark: c_attributes copy vs swap during rotation.

This benchmark compares the old approach (copying dict contents) with the
new approach (swapping dict references) for the c_attributes dictionary
during face and slice rotations.

See: docs/design2/rotation-c_attributes-optimization.md

Usage:
    PYTHONPATH=src python tests/performance/benchmark_rotation_c_attributes.py
"""

import time
import random
import sys
import os

# Add src to path if running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from cube.domain.model.Cube import Cube
from cube.domain.model.PartEdge import PartEdge
from tests.test_utils import TestServiceProvider


def old_copy_color(dest: PartEdge, source: PartEdge):
    """Simulate the OLD approach - copy dict contents."""
    dest._color = source._color
    dest._annotated_by_color = source._annotated_by_color
    dest._texture_direction = source._texture_direction
    dest.c_attributes.clear()
    dest.c_attributes.update(source.c_attributes)


def old_rotate_4cycle(p0: PartEdge, p1: PartEdge, p2: PartEdge, p3: PartEdge):
    """Simulate the OLD 4-cycle with dict copying."""
    # Save copies
    saved_color = p0._color
    saved_annotated = p0._annotated_by_color
    saved_texture = p0._texture_direction
    saved_attrs = p0.c_attributes.copy()  # COPY the dict - O(K)

    # Sequential copies
    old_copy_color(p0, p1)
    old_copy_color(p1, p2)
    old_copy_color(p2, p3)

    # Restore from saved
    p3._color = saved_color
    p3._annotated_by_color = saved_annotated
    p3._texture_direction = saved_texture
    p3.c_attributes.clear()
    p3.c_attributes.update(saved_attrs)


def setup_cube_with_attributes(cube: Cube, num_attrs: int):
    """Add c_attributes to all stickers on the cube."""
    for face in [cube.front, cube.back, cube.left, cube.right, cube.up, cube.down]:
        # Edges
        for edge in [face._edge_top, face._edge_left, face._edge_bottom, face._edge_right]:
            for i in range(cube.n_slices):
                pe = edge.get_slice(i).get_face_edge(face)
                for k in range(num_attrs):
                    pe.c_attributes[f'attr_{k}'] = f'value_{k}' * 10
        # Corners
        for corner in [face._corner_top_left, face._corner_top_right,
                       face._corner_bottom_left, face._corner_bottom_right]:
            pe = corner.get_face_edge(face)
            for k in range(num_attrs):
                pe.c_attributes[f'attr_{k}'] = f'value_{k}' * 10


def benchmark_rotation(cube: Cube, use_new_approach: bool, num_rotations: int = 500) -> float:
    """
    Benchmark rotation performance.

    Args:
        cube: The cube to rotate
        use_new_approach: If True, use PartEdge.rotate_4cycle; else use old_rotate_4cycle
        num_rotations: Number of random face rotations to perform

    Returns:
        Time taken in seconds
    """
    faces = [cube.front, cube.back, cube.left, cube.right, cube.up, cube.down]
    rotate_fn = PartEdge.rotate_4cycle if use_new_approach else old_rotate_4cycle

    start = time.perf_counter()
    for _ in range(num_rotations):
        face = random.choice(faces)
        n_slices = cube.n_slices

        # Edge cycles (2 per rotation)
        for idx in range(n_slices):
            # Cycle on rotating face
            p0 = face._edge_top.get_slice(idx).get_face_edge(face)
            p1 = face._edge_left.get_slice(idx).get_face_edge(face)
            p2 = face._edge_bottom.get_slice(idx).get_face_edge(face)
            p3 = face._edge_right.get_slice(idx).get_face_edge(face)
            rotate_fn(p0, p1, p2, p3)

            # Cycle on adjacent faces
            adj_top = face._edge_top.get_other_face(face)
            adj_left = face._edge_left.get_other_face(face)
            adj_bottom = face._edge_bottom.get_other_face(face)
            adj_right = face._edge_right.get_other_face(face)
            p0 = face._edge_top.get_slice(idx).get_face_edge(adj_top)
            p1 = face._edge_left.get_slice(idx).get_face_edge(adj_left)
            p2 = face._edge_bottom.get_slice(idx).get_face_edge(adj_bottom)
            p3 = face._edge_right.get_slice(idx).get_face_edge(adj_right)
            rotate_fn(p0, p1, p2, p3)

        # Corner cycles (3 per rotation)
        c_bl = face._corner_bottom_left
        c_br = face._corner_bottom_right
        c_tr = face._corner_top_right
        c_tl = face._corner_top_left
        for _ in range(3):
            rotate_fn(
                c_bl.get_face_edge(face), c_br.get_face_edge(face),
                c_tr.get_face_edge(face), c_tl.get_face_edge(face)
            )

    return time.perf_counter() - start


def run_benchmark(cube_size: int = 9, num_rotations: int = 500):
    """Run the full benchmark suite."""
    sp = TestServiceProvider()

    print('=' * 60)
    print(f'BENCHMARK: c_attributes Copy vs Swap')
    print(f'Cube size: {cube_size}x{cube_size}, Rotations: {num_rotations}')
    print('=' * 60)
    print()

    results = []
    for num_attrs in [0, 5, 10, 20, 50]:
        print(f'--- {num_attrs} attributes per sticker ---')

        # Seed random for reproducibility
        random.seed(42)

        # OLD approach
        cube_old = Cube(size=cube_size, sp=sp)
        setup_cube_with_attributes(cube_old, num_attrs)
        old_time = benchmark_rotation(cube_old, use_new_approach=False, num_rotations=num_rotations)

        # NEW approach
        random.seed(42)  # Same seed for fair comparison
        cube_new = Cube(size=cube_size, sp=sp)
        setup_cube_with_attributes(cube_new, num_attrs)
        new_time = benchmark_rotation(cube_new, use_new_approach=True, num_rotations=num_rotations)

        speedup = old_time / new_time if new_time > 0 else 0
        results.append((num_attrs, old_time, new_time, speedup))
        print(f'  OLD: {old_time * 1000:.1f}ms | NEW: {new_time * 1000:.1f}ms | Speedup: {speedup:.2f}x')
        print()

    print('=' * 60)
    print('SUMMARY')
    print('=' * 60)
    print(f'{"Attrs":>6} | {"OLD (ms)":>10} | {"NEW (ms)":>10} | {"Speedup":>8}')
    print('-' * 45)
    for num_attrs, old_t, new_t, speedup in results:
        print(f'{num_attrs:>6} | {old_t * 1000:>10.1f} | {new_t * 1000:>10.1f} | {speedup:>7.2f}x')

    return results


if __name__ == '__main__':
    run_benchmark()
