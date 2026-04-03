#!/usr/bin/env python
"""Compare two parity report JSON files and show differences.

Usage:
    python tests/solvers/compare_parity_reports.py BEFORE.json AFTER.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compare(before: dict, after: dict) -> None:
    meta_b, meta_a = before["meta"], after["meta"]
    res_b, res_a = before["results"], after["results"]

    print(f"BEFORE: branch={meta_b['branch']}  commit={meta_b['commit']}  ts={meta_b['timestamp']}")
    print(f"AFTER:  branch={meta_a['branch']}  commit={meta_a['commit']}  ts={meta_a['timestamp']}")
    print()

    all_keys = sorted(set(res_b) | set(res_a))

    diffs: list[tuple[str, dict, dict]] = []
    new_parity: list[tuple[str, dict]] = []
    lost_parity: list[tuple[str, dict]] = []
    same = 0
    skipped = 0

    for key in all_keys:
        b = res_b.get(key, {"missing": True})
        a = res_a.get(key, {"missing": True})

        # Skip entries where either side is skipped/missing
        if "skipped" in b or "skipped" in a or "missing" in b or "missing" in a:
            skipped += 1
            continue

        b_scalar = (b.get("was_corner_swap"), b.get("was_even_edge_parity"), b.get("was_partial_edge_parity"))
        a_scalar = (a.get("was_corner_swap"), a.get("was_even_edge_parity"), a.get("was_partial_edge_parity"))

        b_has = b.get("has_parity", False)
        a_has = a.get("has_parity", False)

        if b_scalar == a_scalar and b_has == a_has:
            same += 1
            continue

        if not b_has and a_has:
            new_parity.append((key, a))
        elif b_has and not a_has:
            lost_parity.append((key, b))
        else:
            diffs.append((key, b, a))

    print(f"Total keys: {len(all_keys)}  same: {same}  skipped: {skipped}")
    print(f"Changed: {len(diffs)}  new_parity: {len(new_parity)}  lost_parity: {len(lost_parity)}")
    print()

    if lost_parity:
        print("=== LOST PARITY (was reported BEFORE but not AFTER) ===")
        for key, b in lost_parity:
            solver, size, seed = key.split("|")
            print(f"  {solver} {size}x{size} seed={seed}: BEFORE={b.get('summary', '?')}")
        print()

    if new_parity:
        print("=== NEW PARITY (not reported BEFORE but reported AFTER) ===")
        for key, a in new_parity:
            solver, size, seed = key.split("|")
            print(f"  {solver} {size}x{size} seed={seed}: AFTER={a.get('summary', '?')}")
        print()

    if diffs:
        print("=== CHANGED PARITY (reported differently) ===")
        for key, b, a in diffs:
            solver, size, seed = key.split("|")
            print(f"  {solver} {size}x{size} seed={seed}:")
            print(f"    BEFORE: {b.get('summary', '?')}")
            print(f"    AFTER:  {a.get('summary', '?')}")
            bp = b.get("parities", [])
            ap = a.get("parities", [])
            if bp != ap:
                print(f"    BEFORE parities: {bp}")
                print(f"    AFTER  parities: {ap}")
        print()

    if not diffs and not new_parity and not lost_parity:
        print("=== NO DIFFERENCES — scalar parity fields are identical ===")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} BEFORE.json AFTER.json")
        sys.exit(1)
    compare(load(sys.argv[1]), load(sys.argv[2]))


if __name__ == "__main__":
    main()
