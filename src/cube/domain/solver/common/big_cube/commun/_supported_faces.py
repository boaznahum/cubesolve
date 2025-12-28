from cube.domain.model import FaceName


def _get_supported_pairs() -> list[tuple[FaceName, FaceName]]:
    """
    Return list of (source, target) face pairs that are currently supported.

    These are the combinations that do_communicator() can handle.
    Other combinations will raise NotImplementedError.

    Returns:
        List of (source_face, target_face) tuples
    """
    return [
        (FaceName.U, FaceName.F),  # Source=Up, Target=Front
        (FaceName.B, FaceName.F),
        (FaceName.R, FaceName.F),
        (FaceName.L, FaceName.F),
        (FaceName.D, FaceName.F),
        #  (cube.back, cube.front),  # Source=Back, Target=Front
        #  (cube.down, cube.front),  # Source=Down, Target=Front
        #  (cube.left, cube.front),  # Source=Left, Target=Front (E slice)
        #  (cube.right, cube.front),  # Source=Right, Target=Front (E' slice)
    ]
