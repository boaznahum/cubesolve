# Solver TODOs

## CFOP parity detection (TODO)

CFOP doesn't detect and raise parity exceptions like BeginnerSolver3x3 does:
- **Edge parity (OLL):** CFOP silently fixes it in `OLL._check_and_do_oll_edge_parity()`
  instead of raising `EvenCubeEdgeParityException`
- **Corner parity (PLL):** Similar issue - CFOP fixes instead of raising
  `EvenCubeCornerSwapException`

For now, the orchestrator uses BeginnerSolver3x3 as the parity detector.
To use CFOP as parity detector, it needs to be modified to raise exceptions
instead of silently fixing parity.

See: `OLL.py` lines 108-126 (`_check_and_do_oll_edge_parity`)

---

find dead code in solvers

the parity logic in NxNSolverOrchestrator i svery messy, a lot of questions, why parity is not fixed by the detector like corner
and we dont need to tell it not to it
why  if parity_detector is not None:
                            self.debug(f"Falling back to CFOP for remaining parity")
                            parity_detector.solve_3x3(debug, what)
                            break

why we need bith solve and  solve_3x3 ??
same as for status_3x3


