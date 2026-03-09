from typing import Sequence


def _inv(inv: bool, n) -> int:
    return -n if inv else n


def _format_slice_sequence(indices: Sequence[int]) -> str:
    """Format a sorted sequence of ints by compressing consecutive runs into ranges.

    Examples:
        [1, 2, 4, 5, 6] -> "1:2,4:6"
        [1, 3, 5]        -> "1,3,5"
        [1, 2, 3]        -> "1:3"
        [2]              -> "2"
    """
    if not indices:
        return ""

    parts: list[str] = []
    run_start = indices[0]
    run_end = indices[0]

    for i in range(1, len(indices)):
        if indices[i] == run_end + 1:
            run_end = indices[i]
        else:
            # Emit previous run
            if run_start == run_end:
                parts.append(str(run_start))
            else:
                parts.append(f"{run_start}:{run_end}")
            run_start = indices[i]
            run_end = indices[i]

    # Emit last run
    if run_start == run_end:
        parts.append(str(run_start))
    else:
        parts.append(f"{run_start}:{run_end}")

    return ",".join(parts)
def _normalize_for_str(n) -> int:
    n %= 4
    return n


def _normalize_for_count(n) -> int:
    n %= 4

    if n == 3:
        n = 1

    return n


def n_to_str(alg_code, n):
    s = alg_code
    n = _normalize_for_str(n)

    if n != 1:
        if n == 0:
            return alg_code + "4"
        elif n == 3:
            return s + "'"
        else:
            return s + str(2)  # 2
    else:
        return s
