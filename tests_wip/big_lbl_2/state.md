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