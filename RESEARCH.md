# Rubik's Cube Solver — Research & Learning Resources

A comprehensive collection of open-source codebases, online solvers, algorithms, academic papers,
and learning resources for building Rubik's cube solvers — with emphasis on NxN / big cube solving.

---

## Table of Contents

1. [Python Open-Source Codebases](#1-python-open-source-codebases)
2. [Online Web Solvers & Simulators](#2-online-web-solvers--simulators)
3. [3D Visualization Projects (Three.js / WebGL)](#3-3d-visualization-projects-threejs--webgl)
4. [Machine Learning / AI Approaches](#4-machine-learning--ai-approaches)
5. [God's Number & Optimal Solving Research](#5-gods-number--optimal-solving-research)
6. [Commutators & Big Cube Theory](#6-commutators--big-cube-theory)
7. [Parity (Even Cubes)](#7-parity-even-cubes)
8. [Group Theory / Mathematics](#8-group-theory--mathematics)
9. [Algorithm Databases (CFOP Reference)](#9-algorithm-databases-cfop-reference)
10. [Top Recommendations for This Project](#10-top-recommendations-for-this-project)

---

## 1. Python Open-Source Codebases

### NxN / Big Cube Solvers

- **[dwalton76/rubiks-cube-NxNxN-solver](https://github.com/dwalton76/rubiks-cube-NxNxN-solver)**
  — The closest comparable project to cubesolve. Generic NxN solver using reduction + Kociemba for
  the 3x3 phase. Uses lookup tables stored on S3. Good reference for how another developer tackled
  the same NxN problem.

- **[ShellPuppy/RCube](https://github.com/ShellPuppy/RCube)**
  — Solves cubes from 1 to **65,536 layers**. Solve time grows ~N². A 1024-layer cube solves in
  ~1.5 seconds. Great for studying scalable algorithms.

### 3x3 Optimal / Near-Optimal Solvers

- **[hkociemba/RubiksCube-TwophaseSolver](https://github.com/hkociemba/RubiksCube-TwophaseSolver)**
  — Herbert Kociemba's official Python two-phase solver. Solves in <20 moves avg. cubesolve already
  wraps this via the `kociemba` library, but studying the internals (pruning tables, coordinate
  systems) is valuable for understanding how it achieves near-optimal solutions.

- **[hkociemba/RubiksCube-OptimalSolver](https://github.com/hkociemba/RubiksCube-OptimalSolver)**
  — God's algorithm in Python. Uses IDA* with pruning tables. Explores whether optimal solving is
  feasible in Python (spoiler: barely, but very educational for understanding the search space).

- **[muodov/kociemba](https://github.com/muodov/kociemba)**
  — Pure Python + C port of Kociemba's algorithm. Falls back to Python if C isn't available. The C
  implementation is useful if you want speed improvements over the pure Python version.

- **[tcbegley/cube-solver](https://github.com/tcbegley/cube-solver)**
  — Clean pure-Python two-phase implementation. Good for understanding the algorithm without C
  dependencies.

### CFOP Method Implementations

- **[saiakarsh193/PyCube-Solver](https://github.com/saiakarsh193/PyCube-Solver)**
  — Well-structured CFOP solver with clean separation of cube manipulation and solving logic.

- **[CubeLuke/Rubiks-Cube-Solver](https://github.com/CubeLuke/Rubiks-Cube-Solver)**
  — CFOP with 2-look OLL and 2-look PLL.

- **[Micwsr/rubik_solver](https://github.com/Micwsr/rubik_solver)**
  — Pure Python, no external libs, handles all 21 PLL cases.

### Other Notable Python Projects

- **[pglass/cube](https://github.com/pglass/cube)**
  — Clean 3x3 solver with a well-designed `Piece` class. Good for comparing cube model design.

- **[adrianliaw/PyCuber](https://github.com/adrianliaw/PyCuber)**
  — Formula manipulation tools (reverse, mirror). Useful for algorithm database work.

### Algorithm Comparison

- **[The-Semicolons/AnalysisofRubiksCubeSolvingAlgorithm](https://github.com/The-Semicolons/AnalysisofRubiksCubeSolvingAlgorithm)**
  — Implements and benchmarks Kociemba, Korf, Thistlethwaite, and Rokicki side by side. Great for
  understanding the trade-offs between different solving approaches.

---

## 2. Online Web Solvers & Simulators

- **[rubiks-cube-solver.com](https://rubiks-cube-solver.com/)**
  — Uses Kociemba, solves in ≤20 moves. Good UX reference for solver presentation.

- **[ruwix.com/online-rubiks-cube-solver-program](https://ruwix.com/online-rubiks-cube-solver-program/)**
  — Full-featured: drag-to-turn, color input, image export. Excellent UI for studying solver
  interaction patterns.

- **[cube-solver.com](https://cube-solver.com/)**
  — **NxN online solver and simulator** — directly relevant for comparing output with cubesolve's
  solvers across different cube sizes.

- **[rubikscu.be](https://rubikscu.be/)**
  — Simulator + solver + timer + beginner tutorial. All-in-one learning tool.

- **[grubiks.com](https://www.grubiks.com/)**
  — 3D puzzle solver with step-by-step instructions. Good reference for step-by-step visualization.

- **[cubzor.com](https://www.cubzor.com)**
  — Covers CFOP, Roux, and ZZ methods with interactive tutorials. Useful for comparing multiple
  solving methods.

- **[ruwix.com/widget/3d](https://ruwix.com/widget/3d/)**
  — Embeddable 3D cube widget using Roofpig (Three.js). Could inspire the web backend rendering
  approach.

---

## 3. 3D Visualization Projects (Three.js / WebGL)

Relevant to the web backend work in cubesolve:

- **[irisxu02/rubik](https://github.com/irisxu02/rubik)**
  — Three.js frontend + Python backend with `/solve` endpoint using Kociemba. Very similar
  architecture to cubesolve's web backend (WebSocket + browser). Good reference for how to structure
  the communication between a Python solver and a browser-based 3D renderer.

- **[dejwi/rubiks-app](https://github.com/dejwi/rubiks-app)**
  — Next.js + Three.js + camera scanning. Step-by-step 3D solution visualization. Interesting for
  the camera-based input approach.

- **[MeharGaur/rubiks](https://github.com/MeharGaur/rubiks)**
  — TypeScript + WebGL + C/C++ solver. Shows how to integrate a native solver with a web frontend
  for performance.

- **[blonkm/rubiks-cube](https://github.com/blonkm/rubiks-cube)** (GLube)
  — Embeddable, configurable cube widget with Generator/Solver modes. Good for studying modular
  widget design.

---

## 4. Machine Learning / AI Approaches

- **[DeepCubeA](https://deepcube.igb.uci.edu/)**
  — Deep RL + A* search. 100% solve rate, finds shortest path 60.3% of the time. Published in
  [Nature Machine Intelligence](https://www.nature.com/articles/s42256-019-0070-z). Represents an
  entirely different paradigm from classical algorithmic approaches.

- **[jasonrute/puzzle_cube](https://github.com/jasonrute/puzzle_cube)**
  — Residual neural network + Monte Carlo Tree Search (AlphaZero-style approach). Applies the
  AlphaGo/AlphaZero methodology to the Rubik's cube.

- **[yakupbilen/drl-rubiks-cube](https://github.com/yakupbilen/drl-rubiks-cube)**
  — Deep RL + A* with PyQt5 visualization. Good for studying how to combine RL with visual
  debugging.

- **[NVIDIA Blog on DeepCubeA](https://developer.nvidia.com/blog/ai-solves-the-rubiks-cube-in-a-fraction-of-a-second/)**
  — Trained on 10 billion simulations using TITAN V GPUs. Provides practical details on the
  training infrastructure and results.

---

## 5. God's Number & Optimal Solving Research

- **[cube20.org](https://www.cube20.org/)**
  — The definitive proof that God's Number is 20 (HTM). Used 35 CPU-years donated by Google.
  Every position of the Rubik's Cube can be solved in twenty moves or less.

- **[Optimal Solutions — Wikipedia](https://en.wikipedia.org/wiki/Optimal_solutions_for_the_Rubik's_Cube)**
  — History of upper bound reductions from 52 down to 20 over decades of research.

- **[NxN God's Number (arXiv:2112.08602)](https://arxiv.org/pdf/2112.08602)**
  — Proves the NxN diameter is Θ(n²/log n). Directly relevant to cubesolve's big cube work —
  establishes the theoretical lower and upper bounds on how many moves are needed for NxN cubes.

- **[Demaine et al. — MIT](https://dspace.mit.edu/handle/1721.1/73771)**
  — Proves NxN solving is NP-hard in certain restricted cases. Important theoretical context for
  understanding the computational complexity of big cube solving.

---

## 6. Commutators & Big Cube Theory

cubesolve already uses commutators for center solving in the Cage method. These resources provide
deeper theory and practical construction techniques:

- **[Ryan Heise — Commutator Tutorial](https://www.ryanheise.com/cube/commutators.html)**
  — Practical construction of 3-cycles using commutators. A commutator is a sequence of the form
  X.Y.X⁻¹.Y⁻¹ which affects only the pieces "caught up" in the intersection of X and Y while
  leaving everything else untouched.

- **[Ruwix — Commutators & Conjugates](https://ruwix.com/the-rubiks-cube/commutators-conjugates/)**
  — Detailed guide on setup moves (conjugates A.B.A⁻¹), orientation swaps, and three-cycle
  construction. Covers how to use conjugates to position pieces for a known commutator.

- **[Ruwix — Big Cube NxN Solution](https://ruwix.com/twisty-puzzles/big-cubes-nxnxn-solution/)**
  — Full reduction walkthrough for 4x4 through 49x49. Key steps: Centers → Edges → 3x3 Stage.
  Once you know the reduction method for 4x4 and 5x5, you can technically solve any NxN puzzle.

- **[Commutators in the Rubik's Cube Group (Academic Paper)](https://www.tandfonline.com/doi/full/10.1080/00029890.2023.2263158)**
  — Formal mathematical treatment of commutator subgroups in the Rubik's Cube group. Proves that
  if supp(g) ∩ supp(h) consists of a single cubie, then [g, h] is a 3-cycle.

- **[Geometry and the Imagination — Commutators](https://lamington.wordpress.com/2013/08/24/you-can-solve-the-cube-with-commutators/)**
  — Surprisingly, commutators alone form a complete method for solving the Rubik's Cube: make a
  quarter turn if the position is odd, place pieces in their cubicles, and fix orientations.

### Key Concepts

**Commutator:** X.Y.X⁻¹.Y⁻¹
- If X and Y are completely disjoint → does nothing
- If X and Y overlap → affects only the overlapping pieces
- This is the fundamental principle behind constructing useful 3-cycles

**Conjugate (Setup Move):** A.B.A⁻¹
- A "setup" move positions pieces so a known algorithm B can act on them
- Perfect when you have a commutator for one layer but need to cycle pieces across layers

**Niklas Commutator:**
- Provides 8-move commutators that cycle 3 pieces of any type
- Particularly helpful for solving centers between two remaining faces in the reduction method

---

## 7. Parity (Even Cubes)

cubesolve already handles parity — these resources provide complete reference for all cases:

### What Is Parity?

Parity occurs on all even-layered cubes (4x4, 6x6, etc.) and **never** on odd-layered cubes
(3x3, 5x5, etc.). It happens because even cubes have no fixed centers — you build the centers
yourself, and if placed incorrectly, parity results. When forming edges, there is only a 50-50
chance of creating a cycle with the same parity as the corner permutation.

### OLL Parity (Orientation Parity)

Occurs when two adjacent edge pieces are flipped on the last layer. There is only one OLL parity
case.

**Most Common OLL Parity Algorithm:**
Hold the cube with the two flipped edges facing you:
`r2 B2 U2 l U2 r' U2 r U2 F2 r F2 l' B2 r2`

**Repeated-Sequence Algorithm** (easier to memorize, discovered Dec 2017 by Christopher Mowla):
`Rw' (F2 U' Lw' U)5 Rw`

### PLL Parity (Permutation Parity)

Occurs when two pairs of adjacent edge pieces are swapped diagonally. Generally not recognizable
until the PLL stage.

**PLL Parity Case 1 (Opposite Edge Swap):**
`r2 U2 r2 Uw2 r2 u2`

**PLL Parity Case 2 (Adjacent Edge Swap):**
`(R' U R U') r2 U2 r2 Uw2 r2 u2 (U R' U' R)`

There are 22 total PLL parity cases documented in the Speedsolving Wiki.

### Scaling to Larger Even Cubes

For 6x6 and larger: instead of turning outer 2 layers, turn outer 3 layers; instead of turning
1 inner layer slice, turn 2 inner layer slices. The same algorithms can be adapted.

### Parity References

- **[Ruwix — 4x4 Parity Cases](https://ruwix.com/twisty-puzzles/4x4x4-rubiks-cube-rubiks-revenge/parity/)**
  — OLL and PLL parity explained with visual diagrams.

- **[Speedsolving Wiki — 4x4 Parity Algorithms](https://www.speedsolving.com/wiki/index.php?title=4x4x4_parity_algorithms)**
  — Comprehensive list of all 22 PLL parity cases with algorithms.

- **[KewbzUK — 4x4 Parity Guide](https://kewbz.co.uk/blogs/solutions-guides/4x4-parity)**
  — Downloadable PDF cheat sheet for all parity cases.

- **[SpeedCube.us — OLL Parity](https://www.speedcube.us/blogs/speedcubing-solutions/4x4-oll-parity-algorithms)**
  — Multiple OLL parity algorithms ranked by execution speed.

- **[SpeedCube.us — PLL Parity](https://www.speedcube.us/blogs/speedcubing-solutions/4x4-pll-parity-algorithms)**
  — Multiple PLL parity algorithms with explanations.

- **[Kevin Gittemeier — Solving Parity](https://www.kevingittemeier.com/cube-parity/)**
  — Clear explanation of why parity happens (no fixed centers on even cubes).

- **[Tim Koop — Intuitive Parity Fix](https://timkoop.com/how-to-fix-a-dedge-parity-error-in-a-4-by-4-rubiks-cube-without-memorizing-a-big-algorithm)**
  — How to fix dedge parity without memorizing a long algorithm.

- **[Speedsolving Forum — Parity Avoidance](https://www.speedsolving.com/threads/intuitive-4x4-method-with-parity-avoidance.73049/)**
  — Discussion of methods that avoid parity entirely.

- **[Cubing Cheat Sheet — 4x4 Algorithms](https://cubingcheatsheet.com/algs4x.html)**
  — Quick reference card for reduction and parity algorithms.

---

## 8. Group Theory / Mathematics

- **[MIT — Mathematics of the Rubik's Cube (PDF)](https://web.mit.edu/sp.268/www/rubik.pdf)**
  — Permutation groups, commutators, macros. Establishes the formal mathematical framework for
  understanding cube operations as group elements.

- **[Harvard — Group Theory and the Rubik's Cube (PDF)](https://people.math.harvard.edu/~jjchen/docs/Group%20Theory%20and%20the%20Rubik's%20Cube.pdf)**
  — Proves solving methods are complete using group theory. Demonstrates that the commutator
  subgroup generates all even permutations needed to solve the cube.

- **[UC Berkeley — Mathematics of Rubik's Cube (PDF)](https://math.berkeley.edu/~hutching/rubik.pdf)**
  — Hands-on permutation group approach. Good for building intuition about why certain move
  sequences work.

- **[Tom Davis — Group Theory via Rubik's Cube (PDF)](http://www.geometer.org/rubik/group.pdf)**
  — Accessible intro to groups through the cube. Written for people who know how to solve the
  cube but want to understand the mathematics behind it.

- **[UChicago — Analyzing NxN Rubik's Cube Groups (PDF)](http://math.uchicago.edu/~may/REU2021/REUPapers/Chuang,Alex.pdf)**
  — Analysis of group structure for various sizes. Relevant to understanding how the group
  structure changes as cube size increases.

- **[Rubik's Cube Group — Wikipedia](https://en.wikipedia.org/wiki/Rubik's_Cube_group)**
  — The Rubik's Cube group has order 43,252,003,274,489,856,000 (approximately 4.3 × 10¹⁹).
  It is a non-abelian subgroup of S₄₈. Contains detailed information about the group structure,
  subgroups, and generators.

---

## 9. Algorithm Databases (CFOP Reference)

- **[SolveTheCube.com/algorithms](https://solvethecube.com/algorithms)**
  — Complete F2L, OLL (57 cases), PLL (21 cases). All algorithms with visual diagrams.

- **[SpeedCubeDB.com](https://speedcubedb.com/a/3x3/OLL)**
  — Searchable algorithm database. Allows filtering by algorithm set, category, and recognition
  patterns.

- **[CubeMaster.top](https://cubemaster.top/algorithms.html)**
  — Beginner to advanced algorithms. Progressive learning path from basic cross to full CFOP.

- **[Ruwix CFOP Guide](https://ruwix.com/the-rubiks-cube/advanced-cfop-fridrich/)**
  — Full Fridrich method walkthrough. Covers Cross, F2L, OLL, and PLL with visual guides for
  every case.

- **[CubeSkills F2L PDF](https://www.cubeskills.com/uploads/pdf/tutorials/f2l.pdf)**
  — By Feliks Zemdegs (world record holder). Professional-grade F2L tutorial covering all 41
  cases with intuitive explanations and finger tricks.

- **[Speedcubing.com — 4x4 Speedsolve](https://www.speedcubing.com/chris/4speedsolve3.html)**
  — Detailed walkthrough of the 3x3 stage after 4x4 reduction, including OLL and PLL with
  parity considerations.

---

## 10. Top Recommendations for This Project

Given that cubesolve already has Beginner, CFOP, Kociemba, LBL-Big, and Cage solvers with
6 rendering backends and NxN support:

| What to Study | Where | Why |
|---|---|---|
| Scalable NxN algorithms | [ShellPuppy/RCube](https://github.com/ShellPuppy/RCube) | Solves up to 65K layers in O(n²) — study for performance optimization |
| Lookup table approach | [dwalton76/rubiks-cube-NxNxN-solver](https://github.com/dwalton76/rubiks-cube-NxNxN-solver) | Different NxN architecture to compare with cubesolve's approach |
| Optimal solving internals | [hkociemba/RubiksCube-OptimalSolver](https://github.com/hkociemba/RubiksCube-OptimalSolver) | IDA* + pruning in Python — understand the search behind Kociemba |
| Web frontend sync | [irisxu02/rubik](https://github.com/irisxu02/rubik) | Three.js + Python backend, similar to cubesolve's web backend |
| AI/ML approach | [DeepCubeA](https://deepcube.igb.uci.edu/) | Entirely different paradigm — RL + search, published in Nature |
| NxN complexity theory | [arXiv:2112.08602](https://arxiv.org/pdf/2112.08602) | Mathematical bounds Θ(n²/log n) on the problem space |
| Algorithm benchmarking | [The-Semicolons/AnalysisofRubiksCubeSolvingAlgorithm](https://github.com/The-Semicolons/AnalysisofRubiksCubeSolvingAlgorithm) | Side-by-side comparison of Kociemba, Korf, Thistlethwaite, Rokicki |
| Cube model design | [pglass/cube](https://github.com/pglass/cube) | Clean `Piece` class design — compare with cubesolve's domain model |
| Formula manipulation | [adrianliaw/PyCuber](https://github.com/adrianliaw/PyCuber) | Reverse, mirror operations on algorithm strings |
| God's Number proof | [cube20.org](https://www.cube20.org/) | Every 3x3 position solvable in ≤20 moves — the ultimate benchmark |

---

## Summary of Cubesolve's Current Architecture

For context, cubesolve currently features:

- **5 Solving Methods:** Beginner LBL, CFOP (Fridrich), Kociemba Two-Phase, LBL-Big (NxN), Cage (NxN)
- **NxN Support:** 3x3 through 8x8+ (size-agnostic cube model)
- **6 Rendering Backends:** Pyglet 1.5, Pyglet 2.0 (modern OpenGL), Tkinter, Console, Headless, Web (WebSocket)
- **Reduction Mechanism:** BeginnerReducer (NxN → 3x3) with configurable parity algorithms
- **Parity Handling:** Basic M-slice (for LBL) and Advanced R/L-slice (for CFOP)
- **Commutator Algorithms:** For center and edge solving in the Cage method
- **Animation System:** Smooth cube rotations with configurable speed and single-step debug mode
- **~13,000+ lines** of well-organized Python with clean layered architecture
