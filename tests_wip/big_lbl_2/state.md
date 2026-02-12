# On this branch - redo

L1 Edges aggressive test passed
L1 Aggressive Passed
L2 Aggressive Passed, still dead code below 1000 random see fix in this commit
Full solver  Aggressive 1000 Passed , still dead code below 1000 random see fix in this commit

Full solver 10000 fails
    reproducible in tests
    reproducible in GUI F.txt
    cube_size = 6, scramble_name = 'rnd_413547559', scramble_seed = 413547559

Need to work on dead code below

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