from cube.domain.model import FaceName


def _get_supported_pairs() -> list[tuple[FaceName, FaceName]]:
    """
    Return list of (source, target) face pairs that are currently supported.

    These are the combinations that do_communicator() can handle.
    Other combinations will raise NotImplementedError.

    Returns:
        List of (source_face, target_face) tuples
    """
    worked = [
        #  Source    #Target
         (FaceName.U, FaceName.F),  # Source=Up, Target=Front
         (FaceName.B, FaceName.F),
         (FaceName.R, FaceName.F),
         (FaceName.L, FaceName.F),
         (FaceName.D, FaceName.F),

         (FaceName.U, FaceName.R),  # Source=Up, Target=Front
         (FaceName.B, FaceName.R),
         (FaceName.F, FaceName.R),
         (FaceName.L, FaceName.R),
         (FaceName.D, FaceName.R),

        (FaceName.U, FaceName.L),  # Source=Up, Target=Front
        (FaceName.B, FaceName.L),
        (FaceName.F, FaceName.L),
        (FaceName.R, FaceName.L),
        (FaceName.D, FaceName.L),

        #  Source    #Target
        (FaceName.L, FaceName.U),  # Source=Up, Target=Front
        (FaceName.B, FaceName.U),
        (FaceName.F, FaceName.U),
        (FaceName.R, FaceName.U),
        (FaceName.D, FaceName.U),

        #  Source    #Target
        (FaceName.L, FaceName.B),  # Source=Up, Target=Front
        (FaceName.U, FaceName.B),
        (FaceName.F, FaceName.B),
        (FaceName.R, FaceName.B),
        (FaceName.D, FaceName.B)
    ]

    working = [



         ]

    if True:
        return worked + working
    else:
        return working


