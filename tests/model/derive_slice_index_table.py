"""
Empirically derive the slice index lookup table.

For each (source_face, dest_face, coord) combination, find which slice index works.
"""

from cube.domain.algs import Algs
from cube.domain.algs.Alg import Alg
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.model.FaceName import FaceName
from cube.domain.model.Face2FaceTranslator import Face2FaceTranslator, _TRANSFORMATION_TABLE, _apply_transform
from cube.domain.model.cube_slice import SliceName
# noinspection PyProtectedMember
from cube.domain.model.PartSlice import CenterSlice
from cube.application.main_app import MainApp

_test_sp = MainApp.create_non_default_service_provider()


def check_slice_index(
    cube: Cube,
    source_face: Face,
    dest_face: Face,
    coord: tuple[int, int],
    slice_alg: Alg,
    dest_coord: tuple[int, int]
) -> bool:
    """Test if a slice algorithm brings dest_coord on dest to coord on source."""
    cube.reset()
    cube.clear_c_attributes()

    row, col = coord
    source_name = source_face.name
    dest_name = dest_face.name

    # Get fresh references
    source_face = cube.face(source_name)
    dest_face = cube.face(dest_name)

    marker_value = f"TEST_{slice_alg}"

    # Place marker at dest_coord on dest face
    dest_slice: CenterSlice = dest_face.center.get_center_slice(dest_coord)
    dest_slice.edge.c_attributes["test_marker"] = marker_value

    # Apply algorithm
    slice_alg.play(cube)

    # Check if marker is at coord on source face
    source_face = cube.face(source_name)
    check_slice: CenterSlice = source_face.center.get_center_slice(coord)

    return check_slice.edge.c_attributes.get("test_marker") == marker_value


def find_working_slice_index(
    cube: Cube,
    source_face: Face,
    dest_face: Face,
    coord: tuple[int, int],
    base_slice_alg,  # Algs.M, Algs.E, or Algs.S
    n_rotations: int,
    dest_coord: tuple[int, int]
) -> int | None:
    """Find which slice index works for bringing dest to source."""
    n_slices = source_face.center.n_slices

    for slice_idx in range(1, n_slices + 1):  # 1-based indexing
        slice_alg = base_slice_alg[slice_idx] * n_rotations
        if check_slice_index(cube, source_face, dest_face, coord, slice_alg, dest_coord):
            return slice_idx

    return None  # No slice index works


def derive_table_for_face_pair(cube_size: int = 6):
    """Derive the slice index pattern for all face pairs."""
    cube = Cube(cube_size, sp=_test_sp)
    n_slices = cube.front.center.n_slices

    print(f"Cube size: {cube_size}, n_slices: {n_slices}")
    print("=" * 80)

    # Test F -> B (opposite faces, uses M and E)
    source = cube.front
    dest = cube.back

    print(f"\n{source.name} -> {dest.name} (opposite faces)")
    print("-" * 40)

    # Get transformation
    transform = _TRANSFORMATION_TABLE[(source.name, dest.name)]
    print(f"Transform: {transform}")

    # Test all coordinates
    for row in range(n_slices):
        for col in range(n_slices):
            coord = (row, col)
            dest_coord = _apply_transform(coord, transform, n_slices)

            # Find working M slice index
            # M is opposite to X, so for F->B (2 steps in X cycle), use n=2
            m_idx = find_working_slice_index(cube, source, dest, coord, Algs.M, 2, dest_coord)

            # Find working E slice index
            # E is opposite to Y, so for F->B (2 steps in Y cycle), use n=2
            e_idx = find_working_slice_index(cube, source, dest, coord, Algs.E, 2, dest_coord)

            print(f"  coord={coord} -> dest_coord={dest_coord}: M[{m_idx}], E[{e_idx}]")

    # Test L -> R (opposite faces, uses E and S)
    source = cube.left
    dest = cube.right

    print(f"\n{source.name} -> {dest.name} (opposite faces)")
    print("-" * 40)

    transform = _TRANSFORMATION_TABLE[(source.name, dest.name)]
    print(f"Transform: {transform}")

    for row in range(n_slices):
        for col in range(n_slices):
            coord = (row, col)
            dest_coord = _apply_transform(coord, transform, n_slices)

            # E for L->R: 2 steps in Y cycle
            e_idx = find_working_slice_index(cube, source, dest, coord, Algs.E, 2, dest_coord)

            # S for L->R: 2 steps in Z cycle
            s_idx = find_working_slice_index(cube, source, dest, coord, Algs.S, 2, dest_coord)

            print(f"  coord={coord} -> dest_coord={dest_coord}: E[{e_idx}], S[{s_idx}]")

    # Test U -> D (opposite faces, uses M and S)
    source = cube.up
    dest = cube.down

    print(f"\n{source.name} -> {dest.name} (opposite faces)")
    print("-" * 40)

    transform = _TRANSFORMATION_TABLE[(source.name, dest.name)]
    print(f"Transform: {transform}")

    for row in range(n_slices):
        for col in range(n_slices):
            coord = (row, col)
            dest_coord = _apply_transform(coord, transform, n_slices)

            # M for U->D: 2 steps in X cycle
            m_idx = find_working_slice_index(cube, source, dest, coord, Algs.M, 2, dest_coord)

            # S for U->D: 2 steps in Z cycle
            s_idx = find_working_slice_index(cube, source, dest, coord, Algs.S, 2, dest_coord)

            print(f"  coord={coord} -> dest_coord={dest_coord}: M[{m_idx}], S[{s_idx}]")


if __name__ == "__main__":
    derive_table_for_face_pair(6)
