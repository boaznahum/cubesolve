# On this branch - redo

L1 Edges aggressive test passed
L1 Aggressive Passed
‼️‼️‼️ Any change in code change this list ‼️‼️‼️
L2 from aggressive 6 fails, among them reproduced in gui (F):  
    cube_size = 4, scramble_name = 'rnd_1539464596', scramble_seed = 1539464596
    cube_size = 6, scramble_name = 'rnd_793592993', scramble_seed = 793592993

ile "D:\dev\code\python\cubesolve3\src\cube\domain\solver\direct\lbl\_LBLNxNEdges.py", line 268, in _solve_edge_win_one_source
    status = self._solve_edge_wing_by_source(target_face, target_edge_wing, st)
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\direct\lbl\_LBLNxNEdges.py", line 301, in _solve_edge_wing_by_source
    assert target_face.color == target_face_color
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# What i took from claude branch tha almost all passes ? 
##  0885fbfac55d03615daccab0406c93c61ac495aa

### Big LBL L2 a progress Yesterday 16:10 808aab72 ‼️partial

But make it dead cube.domain.solver.direct.lbl._LBLSlices._LBLSlices._find_best_pre_alignment

        #boaz: patch
        if True:
            return 0

### Even cube L2: fix tracker divergence with detection + restart Yesterday 21:23 ee3fa104
take nothing seems to me bullishit, some thing else solve, lets try do l1 l2 separately


### Handle even cube parity exceptions in BigLBL solver Yesterday 21:49 be108435
took all but not the test
handed even and corner swap parity

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