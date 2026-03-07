# Session: web1 — Dwalton Table-Based Solver

## Goal
Implement a new solver inspired by [dwalton76/rubiks-cube-NxNxN-solver](https://github.com/dwalton76/rubiks-cube-NxNxN-solver), which uses precomputed lookup/pruning tables with IDA* search based on Herbert Kociemba's two-phase algorithm.

## Research Phase

### What dwalton76's solver does
- For **3x3**: Delegates to the external `kociemba` CLI binary (not its own algorithm)
- For **NxN**: Reduces to a virtual 3x3 using IDA* with lookup tables, then calls kociemba
- Key technique: **precomputed pruning tables** as heuristics for IDA* search
- Cube state: 1-indexed list of 55 chars (ULFRBD order), moves as permutation tuples
- Move application: `new_state = [old_state[perm[i]] for i in range(55)]` — O(54) per move

### What we implemented
Instead of delegating to an external binary, we implemented the **full Kociemba two-phase algorithm from scratch** in pure Python, using the same table-based approach.

---

## Algorithm: Kociemba Two-Phase

### Overview
The cube's 4.3×10^19 states are split into two nested subgroups:

```
G0 (all states)  →  G1 = <U, D, R2, L2, F2, B2>  →  G2 = {solved}
     Phase 1                   Phase 2
```

- **Phase 1**: Reduce the cube so that corner orientations are correct, edge orientations are correct, and equator-layer (E-slice) edges are in the equator — regardless of exact permutation.
- **Phase 2**: Solve the remaining permutation using only moves that preserve G1 membership (U, U2, U', D, D2, D', R2, L2, F2, B2).

### Coordinate System

Each phase uses integer **coordinates** that compactly represent the relevant aspects of the cube state:

#### Phase 1 Coordinates (track orientation + E-slice membership)
| Coordinate | Range | What it encodes |
|-----------|-------|-----------------|
| **CO** (Corner Orientation) | 0..2186 (3^7) | Twist of 7 corners (8th determined by sum mod 3) |
| **EO** (Edge Orientation) | 0..2047 (2^11) | Flip of 11 edges (12th determined by sum mod 2) |
| **UD-slice** | 0..494 (C(12,4)) | Which 4 of 12 edge positions hold E-slice edges |

Phase 1 goal: CO=0, EO=0, UD-slice=494 (solved value)

#### Phase 2 Coordinates (track permutation)
| Coordinate | Range | What it encodes |
|-----------|-------|-----------------|
| **CP** (Corner Permutation) | 0..40319 (8!) | Which corner is in which position (Lehmer code) |
| **UDEP** (UD-Edge Permutation) | 0..40319 (8!) | Permutation of 8 U/D-layer edges |
| **EP** (E-slice Permutation) | 0..23 (4!) | Permutation of 4 E-slice edges within their slots |

Phase 2 goal: CP=0, UDEP=0, EP=0

### Move Tables
For each of the 18 moves (6 faces × {CW, 180°, CCW}), a **move table** stores how each coordinate changes:

```
co_move[move][old_coord] = new_coord
```

Built by: for each possible coordinate value, decode it to cubie arrays, apply the move via composition, re-encode to coordinate.

Total move table entries: 18 × (2187 + 2048 + 495 + 40320 + 40320 + 24) = ~1.5M integers

### Pruning Tables
Pruning tables store the **minimum number of moves** to reach the goal from any pair of coordinates. They serve as admissible heuristics for IDA*.

Built via **BFS from the goal state**:

```python
# Start: goal = 0 moves
table[goal_a * n_b + goal_b] = 0

# BFS: for each state at depth d, apply all moves to find depth d+1 states
while not all states filled:
    for each state at current depth:
        for each move:
            new_state = move_table[move][state]
            if new_state not yet visited:
                table[new_state] = depth + 1
```

#### Phase 1 Pruning Tables
| Table | Size | What it combines |
|-------|------|-----------------|
| **CO × UD-slice** | 2187 × 495 = 1,082,565 | Corner orient + E-slice position |
| **EO × UD-slice** | 2048 × 495 = 1,013,760 | Edge orient + E-slice position |

Heuristic: `h = max(CO×UD_table[co,ud], EO×UD_table[eo,ud])`

#### Phase 2 Pruning Tables
| Table | Size | What it combines |
|-------|------|-----------------|
| **CP × EP** | 40320 × 24 = 967,680 | Corner perm + E-slice perm |
| **UDEP × EP** | 40320 × 24 = 967,680 | UD-edge perm + E-slice perm |

Heuristic: `h = max(CP×EP_table[cp,ep], UDEP×EP_table[udep,ep])`

### IDA* Search

**Iterative Deepening A***: tries increasing depth limits, pruning branches where `g + h > threshold`.

```
Phase 1:
  for depth = 0, 1, 2, ..., 12:
    DFS with pruning: if h(co, eo, ud) > remaining_depth → prune
    When Phase 1 goal reached → compute Phase 2 coords from cubie state → run Phase 2

Phase 2:
  for depth = 0, 1, 2, ..., 18:
    DFS with pruning: if h(cp, udep, ep) > remaining_depth → prune
    When all coords = 0 → solution found!
```

**Move pruning**: Skip moves on the same face as the previous move, and enforce ordering for opposite faces (U before D, R before L, F before B) to avoid redundant sequences like `U D U`.

### Key Design Decision: Cubie State Tracking in Phase 1

Phase 2 coordinates (CP, UDEP, EP) can't be tracked through Phase 1 via move tables because moves mix UD and E-slice edges, making the UDEP/EP coordinates invalid when E-slice edges aren't in their slots.

**Solution**: Track full cubie arrays (cp, co, ep, eo) alongside Phase 1 coordinates. When Phase 1 completes, compute Phase 2 coordinates directly from the cubie state.

---

## Table Build Performance

All tables built in ~12 seconds on first use, cached in module-level variables (no disk I/O):

| Table Type | Entries | Build Time |
|-----------|---------|------------|
| Move tables (6 coords × 18 moves) | ~1.5M | ~8s |
| Pruning tables (4 tables) | ~4M | ~4s |
| **Total** | **~5.5M integers** | **~12s** |

Tables are **not persisted to disk** — purely in-memory. They're rebuilt each time the solver is first used in a session.

---

## File Structure

### New Files (6 files in `src/cube/domain/solver/_3x3/dwalton/`)

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 5 | Package init, exports `Dwalton3x3` |
| `cubie_defs.py` | 105 | 8 corners, 12 edges, 18 moves as permutation+orientation arrays. Derives half/inverse turns from quarter turns via composition. |
| `coords.py` | 99 | Coordinate encoding functions: `corner_orientation_coord()`, `edge_orientation_coord()`, `ud_slice_coord()`, `corner_perm_coord()`, `edge8_perm_coord()`, `eslice_perm_coord()` |
| `tables.py` | 185 | Move table builder (decode coord → apply move → re-encode) and pruning table builder (BFS from goal). `build_all_tables()` entry point. |
| `search.py` | 120 | IDA* search for Phase 1 and Phase 2 with move pruning. `solve(cp, co, ep, eo)` entry point. |
| `Dwalton3x3.py` | 189 | Main solver class. Converts cube model → 54-char URFDLB string → cubie arrays → search → play solution moves. Implements `Solver3x3Protocol`. |

### Modified Files (5 files)

| File | Change |
|------|--------|
| `SolverName.py` | Added `DWALTON = SolverMeta("Dwalton")` to enum |
| `Solvers.py` | Added `dwalton()` factory method + `by_name()` match case |
| `Solvers3x3.py` | Added `dwalton()` factory method + `by_name()` match case |
| `README.md` | Added credits for dwalton76 and Herbert Kociemba |
| `.claude/sessions/web1.md` | This file |

---

## How the Cube Model ↔ Solver Bridge Works

1. **Cube → Facelet String**: Read 54 facelets in URFDLB order using dynamic color→face mapping (handles center color changes from slice moves)
2. **Facelet String → Cubies**: For each corner/edge position, match the 3/2 colors against all solved corner/edge color triples to identify which piece is there and its orientation
3. **Cubies → Coordinates**: Encode cubie arrays as integer coordinates
4. **Search**: IDA* finds a sequence of move names (e.g., `["R'", "U2", "F"]`)
5. **Execute**: Parse move names via `parse_alg()` and play via `op.play()`

### Corner Orientation Convention
- Twist 0: U/D reference sticker on U/D face (correct position)
- Twist 1: U/D reference sticker at position 1 in the corner triple
- Twist 2: U/D reference sticker at position 2 in the corner triple

This matches the cubie_defs move definitions where R move gives CO = [2,0,0,1,1,0,0,2].

---

## Test Results

**7,578 tests passed** (all solvers, all cube sizes):

```
Dwalton 3x3: 314 passed — all scramble seeds
Dwalton 4x4: 314 passed — with BeginnerReducer + parity handling
Dwalton 5x5: 314 passed — with BeginnerReducer
Dwalton 8x8: 314 passed — with BeginnerReducer + parity handling
Other solvers (LBL, CFOP, Kociemba, Cage, LBL-Big): all passed unchanged
```

Solve performance (after table build):
- Fast scrambles: 10-50ms
- Hard scrambles: 0.5-1.5s
- Table build (one-time): ~12s

---

## Commits
- Not yet committed — awaiting user review.
