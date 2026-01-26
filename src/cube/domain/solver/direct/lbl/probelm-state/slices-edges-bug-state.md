# The bug

1. Patch in cube.domain.solver.direct.lbl._common._get_side_face_trackers
2. Patch is enabled in: src/cube/domain/solver/direct/lbl/_lbl_config.py:14
2. test big_lbl.test_lbl_big_cube_solver.TestLBLBigCubeSolver.test_lbl_slices_ctr_5x5
3. Fails on 5,5 scramble 7, 89, 7: AssertionError: Wing FR[0][ORANGE, GREEN]⬅️[GREEN, ORANGE] is not solved
2. Reset
3. Scramble 7
4. solve instanct or L1 then centers

**Thanks** to the patch, it is reprodcable even we do it in two steps, becuase the faces are sorted

