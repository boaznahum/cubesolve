

# The bug below solved m 1080 full solver tests passed
# On this branch - redo

L1 Edges aggressive test passed
L1 Aggressive Passed
L2 Aggressive Passed, still dead code below 1000 random see fix in this commit
Full solver  Aggressive 1000 Passed , still dead code below 1000 random see fix in this commit
Full solver 10000 fails, rare case 1/5000 tests

6. Solve rare case, more than 8000(still running)  tests passed (random = 3000)

## 7 No dead code in cube.domain.solver.direct.lbl._LBLSlices._LBLSlices._find_best_pre_alignment

Now repoducable with GUI seed 1 size 12

AssertionError: op name: after _try_solve_block[Block(start=Point(row=3, col=7), end=Point(row=3, col=7))]size:1 @ row=3, found previous not solved 2


        with self._parent.with_sanity_check_previous_are_solved(l1_tracker, row_index, f"_try_solve_block[{block}]"):
            with self._preserve_trackers():
                self._comm_helper.execute_commutator(
                    source_face=source_face,
                    target_face=target_face,
                    target_block=block,
                    source_block=valid_source,
                    preserve_state=True,
                    dry_run=False,
                    _cached_secret=dry_result
                )

Comment out this code, 2000 full solver tests passed
    # TODO: Debug the mapping and re-enable optimization:
    # if t_colors[i] == second_piece.color:
    #     continue  # Same color - safe, no actual change




Running L2 tests Random=1000 , 2 of 5073 fail
cube_size = 8, scramble_name = 'rnd_1781991940', scramble_seed = 1781991940
cube_size = 10, scramble_name = 'rnd_1037976487', scramble_seed = 1037976487

Not reproducible , second run 5 tests fail

## #current state

Bug solved, the failure

see in cube.domain.solver.direct.lbl._LBLSlices._LBLSlices._find_row_best_pre_alignment
```python
        if False:
            return 0

```

All failures are of type:

```terminaloutput
E                           AssertionError: After solving 9, found previous not solved 5

..\src\cube\domain\solver\direct\lbl\_LBLSlices.py:476: AssertionError

```

### Big LBL L2 a progress Yesterday 16:10 808aab72 ‼️partial

But make it dead cube.domain.solver.direct.lbl._LBLSlices._LBLSlices._find_best_pre_alignment

        #boaz: patch
        if True:
            return 0

### Even cube L2: fix tracker divergence with detection + restart Yesterday 21:23 ee3fa104
take nothing seems to me bullishit, some thing else solve, lets try do l1 l2 separately
# current state new bug

take for example a cube 12x12
e slice lower part of slices, so now sole, it will perfrom slice optimaztion and slice the upper in same direction
the problem i thin that:
FacesHolder satrta it find the face according tot the new majority and it is whee the lawer slices moved
also the edges athink that this is the face color because of the even/2 middle slice

The exact reproducing
Slice E[1:4, 7:8]  this is enough to fool the majority algorithm
Solve

when we try to solve l1 doesnt try to roate itslef to new location ? why

DEBUG: Big-LBL:_LBLSlices: ── end: Solving face row 9 ──
Traceback (most recent call last):
  File "D:\dev\code\python\cubesolve\src\cube\presentation\gui\backends\pyglet2\PygletAppWindow.py", line 650, in inject_command
    result = command.execute(ctx)
  File "D:\dev\code\python\cubesolve\src\cube\presentation\gui\commands\concrete.py", line 136, in execute
    ctx.slv.solve(animation=None)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "D:\dev\code\python\cubesolve\src\cube\domain\solver\common\AbstractSolver.py", line 90, in solve
    result = self._solve_impl(what)
  File "D:\dev\code\python\cubesolve\src\cube\domain\solver\direct\lbl\LayerByLayerNxNSolver.py", line 306, in _solve_impl
    return self._solve_impl2(what)
           ~~~~~~~~~~~~~~~~~^^^^^^
  File "D:\dev\code\python\cubesolve\src\cube\domain\solver\direct\lbl\LayerByLayerNxNSolver.py", line 411, in _solve_impl2
    self._solve_l2_slices(th)
    ~~~~~~~~~~~~~~~~~~~~~^^^^
  File "D:\dev\code\python\cubesolve\src\cube\domain\solver\direct\lbl\LayerByLayerNxNSolver.py", line 782, in _solve_l2_slices
    assert self._is_l2_slices_solved(
           ~~~~~~~~~~~~~~~~~~~~~~~~~^
        face_trackers), f"L2 not solve={self._is_l2_slices_not_solved_reason(face_trackers)}"
        ^^^^^^^^^^^^^^
AssertionError: L2 not solve=L1 edges are not on place



### Handle even cube parity exceptions in BigLBL solver Yesterday 21:49 be108435
took all but not the test
handed even and corner swap parity

# Tie in colors
we sort according to color, still fail

# in ahead commits
All L1 tests fail
tests_wip/big_lbl_2/test_lbl_big_cube_full_solver.py

fails:
    cube_size = 6, scramble_name = 'rnd_137658025', scramble_seed = 137658025
    cube_size = 4, scramble_name = 'rnd_1794630359', scramble_seed = 1794630359
    cube_size = 6, scramble_name = 'rnd_1838264046', scramble_seed = 1838264046

reproduced when we hardcoded the seeds

L1 solver: passed
L2: Solver: fails
