# 2x2 Rubik's Cube Solver — IDA* Optimal Algorithm

## State Space

- **Positions:** 3,674,160 (7! x 3^6)
- **God's number:** 11 moves (HTM)
- **Average optimal solution:** 8.76 moves
- **Depth distribution:** 1 at d=0, 9 at d=1, 54 at d=2, 321 at d=3, 1847 at d=4, 9992 at d=5, 50136 at d=6, 227536 at d=7, 870072 at d=8, 1887748 at d=9, 623800 at d=10, 2644 at d=11

## Algorithm

### Fix DBL Corner

We fix corner 7 (DBL) in place and only use **U, R, F** moves (9 total: U, U2, U', R, R2, R', F, F2, F'). This reduces the state space from 88,179,840 to 3,674,160.

### Coordinate System

Two coordinates fully encode the state:

1. **Twist (0-728):** Orientation of corners 0-5 encoded in base-3. Corner 6's orientation is derived (total twist mod 3 = 0). Corner 7 (DBL) is fixed at orientation 0.

2. **Permutation (0-5039):** Lehmer code encoding the permutation of corners 0-6. Corner 7 (DBL) is fixed in place.

### Corner Numbering (Kociemba Standard)

```
URF=0  UFL=1  ULB=2  UBR=3  DFR=4  DLF=5  DBL=6  DRB=7
```

### Orientation Convention

- **0:** U/D-colored sticker on U or D face (oriented)
- **1:** U/D-colored sticker one position clockwise
- **2:** U/D-colored sticker one position counter-clockwise

### Move Definitions (Cubie Level)

```
U: [UBR, URF, UFL, ULB, DFR, DLF, DBL, DRB]  co=[0,0,0,0,0,0,0,0]
R: [DFR, UFL, ULB, URF, DRB, DLF, DBL, UBR]  co=[2,0,0,1,1,0,0,2]
F: [UFL, DLF, ULB, UBR, URF, DFR, DBL, DRB]  co=[1,2,0,0,2,1,0,0]
```

## Precomputed Tables

### Move Tables

- **twist_move[729 x 9]:** New twist coordinate after applying each of the 9 moves. Stored as `array('H')`, ~13 KB.
- **perm_move[5040 x 9]:** New permutation coordinate after applying each of the 9 moves. Stored as `array('H')`, ~91 KB.

### Pruning Table

- **pruning[5040 x 729]:** Exact distance from solved for every position. Computed via BFS from the solved state. Stored as `bytearray`, ~3.5 MB.
- Since the table stores exact distances, IDA* has zero wasted iterations.

## IDA* Search

1. Look up exact distance from pruning table as initial depth limit.
2. Recursive depth-first search with same-face pruning (skip moves on same face as last move).
3. At each node, if pruning[state] > remaining depth, prune.
4. With exact pruning, the first iteration always succeeds.

## Performance

- **Table build time:** ~2-5 seconds (one-time, cached in memory)
- **Solve time:** Sub-millisecond (typically <0.1ms)
- **Memory:** ~3.6 MB for all tables

## Files

- `ida_star_tables.py` — Table generation, coordinate helpers, lazy singleton
- `ida_star_search.py` — IDA* search function
- `cube_to_coordinates.py` — Bridge from domain Cube to IDA* coordinates
- `Solver2x2.py` — Solver class integrating IDA* with the domain model

## References

- Kociemba, Herbert. "Cube Explorer" — http://kociemba.org/cube.htm
- Jaap Scherphuis. "Jaap's Puzzle Page — Pocket Cube" — https://www.jaapsch.net/puzzles/cube2.htm
